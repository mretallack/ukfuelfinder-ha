"""End-to-end tests for dynamic location tracking."""

import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.const import (
    ATTR_LATITUDE,
    ATTR_LONGITUDE,
    STATE_HOME,
    STATE_NOT_HOME,
    STATE_UNAVAILABLE,
)

from custom_components.ukfuelfinder.const import (
    CONF_LOCATION_SOURCE,
    LOCATION_SOURCE_STATIC,
)
from custom_components.ukfuelfinder.coordinator import UKFuelFinderCoordinator
from custom_components.ukfuelfinder.location import DEBOUNCE_SECONDS


@pytest.fixture
def entry_data_dynamic():
    """Config entry data with dynamic location source."""
    return {
        "client_id": "test_id",
        "client_secret": "test_secret",
        "environment": "test",
        "latitude": 51.5074,
        "longitude": -0.1278,
        "radius": 5.0,
        "update_interval": 30,
        "location_source": "person.mark",
    }


@pytest.fixture
def mock_nearby_home():
    """Mock stations near home location."""
    location = MagicMock()
    location.latitude = 51.51
    location.longitude = -0.13
    location.address_line_1 = "Home Station"
    location.city = "London"
    location.postcode = "SW1A"

    station = MagicMock()
    station.node_id = "home_station"
    station.trading_name = "Home Station"
    station.brand_name = "HomeBrand"
    station.public_phone_number = "111"
    station.location = location
    station.is_supermarket_service_station = False
    station.is_motorway_service_station = False
    station.amenities = []
    station.opening_times = {}
    station.fuel_types = ["e10"]
    station.mft_organisation_name = "Org"
    station.temporary_closure = False
    station.permanent_closure = False

    fuel_price = MagicMock()
    fuel_price.fuel_type = "E10"
    fuel_price.price = 145.9
    fuel_price.price_last_updated = None

    pfs = MagicMock()
    pfs.node_id = "home_station"
    pfs.fuel_prices = [fuel_price]

    return [(1.0, station)], [pfs]


@pytest.fixture
def mock_nearby_work():
    """Mock stations near work location."""
    location = MagicMock()
    location.latitude = 52.51
    location.longitude = -1.93
    location.address_line_1 = "Work Station"
    location.city = "Birmingham"
    location.postcode = "B1"

    station = MagicMock()
    station.node_id = "work_station"
    station.trading_name = "Work Station"
    station.brand_name = "WorkBrand"
    station.public_phone_number = "222"
    station.location = location
    station.is_supermarket_service_station = True
    station.is_motorway_service_station = False
    station.amenities = []
    station.opening_times = {}
    station.fuel_types = ["e10"]
    station.mft_organisation_name = "Org2"
    station.temporary_closure = False
    station.permanent_closure = False

    fuel_price = MagicMock()
    fuel_price.fuel_type = "E10"
    fuel_price.price = 140.9
    fuel_price.price_last_updated = None

    pfs = MagicMock()
    pfs.node_id = "work_station"
    pfs.fuel_prices = [fuel_price]

    return [(0.5, station)], [pfs]


async def test_person_moves_stations_update(
    hass, entry_data_dynamic, mock_nearby_home, mock_nearby_work
):
    """Test: person moves → coordinator refreshes → station list changes."""
    # Set up person at home
    hass.states.async_set(
        "person.mark",
        STATE_HOME,
        {ATTR_LATITUDE: 51.5074, ATTR_LONGITUDE: -0.1278},
    )

    home_stations, home_prices = mock_nearby_home
    work_stations, work_prices = mock_nearby_work

    with patch("ukfuelfinder.FuelFinderClient") as mock_client:
        mock_instance = mock_client.return_value
        mock_instance.search_by_location = MagicMock(return_value=home_stations)
        mock_instance.get_all_pfs_prices = MagicMock(return_value=home_prices)

        coordinator = UKFuelFinderCoordinator(hass, entry_data_dynamic)
        coordinator.setup_location_manager(
            location_source="person.mark",
            fallback_lat=51.5074,
            fallback_lon=-0.1278,
        )

        # First update — should use home location
        data = await coordinator._async_update_data()
        assert "home_station" in data["stations"]

        # Person moves to work
        hass.states.async_set(
            "person.mark",
            STATE_NOT_HOME,
            {ATTR_LATITUDE: 52.5, ATTR_LONGITUDE: -1.9},
        )

        # Update mock to return work stations
        mock_instance.search_by_location = MagicMock(return_value=work_stations)
        mock_instance.get_all_pfs_prices = MagicMock(return_value=work_prices)

        # Refresh with new location
        data = await coordinator._async_update_data()
        assert "work_station" in data["stations"]

        # Verify the search was called with new coords
        mock_instance.search_by_location.assert_called_with(52.5, -1.9, 5.0)


async def test_person_unavailable_falls_back(hass, entry_data_dynamic, mock_nearby_home):
    """Test: person goes unavailable → fallback to HA home coordinates."""
    # Set up person as unavailable
    hass.states.async_set(
        "person.mark",
        STATE_UNAVAILABLE,
        {},
    )

    home_stations, home_prices = mock_nearby_home

    with patch("ukfuelfinder.FuelFinderClient") as mock_client:
        mock_instance = mock_client.return_value
        mock_instance.search_by_location = MagicMock(return_value=home_stations)
        mock_instance.get_all_pfs_prices = MagicMock(return_value=home_prices)

        coordinator = UKFuelFinderCoordinator(hass, entry_data_dynamic)
        coordinator.setup_location_manager(
            location_source="person.mark",
            fallback_lat=51.5074,
            fallback_lon=-0.1278,
        )

        # Should use fallback coords
        data = await coordinator._async_update_data()

        mock_instance.search_by_location.assert_called_with(51.5074, -0.1278, 5.0)
        assert "home_station" in data["stations"]


async def test_debounce_limits_refreshes(hass, entry_data_dynamic):
    """Test: rapid location changes → debounce limits refresh calls."""
    hass.states.async_set(
        "person.mark",
        STATE_HOME,
        {ATTR_LATITUDE: 51.5, ATTR_LONGITUDE: -0.1},
    )

    with patch("ukfuelfinder.FuelFinderClient"):
        coordinator = UKFuelFinderCoordinator(hass, entry_data_dynamic)
        coordinator.setup_location_manager(
            location_source="person.mark",
            fallback_lat=51.5074,
            fallback_lon=-0.1278,
        )

        # Mock async_request_refresh to track calls
        coordinator.async_request_refresh = AsyncMock()

        # Start location manager
        await coordinator.location_manager.async_start()

        # Simulate rapid location changes
        for i in range(5):
            hass.states.async_set(
                "person.mark",
                STATE_NOT_HOME,
                {ATTR_LATITUDE: 51.5 + (i * 0.01), ATTR_LONGITUDE: -0.1},
            )
            await hass.async_block_till_done()

        # Should have only triggered one immediate refresh (first change)
        # Subsequent ones are debounced
        assert coordinator.async_request_refresh.call_count == 1

        # Clean up
        await coordinator.location_manager.async_stop()


async def test_setup_and_unload_dynamic(hass, entry_data_dynamic, mock_nearby_home):
    """Test: setup with dynamic source, unload, verify no dangling listeners."""
    hass.states.async_set(
        "person.mark",
        STATE_HOME,
        {ATTR_LATITUDE: 51.5074, ATTR_LONGITUDE: -0.1278},
    )

    home_stations, home_prices = mock_nearby_home

    with patch("ukfuelfinder.FuelFinderClient") as mock_client:
        mock_instance = mock_client.return_value
        mock_instance.search_by_location = MagicMock(return_value=home_stations)
        mock_instance.get_all_pfs_prices = MagicMock(return_value=home_prices)

        coordinator = UKFuelFinderCoordinator(hass, entry_data_dynamic)
        coordinator.setup_location_manager(
            location_source="person.mark",
            fallback_lat=51.5074,
            fallback_lon=-0.1278,
        )

        await coordinator.location_manager.async_start()
        assert coordinator.location_manager._unsub_state_change is not None

        # Unload
        await coordinator.location_manager.async_stop()
        assert coordinator.location_manager._unsub_state_change is None
