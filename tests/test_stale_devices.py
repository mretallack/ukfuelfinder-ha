"""Test stale device removal with grace period."""

from unittest.mock import MagicMock, patch

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.ukfuelfinder.const import DOMAIN


@pytest.fixture
def mock_client():
    """Mock FuelFinderClient."""
    with patch("ukfuelfinder.FuelFinderClient") as mock:
        client = MagicMock()
        mock.return_value = client
        yield client


async def test_stale_device_removal_grace_period(hass, mock_client):
    """Test that devices are removed after 2 update cycles (grace period)."""
    from custom_components.ukfuelfinder.coordinator import UKFuelFinderCoordinator

    # Create mock station data using MagicMock
    def create_mock_station(station_id, name):
        location = MagicMock()
        location.address_line_1 = "123 Test St"
        location.city = "Test City"
        location.postcode = "TE1 1ST"
        location.latitude = 51.5074
        location.longitude = -0.1278

        station_info = MagicMock()
        station_info.node_id = station_id
        station_info.trading_name = name
        station_info.brand_name = "TestBrand"
        station_info.location = location
        station_info.public_phone_number = "01234567890"

        fuel_price = MagicMock()
        fuel_price.fuel_type = "Unleaded"
        fuel_price.price = 145.9

        pfs = MagicMock()
        pfs.node_id = station_id
        pfs.fuel_prices = [fuel_price]

        return station_info, pfs

    station1_info, station1_pfs = create_mock_station("12345", "Station 1")
    station2_info, station2_pfs = create_mock_station("67890", "Station 2")

    # Initial data: both stations present
    mock_client.search_by_location.return_value = [
        (2.5, station1_info),
        (3.5, station2_info),
    ]
    mock_client.get_all_pfs_prices.return_value = [station1_pfs, station2_pfs]

    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            "client_id": "test_id",
            "client_secret": "test_secret",
            "environment": "test",
            "latitude": 51.5074,
            "longitude": -0.1278,
            "radius": 5.0,
            "update_interval": 30,
        },
    )
    entry.add_to_hass(hass)

    coordinator = UKFuelFinderCoordinator(hass, entry.data)
    coordinator.config_entry = entry

    # First update - both stations present
    await coordinator.async_refresh()
    assert "12345" in coordinator.data["stations"]
    assert "67890" in coordinator.data["stations"]
    assert len(coordinator.missing_stations) == 0

    # Create mock devices in registry
    from homeassistant.helpers import device_registry as dr

    device_registry = dr.async_get(hass)
    device1 = device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, "12345")},
        name="Station 1",
    )
    device2 = device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, "67890")},
        name="Station 2",
    )

    # Second update - station 2 disappears (first missing cycle)
    mock_client.search_by_location.return_value = [(2.5, station1_info)]
    mock_client.get_all_pfs_prices.return_value = [station1_pfs]

    await coordinator.async_refresh()
    assert "12345" in coordinator.data["stations"]
    assert "67890" not in coordinator.data["stations"]
    assert coordinator.missing_stations["67890"] == 1

    # Device should still exist (grace period)
    device = device_registry.async_get_device(identifiers={(DOMAIN, "67890")})
    assert device is not None
    assert entry.entry_id in device.config_entries

    # Third update - station 2 still missing (second missing cycle, triggers removal)
    await coordinator.async_refresh()
    assert coordinator.missing_stations.get("67890", 2) == 2  # Should be at count 2

    # Fourth update - triggers removal after grace period
    await coordinator.async_refresh()
    assert coordinator.missing_stations.get("67890") is None  # Removed from tracking

    # Device should now be removed
    device = device_registry.async_get_device(identifiers={(DOMAIN, "67890")})
    assert device is None or entry.entry_id not in device.config_entries

    # Station 1 should still be present
    device = device_registry.async_get_device(identifiers={(DOMAIN, "12345")})
    assert device is not None
    assert entry.entry_id in device.config_entries


async def test_station_reappears_during_grace_period(hass, mock_client):
    """Test that station reappearing during grace period resets the counter."""
    from custom_components.ukfuelfinder.coordinator import UKFuelFinderCoordinator

    def create_mock_station(station_id, name):
        location = MagicMock()
        location.address_line_1 = "123 Test St"
        location.city = "Test City"
        location.postcode = "TE1 1ST"
        location.latitude = 51.5074
        location.longitude = -0.1278

        station_info = MagicMock()
        station_info.node_id = station_id
        station_info.trading_name = name
        station_info.brand_name = "TestBrand"
        station_info.location = location
        station_info.public_phone_number = "01234567890"

        fuel_price = MagicMock()
        fuel_price.fuel_type = "Unleaded"
        fuel_price.price = 145.9

        pfs = MagicMock()
        pfs.node_id = station_id
        pfs.fuel_prices = [fuel_price]

        return station_info, pfs

    station1_info, station1_pfs = create_mock_station("12345", "Station 1")

    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            "client_id": "test_id",
            "client_secret": "test_secret",
            "environment": "test",
            "latitude": 51.5074,
            "longitude": -0.1278,
            "radius": 5.0,
            "update_interval": 30,
        },
    )
    entry.add_to_hass(hass)

    coordinator = UKFuelFinderCoordinator(hass, entry.data)
    coordinator.config_entry = entry

    # First update - station present
    mock_client.search_by_location.return_value = [(2.5, station1_info)]
    mock_client.get_all_pfs_prices.return_value = [station1_pfs]
    await coordinator.async_refresh()

    # Second update - station disappears
    mock_client.search_by_location.return_value = []
    mock_client.get_all_pfs_prices.return_value = []
    await coordinator.async_refresh()
    assert coordinator.missing_stations["12345"] == 1

    # Third update - station reappears (should reset counter)
    mock_client.search_by_location.return_value = [(2.5, station1_info)]
    mock_client.get_all_pfs_prices.return_value = [station1_pfs]
    await coordinator.async_refresh()
    assert "12345" not in coordinator.missing_stations  # Counter reset
    assert "12345" in coordinator.data["stations"]
