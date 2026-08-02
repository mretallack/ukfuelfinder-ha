"""Test UK Fuel Finder config flow."""

from unittest.mock import AsyncMock, patch

import pytest
from homeassistant import config_entries
from homeassistant.const import CONF_CLIENT_ID, CONF_CLIENT_SECRET, CONF_LATITUDE, CONF_LONGITUDE
from homeassistant.data_entry_flow import FlowResultType

from custom_components.ukfuelfinder.const import DOMAIN


async def test_form(hass):
    """Test we get the form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == FlowResultType.FORM
    assert result["errors"] == {}


async def test_user_flow_success(hass):
    """Test successful user flow."""
    with patch("ukfuelfinder.FuelFinderClient") as mock_client:
        mock_instance = mock_client.return_value
        mock_instance.get_all_pfs_info = lambda: []

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

        assert result["type"] == FlowResultType.CREATE_ENTRY
        assert result["title"] == "UK Fuel Finder"


async def test_user_flow_with_dynamic_location(hass):
    """Test user flow with dynamic location source."""
    # Set up a person entity
    hass.states.async_set(
        "person.mark", "home", {"friendly_name": "Mark", "latitude": 52.0, "longitude": -1.0}
    )

    with patch("ukfuelfinder.FuelFinderClient") as mock_client:
        mock_instance = mock_client.return_value
        mock_instance.get_all_pfs_info = lambda: []

        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_CLIENT_ID: "test_id",
                CONF_CLIENT_SECRET: "test_secret",
                "environment": "test",
                "location_source": "person.mark",
                CONF_LATITUDE: 51.5074,
                CONF_LONGITUDE: -0.1278,
                "radius": 5.0,
                "update_interval": 30,
            },
        )

        assert result["type"] == FlowResultType.CREATE_ENTRY
        assert result["data"]["location_source"] == "person.mark"
        # Should store HA home as fallback lat/lon
        assert result["data"][CONF_LATITUDE] == hass.config.latitude
        assert result["data"][CONF_LONGITUDE] == hass.config.longitude


async def test_user_flow_entity_not_found_error(hass):
    """Test user flow shows error when selected entity doesn't exist."""
    with patch("ukfuelfinder.FuelFinderClient") as mock_client:
        mock_instance = mock_client.return_value
        mock_instance.get_all_pfs_info = lambda: []

        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_CLIENT_ID: "test_id",
                CONF_CLIENT_SECRET: "test_secret",
                "environment": "test",
                "location_source": "person.nonexistent",
                CONF_LATITUDE: 51.5074,
                CONF_LONGITUDE: -0.1278,
                "radius": 5.0,
                "update_interval": 30,
                "fuel_types": ["e10"],
            },
        )

        assert result["type"] == FlowResultType.FORM
        assert result["errors"] == {"base": "entity_not_found"}


async def test_user_flow_static_location(hass):
    """Test user flow with static location stores user-provided coordinates."""
    with patch("ukfuelfinder.FuelFinderClient") as mock_client:
        mock_instance = mock_client.return_value
        mock_instance.get_all_pfs_info = lambda: []

        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_CLIENT_ID: "test_id_2",
                CONF_CLIENT_SECRET: "test_secret",
                "environment": "test",
                "location_source": "static",
                CONF_LATITUDE: 52.5,
                CONF_LONGITUDE: -1.9,
                "radius": 10.0,
                "update_interval": 60,
            },
        )

        assert result["type"] == FlowResultType.CREATE_ENTRY
        assert result["data"]["location_source"] == "static"
        assert result["data"][CONF_LATITUDE] == 52.5
        assert result["data"][CONF_LONGITUDE] == -1.9


async def test_user_flow_connection_failure(hass):
    """Test user flow shows error when API connection fails."""
    with patch("ukfuelfinder.FuelFinderClient") as mock_client:
        mock_instance = mock_client.return_value
        mock_instance.get_all_pfs_info = lambda: (_ for _ in ()).throw(
            Exception("Connection timeout")
        )

        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_CLIENT_ID: "bad_id",
                CONF_CLIENT_SECRET: "bad_secret",
                "environment": "test",
                "location_source": "static",
                CONF_LATITUDE: 51.5074,
                CONF_LONGITUDE: -0.1278,
                "radius": 5.0,
                "update_interval": 30,
                "fuel_types": ["e10"],
            },
        )

        assert result["type"] == FlowResultType.FORM
        assert result["errors"] == {"base": "cannot_connect"}


async def test_user_flow_no_fuel_types_error(hass):
    """Test user flow shows error when no fuel types selected."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_CLIENT_ID: "test_id",
            CONF_CLIENT_SECRET: "test_secret",
            "environment": "test",
            "location_source": "static",
            CONF_LATITUDE: 51.5074,
            CONF_LONGITUDE: -0.1278,
            "radius": 5.0,
            "update_interval": 30,
            "fuel_types": [],
        },
    )

    assert result["type"] == FlowResultType.FORM
    assert result["errors"] == {"base": "no_fuel_types"}
