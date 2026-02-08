"""Test coordinator metadata and cheapest calculation."""

from unittest.mock import MagicMock, patch

import pytest

from custom_components.ukfuelfinder.const import DOMAIN


async def test_coordinator_get_cheapest_fuel(hass):
    """Test coordinator get_cheapest_fuel method."""
    from custom_components.ukfuelfinder.coordinator import UKFuelFinderCoordinator

    entry_data = {
        "client_id": "test_id",
        "client_secret": "test_secret",
        "environment": "test",
        "latitude": 51.5074,
        "longitude": -0.1278,
        "radius": 5.0,
        "update_interval": 30,
    }

    with patch("ukfuelfinder.FuelFinderClient"):
        coordinator = UKFuelFinderCoordinator(hass, entry_data)

    coordinator.data = {
        "stations": {
            "station1": {
                "info": {
                    "id": "station1",
                    "trading_name": "Station 1",
                    "brand": "Brand1",
                },
                "distance": 2.5,
                "prices": {
                    "e10": 145.9,
                    "b7": 155.9,
                },
            },
            "station2": {
                "info": {
                    "id": "station2",
                    "trading_name": "Station 2",
                    "brand": "Brand2",
                },
                "distance": 3.5,
                "prices": {
                    "e10": 140.9,  # Cheaper
                    "b7": 160.9,
                },
            },
        }
    }

    # Test finding cheapest e10
    cheapest = coordinator.get_cheapest_fuel("e10")
    assert cheapest is not None
    assert cheapest["station_id"] == "station2"
    assert cheapest["price"] == 140.9
    assert cheapest["trading_name"] == "Station 2"

    # Test finding cheapest b7
    cheapest = coordinator.get_cheapest_fuel("b7")
    assert cheapest is not None
    assert cheapest["station_id"] == "station1"
    assert cheapest["price"] == 155.9

    # Test fuel type not available
    cheapest = coordinator.get_cheapest_fuel("e5")
    assert cheapest is None


async def test_coordinator_get_cheapest_fuel_no_data(hass):
    """Test get_cheapest_fuel with no data."""
    from custom_components.ukfuelfinder.coordinator import UKFuelFinderCoordinator

    entry_data = {
        "client_id": "test_id",
        "client_secret": "test_secret",
        "environment": "test",
        "latitude": 51.5074,
        "longitude": -0.1278,
        "radius": 5.0,
        "update_interval": 30,
    }

    with patch("ukfuelfinder.FuelFinderClient"):
        coordinator = UKFuelFinderCoordinator(hass, entry_data)

    coordinator.data = None

    cheapest = coordinator.get_cheapest_fuel("e10")
    assert cheapest is None


async def test_coordinator_metadata_fields(hass):
    """Test coordinator includes metadata fields in station data."""
    from ukfuelfinder.models import PFS, FuelPrice, Location, PFSInfo

    from custom_components.ukfuelfinder.coordinator import UKFuelFinderCoordinator

    entry_data = {
        "client_id": "test_id",
        "client_secret": "test_secret",
        "environment": "test",
        "latitude": 51.5074,
        "longitude": -0.1278,
        "radius": 5.0,
        "update_interval": 30,
    }

    # Create mock station with metadata
    mock_location = Location(
        latitude=51.5074,
        longitude=-0.1278,
        address_line_1="123 Test St",
        city="London",
        postcode="SW1A 1AA",
    )

    mock_station = PFSInfo(
        node_id="test123",
        mft_organisation_name="Test Org Ltd",
        trading_name="Test Station",
        public_phone_number="01234567890",
        brand_name="TestBrand",
        location=mock_location,
        is_supermarket_service_station=True,
        is_motorway_service_station=False,
        amenities=["customer_toilets", "car_wash"],
        opening_times={"monday": {"open": "06:00", "close": "22:00"}},
        fuel_types=["E10", "B7"],
        temporary_closure=False,
        permanent_closure=None,
    )

    mock_pfs = PFS(
        node_id="test123",
        mft_organisation_name="Test Org Ltd",
        trading_name="Test Station",
        public_phone_number="01234567890",
        fuel_prices=[
            FuelPrice(fuel_type="E10", price=145.9),
        ],
    )

    with patch("ukfuelfinder.FuelFinderClient") as mock_client:
        mock_client.return_value.search_by_location.return_value = [(2.5, mock_station)]
        mock_client.return_value.get_all_pfs_prices.return_value = [mock_pfs]

        coordinator = UKFuelFinderCoordinator(hass, entry_data)
        data = await coordinator._async_update_data()

    # Verify metadata fields are present
    station = data["stations"]["test123"]
    info = station["info"]

    assert info["is_supermarket"] is True
    assert info["is_motorway"] is False
    assert info["amenities"] == ["customer_toilets", "car_wash"]
    assert info["opening_times"] == {"monday": {"open": "06:00", "close": "22:00"}}
    assert info["fuel_types_available"] == ["E10", "B7"]
    assert info["organization_name"] == "Test Org Ltd"
    assert info["temporary_closure"] is False
    assert info["permanent_closure"] is None


async def test_coordinator_handles_missing_metadata(hass):
    """Test coordinator handles missing/None metadata gracefully."""
    from ukfuelfinder.models import PFS, Location, PFSInfo

    from custom_components.ukfuelfinder.coordinator import UKFuelFinderCoordinator

    entry_data = {
        "client_id": "test_id",
        "client_secret": "test_secret",
        "environment": "test",
        "latitude": 51.5074,
        "longitude": -0.1278,
        "radius": 5.0,
        "update_interval": 30,
    }

    # Create station with minimal data (no metadata)
    mock_location = Location(
        latitude=51.5074,
        longitude=-0.1278,
    )

    mock_station = PFSInfo(
        node_id="test123",
        mft_organisation_name="Test Org",
        trading_name="Test Station",
        public_phone_number=None,
        location=mock_location,
        # All metadata fields None
        is_supermarket_service_station=None,
        is_motorway_service_station=None,
        amenities=None,
        opening_times=None,
        fuel_types=None,
        temporary_closure=None,
        permanent_closure=None,
    )

    with patch("ukfuelfinder.FuelFinderClient") as mock_client:
        mock_client.return_value.search_by_location.return_value = [(2.5, mock_station)]
        mock_client.return_value.get_all_pfs_prices.return_value = []

        coordinator = UKFuelFinderCoordinator(hass, entry_data)
        data = await coordinator._async_update_data()

    # Verify defaults are applied
    station = data["stations"]["test123"]
    info = station["info"]

    assert info["amenities"] == []  # Default to empty list
    assert info["opening_times"] == {}  # Default to empty dict
    assert info["fuel_types_available"] == []  # Default to empty list


async def test_coordinator_stores_price_timestamps(hass):
    """Test coordinator stores price_timestamps alongside prices."""
    from datetime import datetime, timezone

    from ukfuelfinder.models import PFS, FuelPrice, Location, PFSInfo

    from custom_components.ukfuelfinder.coordinator import UKFuelFinderCoordinator

    entry_data = {
        "client_id": "test_id",
        "client_secret": "test_secret",
        "environment": "test",
        "latitude": 51.5074,
        "longitude": -0.1278,
        "radius": 5.0,
        "update_interval": 30,
    }

    mock_location = Location(latitude=51.5074, longitude=-0.1278)
    mock_station = PFSInfo(
        node_id="test123",
        mft_organisation_name="Test Org",
        trading_name="Test Station",
        public_phone_number=None,
        location=mock_location,
    )

    # Create PFS with timestamp
    test_timestamp = datetime(2026, 2, 8, 12, 0, 0, tzinfo=timezone.utc)
    mock_pfs = PFS(
        node_id="test123",
        mft_organisation_name="Test Org",
        trading_name="Test Station",
        public_phone_number=None,
        fuel_prices=[
            FuelPrice(fuel_type="E10", price=145.9, price_last_updated=test_timestamp),
        ],
    )

    with patch("ukfuelfinder.FuelFinderClient") as mock_client:
        mock_client.return_value.search_by_location.return_value = [(2.5, mock_station)]
        mock_client.return_value.get_all_pfs_prices.return_value = [mock_pfs]

        coordinator = UKFuelFinderCoordinator(hass, entry_data)
        data = await coordinator._async_update_data()

    # Verify price_timestamps stored
    station = data["stations"]["test123"]
    assert "price_timestamps" in station
    assert "e10" in station["price_timestamps"]
    assert station["price_timestamps"]["e10"] == test_timestamp


async def test_coordinator_handles_none_timestamp(hass):
    """Test coordinator handles None price_last_updated gracefully."""
    from ukfuelfinder.models import PFS, FuelPrice, Location, PFSInfo

    from custom_components.ukfuelfinder.coordinator import UKFuelFinderCoordinator

    entry_data = {
        "client_id": "test_id",
        "client_secret": "test_secret",
        "environment": "test",
        "latitude": 51.5074,
        "longitude": -0.1278,
        "radius": 5.0,
        "update_interval": 30,
    }

    mock_location = Location(latitude=51.5074, longitude=-0.1278)
    mock_station = PFSInfo(
        node_id="test123",
        mft_organisation_name="Test Org",
        trading_name="Test Station",
        public_phone_number=None,
        location=mock_location,
    )

    # Create PFS without timestamp
    mock_pfs = PFS(
        node_id="test123",
        mft_organisation_name="Test Org",
        trading_name="Test Station",
        public_phone_number=None,
        fuel_prices=[
            FuelPrice(fuel_type="E10", price=145.9, price_last_updated=None),
        ],
    )

    with patch("ukfuelfinder.FuelFinderClient") as mock_client:
        mock_client.return_value.search_by_location.return_value = [(2.5, mock_station)]
        mock_client.return_value.get_all_pfs_prices.return_value = [mock_pfs]

        coordinator = UKFuelFinderCoordinator(hass, entry_data)
        data = await coordinator._async_update_data()

    # Verify None timestamp handled
    station = data["stations"]["test123"]
    assert "price_timestamps" in station
    assert station["price_timestamps"]["e10"] is None
