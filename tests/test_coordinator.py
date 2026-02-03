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
        assert data["stations"]["12345"]["distance"] == 2.5
        assert "unleaded" in data["stations"]["12345"]["prices"]


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
