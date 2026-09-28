"""Test extra decimal place option for sensors."""

from unittest.mock import MagicMock, patch

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.ukfuelfinder.const import CONF_EXTRA_DECIMAL, DOMAIN


@pytest.fixture
def mock_coordinator():
    """Mock coordinator."""
    coordinator = MagicMock()
    coordinator.data = {
        "stations": {
            "12345": {
                "info": {
                    "id": "12345",
                    "trading_name": "Test Station",
                    "brand": "Test Brand",
                },
                "distance": 1.0,
                "prices": {"unleaded": 145.9},
            }
        }
    }
    return coordinator


async def test_sensor_precision_default(hass, mock_coordinator):
    """Test default display precision is 2 decimals."""
    from custom_components.ukfuelfinder.sensor import UKFuelFinderSensor

    station_data = mock_coordinator.data["stations"]["12345"]
    entry = MockConfigEntry(domain=DOMAIN, data={CONF_EXTRA_DECIMAL: False})
    sensor = UKFuelFinderSensor(mock_coordinator, "12345", "unleaded", station_data, entry)

    assert sensor.suggested_display_precision == 2


async def test_sensor_precision_extra_decimal(hass, mock_coordinator):
    """Test display precision is 3 decimals when extra_decimal is enabled."""
    from custom_components.ukfuelfinder.sensor import UKFuelFinderSensor

    station_data = mock_coordinator.data["stations"]["12345"]
    entry = MockConfigEntry(domain=DOMAIN, data={CONF_EXTRA_DECIMAL: True})
    sensor = UKFuelFinderSensor(mock_coordinator, "12345", "unleaded", station_data, entry)

    assert sensor.suggested_display_precision == 3


async def test_cheapest_sensor_precision_extra_decimal(hass, mock_coordinator):
    """Test cheapest sensor display precision is 3 decimals when extra_decimal is enabled."""
    from custom_components.ukfuelfinder.sensor import UKFuelFinderCheapestSensor

    entry = MockConfigEntry(domain=DOMAIN, data={CONF_EXTRA_DECIMAL: True})
    sensor = UKFuelFinderCheapestSensor(mock_coordinator, "unleaded", entry)

    assert sensor.suggested_display_precision == 3
