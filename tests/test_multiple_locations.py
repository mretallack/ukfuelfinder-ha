"""Test adding multiple static locations with the same client ID (Issue #15)."""

from unittest.mock import patch

import pytest
from homeassistant import config_entries
from homeassistant.const import CONF_CLIENT_ID, CONF_CLIENT_SECRET, CONF_LATITUDE, CONF_LONGITUDE
from homeassistant.data_entry_flow import FlowResultType

from custom_components.ukfuelfinder.const import DOMAIN, FUEL_TYPES


async def test_multiple_static_locations_allowed(hass):
    """Test that multiple config entries with the same client_id but different coordinates can be created."""
    with patch("ukfuelfinder.FuelFinderClient") as mock_client:
        mock_instance = mock_client.return_value
        mock_instance.get_all_pfs_info.return_value = []

        # Flow 1: Home location
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_CLIENT_ID: "shared_client_id",
                CONF_CLIENT_SECRET: "shared_secret",
                "environment": "test",
                "location_mode": "static",
            },
        )
        assert result["step_id"] == "location_static"

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_LATITUDE: 51.5074,
                CONF_LONGITUDE: -0.1278,
                "radius": 5.0,
                "cheapest_radius": 5.0,
                "update_interval": 30,
                "fuel_types": FUEL_TYPES,
            },
        )
        assert result["type"] == FlowResultType.CREATE_ENTRY

        # Flow 2: Work location (same client_id, different coordinates)
        result2 = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result2 = await hass.config_entries.flow.async_configure(
            result2["flow_id"],
            {
                CONF_CLIENT_ID: "shared_client_id",
                CONF_CLIENT_SECRET: "shared_secret",
                "environment": "test",
                "location_mode": "static",
            },
        )
        assert result2["step_id"] == "location_static"

        result2 = await hass.config_entries.flow.async_configure(
            result2["flow_id"],
            {
                CONF_LATITUDE: 53.4808,
                CONF_LONGITUDE: -2.2426,
                "radius": 5.0,
                "cheapest_radius": 5.0,
                "update_interval": 30,
                "fuel_types": FUEL_TYPES,
            },
        )
        assert result2["type"] == FlowResultType.CREATE_ENTRY
