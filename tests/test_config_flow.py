"""Test UK Fuel Finder config flow."""
from unittest.mock import patch

import pytest
from homeassistant import config_entries
from homeassistant.const import CONF_CLIENT_ID, CONF_CLIENT_SECRET, CONF_LATITUDE, CONF_LONGITUDE

from custom_components.ukfuelfinder.const import DOMAIN


async def test_form(hass):
    """Test we get the form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == "form"
    assert result["errors"] == {}


async def test_user_flow_success(hass):
    """Test successful user flow."""
    with patch(
        "custom_components.ukfuelfinder.config_flow.FuelFinderClient"
    ) as mock_client:
        mock_client.return_value.get_all_pfs_info.return_value = []
        
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_CLIENT_ID: "test_id",
                CONF_CLIENT_SECRET: "test_secret",
                "environment": "test",
                CONF_LATITUDE: 51.5074,
                CONF_LONGITUDE: -0.1278,
                "radius": 5.0,
                "update_interval": 30,
            },
        )
        
        assert result["type"] == "create_entry"
        assert result["title"] == "UK Fuel Finder"
