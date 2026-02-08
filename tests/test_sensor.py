"""Test UK Fuel Finder sensor platform."""

from unittest.mock import MagicMock, patch

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.ukfuelfinder.const import DOMAIN


@pytest.fixture
def mock_coordinator():
    """Mock coordinator with data."""
    coordinator = MagicMock()
    coordinator.data = {
        "stations": {
            "12345": {
                "info": {
                    "id": "12345",
                    "trading_name": "Test Station",
                    "address": "123 Test St",
                    "brand": "TestBrand",
                    "latitude": 51.5074,
                    "longitude": -0.1278,
                    "phone": "01234567890",
                },
                "distance": 2.5,
                "prices": {
                    "e10": 145.9,
                    "b7": 155.9,
                },
            }
        }
    }
    coordinator.async_add_listener = MagicMock()
    return coordinator


async def test_sensor_setup(hass, mock_coordinator):
    """Test sensor platform setup."""
    from custom_components.ukfuelfinder.sensor import async_setup_entry

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

    hass.data[DOMAIN] = {entry.entry_id: mock_coordinator}

    entities = []

    def add_entities(new_entities):
        entities.extend(new_entities)

    await async_setup_entry(hass, entry, add_entities)

    # Should have 2 station sensors (e10, b7) + 6 cheapest sensors (one per fuel type)
    assert len(entities) == 8
    
    # Check we have station sensors
    station_sensors = [e for e in entities if hasattr(e, '_station_id')]
    assert len(station_sensors) == 2
    assert station_sensors[0]._fuel_type in ["e10", "b7"]
    
    # Check we have cheapest sensors
    cheapest_sensors = [e for e in entities if not hasattr(e, '_station_id')]
    assert len(cheapest_sensors) == 6


async def test_sensor_state(hass, mock_coordinator):
    """Test sensor state."""
    from custom_components.ukfuelfinder.sensor import UKFuelFinderSensor

    station_data = mock_coordinator.data["stations"]["12345"]

    sensor = UKFuelFinderSensor(
        mock_coordinator,
        "12345",
        "e10",
        station_data,
    )

    assert sensor.native_value == 1.459  # 145.9 pence = 1.459 pounds
    assert sensor.native_unit_of_measurement == "GBP"
    assert sensor.available is True


async def test_sensor_attributes(hass, mock_coordinator):
    """Test sensor attributes."""
    from custom_components.ukfuelfinder.sensor import UKFuelFinderSensor

    station_data = mock_coordinator.data["stations"]["12345"]

    sensor = UKFuelFinderSensor(
        mock_coordinator,
        "12345",
        "e10",
        station_data,
    )

    attrs = sensor.extra_state_attributes

    assert attrs["station_name"] == "Test Station"
    assert attrs["brand"] == "TestBrand"
    assert attrs["distance_km"] == 2.5
    assert attrs["fuel_type"] == "e10"
    assert attrs["price_pence"] == 145.9


async def test_sensor_unavailable_when_no_data(hass):
    """Test sensor is unavailable when no data."""
    from custom_components.ukfuelfinder.sensor import UKFuelFinderSensor

    coordinator = MagicMock()
    coordinator.data = None

    station_data = {
        "info": {
            "trading_name": "Test",
            "brand": "Test",
        },
        "distance": 0,
        "prices": {},
    }

    sensor = UKFuelFinderSensor(
        coordinator,
        "12345",
        "unleaded",
        station_data,
    )

    assert sensor.available is False


async def test_sensor_display_precision(hass, mock_coordinator):
    """Test sensor has correct display precision for currency."""
    from custom_components.ukfuelfinder.sensor import UKFuelFinderSensor

    station_data = mock_coordinator.data["stations"]["12345"]

    sensor = UKFuelFinderSensor(
        mock_coordinator,
        "12345",
        "unleaded",
        station_data,
    )

    # Currency should display with 2 decimal places
    assert sensor.suggested_display_precision == 2


async def test_dynamic_station_addition(hass):
    """Test that new stations are automatically added when detected."""
    from custom_components.ukfuelfinder.sensor import async_setup_entry

    # Create coordinator with initial station
    coordinator = MagicMock()
    coordinator.data = {
        "stations": {
            "12345": {
                "info": {
                    "id": "12345",
                    "trading_name": "Station 1",
                    "address": "123 Test St",
                    "brand": "TestBrand",
                    "latitude": 51.5074,
                    "longitude": -0.1278,
                    "phone": "01234567890",
                },
                "distance": 2.5,
                "prices": {
                    "e10": 145.9,
                },
            }
        }
    }

    listeners = []
    coordinator.async_add_listener = lambda callback: listeners.append(callback)

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
    entry.async_on_unload = MagicMock()

    hass.data[DOMAIN] = {entry.entry_id: coordinator}

    entities_added = []

    def track_entities(new_entities):
        entities_added.extend(new_entities)

    # Initial setup
    await async_setup_entry(hass, entry, track_entities)

    # Should have 1 station sensor + 6 cheapest sensors initially
    assert len(entities_added) == 7
    station_sensors = [e for e in entities_added if hasattr(e, '_station_id')]
    assert len(station_sensors) == 1
    assert station_sensors[0]._station_id == "12345"
    assert station_sensors[0]._fuel_type == "e10"

    # Add a new station to coordinator data
    coordinator.data["stations"]["67890"] = {
        "info": {
            "id": "67890",
            "trading_name": "Station 2",
            "address": "456 Test Ave",
            "brand": "TestBrand2",
            "latitude": 51.5075,
            "longitude": -0.1279,
            "phone": "09876543210",
        },
        "distance": 3.5,
        "prices": {
            "b7": 155.9,
        },
    }

    # Trigger coordinator update callback
    assert len(listeners) == 1
    listeners[0]()

    # Should now have 8 sensors total (7 initial + 1 new station sensor)
    # Cheapest sensors don't get recreated
    assert len(entities_added) == 8
    station_sensors = [e for e in entities_added if hasattr(e, '_station_id')]
    assert len(station_sensors) == 2
    assert station_sensors[1]._station_id == "67890"
    assert station_sensors[1]._fuel_type == "b7"

    # Trigger again with same data - should not add duplicates
    listeners[0]()
    assert len(entities_added) == 8
