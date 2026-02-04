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
                    "unleaded": 145.9,
                    "diesel": 155.9,
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

    assert len(entities) == 2  # unleaded and diesel
    assert entities[0]._fuel_type in ["unleaded", "diesel"]


async def test_sensor_state(hass, mock_coordinator):
    """Test sensor state."""
    from custom_components.ukfuelfinder.sensor import UKFuelFinderSensor

    station_data = mock_coordinator.data["stations"]["12345"]

    sensor = UKFuelFinderSensor(
        mock_coordinator,
        "12345",
        "unleaded",
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
        "unleaded",
        station_data,
    )

    attrs = sensor.extra_state_attributes

    assert attrs["station_name"] == "Test Station"
    assert attrs["brand"] == "TestBrand"
    assert attrs["distance_km"] == 2.5
    assert attrs["fuel_type"] == "unleaded"
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
