"""Test cheapest sensor functionality."""

from unittest.mock import MagicMock

import pytest
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from custom_components.ukfuelfinder.const import DOMAIN


@pytest.fixture
def mock_coordinator_with_prices():
    """Mock coordinator with multiple stations and prices."""
    coordinator = MagicMock(spec=DataUpdateCoordinator)
    coordinator.last_update_success = True  # Add this for available property
    coordinator.data = {
        "stations": {
            "station1": {
                "info": {
                    "id": "station1",
                    "trading_name": "Cheap Station",
                    "address": "123 Test St",
                    "brand": "TestBrand",
                    "latitude": 51.5074,
                    "longitude": -0.1278,
                    "phone": "01234567890",
                    "is_supermarket": True,
                    "is_motorway": False,
                    "amenities": ["customer_toilets", "car_wash"],
                    "opening_times": {"monday": {"open": "06:00", "close": "22:00"}},
                    "fuel_types_available": ["e10", "b7"],
                    "organization_name": "Test Org",
                    "temporary_closure": False,
                    "permanent_closure": None,
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
                    "trading_name": "Expensive Station",
                    "address": "456 Test Ave",
                    "brand": "TestBrand2",
                    "latitude": 51.5075,
                    "longitude": -0.1279,
                    "phone": "09876543210",
                    "is_supermarket": False,
                    "is_motorway": True,
                    "amenities": ["adblue_at_pump"],
                    "opening_times": {},
                    "fuel_types_available": ["e10", "e5"],
                    "organization_name": "Test Org 2",
                    "temporary_closure": None,
                    "permanent_closure": False,
                },
                "distance": 3.5,
                "prices": {
                    "e10": 150.9,
                    "e5": 160.9,
                },
            },
        }
    }
    return coordinator


async def test_cheapest_sensor_finds_lowest_price(hass, mock_coordinator_with_prices):
    """Test cheapest sensor finds the lowest price."""
    from custom_components.ukfuelfinder.sensor import UKFuelFinderCheapestSensor
    from custom_components.ukfuelfinder.coordinator import UKFuelFinderCoordinator

    # Add get_cheapest_fuel method to mock
    def get_cheapest_fuel(fuel_type):
        cheapest = None
        cheapest_price = float('inf')
        for station_id, station_data in mock_coordinator_with_prices.data["stations"].items():
            price = station_data["prices"].get(fuel_type)
            if price and price < cheapest_price:
                cheapest_price = price
                cheapest = {
                    "station_id": station_id,
                    "price": price,
                    **station_data["info"],
                    "distance": station_data["distance"],
                }
        return cheapest

    mock_coordinator_with_prices.get_cheapest_fuel = get_cheapest_fuel

    sensor = UKFuelFinderCheapestSensor(mock_coordinator_with_prices, "e10")

    # Should find station1 with 145.9 pence
    assert sensor.native_value == 1.459
    assert sensor.available is True


async def test_cheapest_sensor_attributes(hass, mock_coordinator_with_prices):
    """Test cheapest sensor includes all attributes."""
    from custom_components.ukfuelfinder.sensor import UKFuelFinderCheapestSensor

    def get_cheapest_fuel(fuel_type):
        cheapest = None
        cheapest_price = float('inf')
        for station_id, station_data in mock_coordinator_with_prices.data["stations"].items():
            price = station_data["prices"].get(fuel_type)
            if price and price < cheapest_price:
                cheapest_price = price
                cheapest = {
                    "station_id": station_id,
                    "price": price,
                    **station_data["info"],
                    "distance": station_data["distance"],
                }
        return cheapest

    mock_coordinator_with_prices.get_cheapest_fuel = get_cheapest_fuel

    sensor = UKFuelFinderCheapestSensor(mock_coordinator_with_prices, "e10")
    attrs = sensor.extra_state_attributes

    # Check basic attributes
    assert attrs["station_name"] == "Cheap Station"
    assert attrs["brand"] == "TestBrand"
    assert attrs["distance_km"] == 2.5
    assert attrs["price_pence"] == 145.9
    assert attrs["station_id"] == "station1"

    # Check metadata attributes
    assert attrs["is_supermarket"] is True
    assert attrs["is_motorway"] is False
    assert attrs["amenities"] == ["customer_toilets", "car_wash"]
    assert attrs["opening_times"] == {"monday": {"open": "06:00", "close": "22:00"}}
    assert attrs["fuel_types_available"] == ["e10", "b7"]
    assert attrs["organization_name"] == "Test Org"
    assert attrs["temporary_closure"] is False
    assert attrs["permanent_closure"] is None


async def test_cheapest_sensor_no_stations(hass):
    """Test cheapest sensor when no stations have the fuel type."""
    from custom_components.ukfuelfinder.sensor import UKFuelFinderCheapestSensor

    coordinator = MagicMock()
    coordinator.data = {"stations": {}}
    coordinator.get_cheapest_fuel = lambda fuel_type: None

    sensor = UKFuelFinderCheapestSensor(coordinator, "e10")

    assert sensor.native_value is None
    assert sensor.available is False
    assert sensor.extra_state_attributes == {}


async def test_cheapest_sensor_switches_station(hass, mock_coordinator_with_prices):
    """Test cheapest sensor switches when a cheaper station appears."""
    from custom_components.ukfuelfinder.sensor import UKFuelFinderCheapestSensor

    def get_cheapest_fuel(fuel_type):
        cheapest = None
        cheapest_price = float('inf')
        for station_id, station_data in mock_coordinator_with_prices.data["stations"].items():
            price = station_data["prices"].get(fuel_type)
            if price and price < cheapest_price:
                cheapest_price = price
                cheapest = {
                    "station_id": station_id,
                    "price": price,
                    **station_data["info"],
                    "distance": station_data["distance"],
                }
        return cheapest

    mock_coordinator_with_prices.get_cheapest_fuel = get_cheapest_fuel

    sensor = UKFuelFinderCheapestSensor(mock_coordinator_with_prices, "e10")

    # Initially station1 is cheapest
    assert sensor.extra_state_attributes["station_id"] == "station1"
    assert sensor.native_value == 1.459

    # Add a cheaper station
    mock_coordinator_with_prices.data["stations"]["station3"] = {
        "info": {
            "id": "station3",
            "trading_name": "Super Cheap Station",
            "address": "789 Test Rd",
            "brand": "TestBrand3",
            "latitude": 51.5076,
            "longitude": -0.1280,
            "phone": "01111111111",
            "is_supermarket": True,
            "is_motorway": False,
            "amenities": [],
            "opening_times": {},
            "fuel_types_available": ["e10"],
            "organization_name": "Test Org 3",
            "temporary_closure": None,
            "permanent_closure": None,
        },
        "distance": 1.5,
        "prices": {
            "e10": 140.9,
        },
    }

    # Now station3 should be cheapest
    assert sensor.extra_state_attributes["station_id"] == "station3"
    assert sensor.native_value == 1.409


async def test_cheapest_sensor_device_info(hass, mock_coordinator_with_prices):
    """Test cheapest sensor has correct device info."""
    from custom_components.ukfuelfinder.sensor import UKFuelFinderCheapestSensor

    mock_coordinator_with_prices.get_cheapest_fuel = lambda fuel_type: None

    sensor = UKFuelFinderCheapestSensor(mock_coordinator_with_prices, "e10")

    assert sensor._attr_device_info["identifiers"] == {(DOMAIN, "cheapest")}
    assert sensor._attr_device_info["name"] == "Cheapest Fuel Prices"
    assert sensor._attr_device_info["manufacturer"] == "UK Fuel Finder"
    assert sensor._attr_device_info["model"] == "Aggregate Sensor"


async def test_cheapest_sensor_unique_id(hass, mock_coordinator_with_prices):
    """Test cheapest sensor has correct unique ID."""
    from custom_components.ukfuelfinder.sensor import UKFuelFinderCheapestSensor

    mock_coordinator_with_prices.get_cheapest_fuel = lambda fuel_type: None

    sensor = UKFuelFinderCheapestSensor(mock_coordinator_with_prices, "e10")

    assert sensor._attr_unique_id == "cheapest_e10"
    assert sensor._attr_name == "Cheapest E10"
