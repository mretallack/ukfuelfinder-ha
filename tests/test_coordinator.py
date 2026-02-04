"""Test UK Fuel Finder coordinator."""

from datetime import timedelta
from unittest.mock import MagicMock, patch

import pytest
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import UpdateFailed
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.ukfuelfinder.const import DOMAIN
from custom_components.ukfuelfinder.coordinator import UKFuelFinderCoordinator


@pytest.fixture
def mock_station_data():
    """Mock station data with correct API structure."""
    # Create location mock
    location = MagicMock()
    location.latitude = 51.5074
    location.longitude = -0.1278
    location.address_line_1 = "123 Test St"
    location.city = "London"
    location.postcode = "SW1A 1AA"

    # Create station info mock
    station_info = MagicMock()
    station_info.node_id = "12345"  # Changed from pfs_id
    station_info.trading_name = "Test Station"
    station_info.brand_name = "TestBrand"  # Changed from brand
    station_info.public_phone_number = "01234567890"  # Changed from phone
    station_info.location = location  # Added location object

    # Create fuel price mock
    fuel_price = MagicMock()
    fuel_price.fuel_type = "Unleaded"
    fuel_price.price = 145.9

    # Create PFS mock (what get_all_pfs_prices returns)
    pfs = MagicMock()
    pfs.node_id = "12345"  # Changed from pfs_id
    pfs.fuel_prices = [fuel_price]  # List of fuel prices

    return [(2.5, station_info)], [pfs]


async def test_coordinator_update_success(hass, mock_station_data):
    """Test successful coordinator update with all fields."""
    nearby_stations, prices = mock_station_data

    entry_data = {
        "client_id": "test_id",
        "client_secret": "test_secret",
        "environment": "test",
        "latitude": 51.5074,
        "longitude": -0.1278,
        "radius": 5.0,
        "update_interval": 30,
    }

    with patch("ukfuelfinder.FuelFinderClient") as mock_client:
        mock_instance = mock_client.return_value
        mock_instance.search_by_location = lambda *args, **kwargs: nearby_stations
        mock_instance.get_all_pfs_prices = lambda: prices

        coordinator = UKFuelFinderCoordinator(hass, entry_data)

        # Call the internal update method directly
        data = await coordinator._async_update_data()

        assert data is not None
        assert "stations" in data
        assert "12345" in data["stations"]
        
        station = data["stations"]["12345"]
        
        # Check all station fields
        assert station["distance"] == 2.5
        assert station["info"]["id"] == "12345"
        assert station["info"]["trading_name"] == "Test Station"
        assert station["info"]["brand"] == "TestBrand"
        assert station["info"]["address"] == "123 Test St, London, SW1A 1AA"
        assert station["info"]["latitude"] == 51.5074
        assert station["info"]["longitude"] == -0.1278
        assert station["info"]["phone"] == "01234567890"
        
        # Check prices
        assert "unleaded" in station["prices"]
        assert station["prices"]["unleaded"] == 145.9


async def test_coordinator_auth_failure(hass):
    """Test coordinator handles auth failure."""
    entry_data = {
        "client_id": "test_id",
        "client_secret": "test_secret",
        "environment": "test",
        "latitude": 51.5074,
        "longitude": -0.1278,
        "radius": 5.0,
        "update_interval": 30,
    }

    with patch("ukfuelfinder.FuelFinderClient") as mock_client:
        mock_instance = mock_client.return_value

        def raise_auth_error(*args, **kwargs):
            raise Exception("Authentication failed")

        mock_instance.search_by_location = raise_auth_error

        coordinator = UKFuelFinderCoordinator(hass, entry_data)

        with pytest.raises(ConfigEntryAuthFailed):
            await coordinator._async_update_data()


async def test_coordinator_network_error(hass):
    """Test coordinator handles network errors."""
    entry_data = {
        "client_id": "test_id",
        "client_secret": "test_secret",
        "environment": "test",
        "latitude": 51.5074,
        "longitude": -0.1278,
        "radius": 5.0,
        "update_interval": 30,
    }

    with patch("ukfuelfinder.FuelFinderClient") as mock_client:
        mock_instance = mock_client.return_value

        def raise_network_error(*args, **kwargs):
            raise Exception("Network error")

        mock_instance.search_by_location = raise_network_error

        coordinator = UKFuelFinderCoordinator(hass, entry_data)

        with pytest.raises(UpdateFailed):
            await coordinator._async_update_data()
