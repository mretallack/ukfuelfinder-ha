"""Test UK Fuel Finder init."""

from unittest.mock import AsyncMock, patch

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.ukfuelfinder import async_setup_entry, async_unload_entry
from custom_components.ukfuelfinder.const import DOMAIN


async def test_setup_entry(hass):
    """Test setup entry."""
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

    with patch("ukfuelfinder.FuelFinderClient"):
        with patch(
            "custom_components.ukfuelfinder.coordinator.UKFuelFinderCoordinator._async_update_data",
            return_value={"stations": {}},
        ):
            assert await hass.config_entries.async_setup(entry.entry_id)
            await hass.async_block_till_done()

    assert DOMAIN in hass.data
    assert entry.entry_id in hass.data[DOMAIN]


async def test_unload_entry(hass):
    """Test unload entry."""
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

    with patch("ukfuelfinder.FuelFinderClient"):
        with patch(
            "custom_components.ukfuelfinder.coordinator.UKFuelFinderCoordinator._async_update_data",
            return_value={"stations": {}},
        ):
            await hass.config_entries.async_setup(entry.entry_id)
            await hass.async_block_till_done()

    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()

    assert entry.entry_id not in hass.data[DOMAIN]
