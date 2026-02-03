"""Test UK Fuel Finder coordinator."""
from unittest.mock import MagicMock, patch
from datetime import timedelta

import pytest
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import UpdateFailed

from custom_components.ukfuelfinder.coordinator import UKFuelFinderCoordinator


@pytest.fixture
def mock_station_data():
    """Mock station data."""
    station_info = MagicMock()
    station_info.pfs_id = "12345"
    station_info.trading_name = "Test Station"
    station_info.address = "123 Test St"
    station_info.brand = "TestBrand"
    station_info.latitude = 51.5074
    station_info.longitude = -0.1278
    station_info.phone = "01234567890"
    
    price_info = MagicMock()
    price_info.pfs_id = "12345"
    price_info.fuel_type = "Unleaded"
    price_info.price = 145.9
    
    return [(2.5, station_info)], [price_info]


async def test_coordinator_update_success(hass, mock_station_data):
    """Test successful coordinator update."""
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
    
    with patch("custom_components.ukfuelfinder.coordinator.FuelFinderClient") as mock_client:
        mock_instance = mock_client.return_value
        mock_instance.search_by_location.return_value = nearby_stations
        mock_instance.get_all_pfs_prices.return_value = prices
        
        coordinator = UKFuelFinderCoordinator(hass, entry_data)
        await coordinator.async_config_entry_first_refresh()
        
        assert coordinator.data is not None
        assert "stations" in coordinator.data
        assert "12345" in coordinator.data["stations"]
        assert coordinator.data["stations"]["12345"]["distance"] == 2.5
        assert "unleaded" in coordinator.data["stations"]["12345"]["prices"]


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
    
    with patch("custom_components.ukfuelfinder.coordinator.FuelFinderClient") as mock_client:
        mock_instance = mock_client.return_value
        mock_instance.search_by_location.side_effect = Exception("Authentication failed")
        
        coordinator = UKFuelFinderCoordinator(hass, entry_data)
        
        with pytest.raises(ConfigEntryAuthFailed):
            await coordinator.async_config_entry_first_refresh()


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
    
    with patch("custom_components.ukfuelfinder.coordinator.FuelFinderClient") as mock_client:
        mock_instance = mock_client.return_value
        mock_instance.search_by_location.side_effect = Exception("Network error")
        
        coordinator = UKFuelFinderCoordinator(hass, entry_data)
        
        with pytest.raises(UpdateFailed):
            await coordinator.async_config_entry_first_refresh()
