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
    assert result["step_id"] == "user"


async def test_user_flow_static_success(hass):
    """Test successful user flow with static location."""
    with patch("ukfuelfinder.FuelFinderClient") as mock_client:
        mock_instance = mock_client.return_value
        mock_instance.get_all_pfs_info = lambda: []

        # Step 1: credentials + location mode
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_CLIENT_ID: "test_id",
                CONF_CLIENT_SECRET: "test_secret",
                "environment": "test",
                "location_mode": "static",
            },
        )

        # Should advance to location_static step
        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "location_static"

        # Step 2: static location details
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_LATITUDE: 51.5074,
                CONF_LONGITUDE: -0.1278,
                "radius": 5.0,
                "update_interval": 30,
            },
        )

        assert result["type"] == FlowResultType.CREATE_ENTRY
        assert result["title"] == "UK Fuel Finder"
        assert result["data"]["location_source"] == "static"
        assert result["data"][CONF_LATITUDE] == 51.5074
        assert result["data"][CONF_LONGITUDE] == -0.1278


async def test_user_flow_dynamic_success(hass):
    """Test successful user flow with dynamic location."""
    # Set up a person entity
    hass.states.async_set(
        "person.mark", "home", {"friendly_name": "Mark", "latitude": 52.0, "longitude": -1.0}
    )

    with patch("ukfuelfinder.FuelFinderClient") as mock_client:
        mock_instance = mock_client.return_value
        mock_instance.get_all_pfs_info = lambda: []

        # Step 1: credentials + location mode
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_CLIENT_ID: "test_id",
                CONF_CLIENT_SECRET: "test_secret",
                "environment": "test",
                "location_mode": "dynamic",
            },
        )

        # Should advance to location_dynamic step
        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "location_dynamic"

        # Step 2: select entity
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "location_source": "person.mark",
                "radius": 5.0,
                "update_interval": 30,
            },
        )

        assert result["type"] == FlowResultType.CREATE_ENTRY
        assert result["title"] == "UK Fuel Finder (Mark)"
        assert result["data"]["location_source"] == "person.mark"
        # Should store HA home as fallback
        assert result["data"][CONF_LATITUDE] == hass.config.latitude
        assert result["data"][CONF_LONGITUDE] == hass.config.longitude


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
                "location_mode": "static",
            },
        )

        # Should stay on step 1 with error
        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "user"
        assert result["errors"] == {"base": "cannot_connect"}


async def test_user_flow_no_fuel_types_error(hass):
    """Test user flow shows error when no fuel types selected."""
    with patch("ukfuelfinder.FuelFinderClient") as mock_client:
        mock_instance = mock_client.return_value
        mock_instance.get_all_pfs_info = lambda: []

        # Step 1
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_CLIENT_ID: "test_id",
                CONF_CLIENT_SECRET: "test_secret",
                "environment": "test",
                "location_mode": "static",
            },
        )

        # Step 2: submit with no fuel types
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_LATITUDE: 51.5074,
                CONF_LONGITUDE: -0.1278,
                "radius": 5.0,
                "update_interval": 30,
                "fuel_types": [],
            },
        )

        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "location_static"
        assert result["errors"] == {"base": "no_fuel_types"}


async def test_user_flow_entity_not_found_error(hass):
    """Test dynamic flow shows error when entity doesn't exist."""
    with patch("ukfuelfinder.FuelFinderClient") as mock_client:
        mock_instance = mock_client.return_value
        mock_instance.get_all_pfs_info = lambda: []

        # Step 1
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_CLIENT_ID: "test_id",
                CONF_CLIENT_SECRET: "test_secret",
                "environment": "test",
                "location_mode": "dynamic",
            },
        )

        # Step 2: submit with non-existent entity
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "location_source": "person.nonexistent",
                "radius": 5.0,
                "update_interval": 30,
                "fuel_types": ["e10"],
            },
        )

        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "location_dynamic"
        assert result["errors"] == {"base": "entity_not_found"}


# ── Reconfigure tests ──


async def test_reconfigure_static_to_dynamic(hass):
    """Test reconfigure flow switching from static to dynamic."""
    from pytest_homeassistant_custom_component.common import MockConfigEntry

    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_CLIENT_ID: "test_id",
            CONF_CLIENT_SECRET: "test_secret",
            "environment": "test",
            CONF_LATITUDE: 51.5074,
            CONF_LONGITUDE: -0.1278,
            "radius": 5.0,
            "update_interval": 30,
            "fuel_types": ["e10"],
            "location_source": "static",
        },
    )
    entry.add_to_hass(hass)

    # Set up a person entity
    hass.states.async_set(
        "person.mark", "home", {"friendly_name": "Mark", "latitude": 52.0, "longitude": -1.0}
    )

    # Step 1: choose dynamic
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": "reconfigure", "entry_id": entry.entry_id},
    )
    assert result["step_id"] == "reconfigure"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"location_mode": "dynamic"},
    )
    assert result["step_id"] == "reconfigure_dynamic"

    # Step 2: select entity
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            "location_source": "person.mark",
            "radius": 10.0,
            "update_interval": 15,
            "fuel_types": ["e10", "b7"],
        },
    )

    assert result["type"] == FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"
    assert entry.data["location_source"] == "person.mark"
    assert entry.data["radius"] == 10.0


async def test_reconfigure_dynamic_to_static(hass):
    """Test reconfigure flow switching from dynamic to static."""
    from pytest_homeassistant_custom_component.common import MockConfigEntry

    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_CLIENT_ID: "test_id",
            CONF_CLIENT_SECRET: "test_secret",
            "environment": "test",
            CONF_LATITUDE: 51.5074,
            CONF_LONGITUDE: -0.1278,
            "radius": 5.0,
            "update_interval": 30,
            "fuel_types": ["e10"],
            "location_source": "person.mark",
        },
    )
    entry.add_to_hass(hass)

    # Step 1: choose static
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": "reconfigure", "entry_id": entry.entry_id},
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"location_mode": "static"},
    )
    assert result["step_id"] == "reconfigure_static"

    # Step 2: enter coords
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_LATITUDE: 52.5,
            CONF_LONGITUDE: -1.9,
            "radius": 8.0,
            "update_interval": 60,
            "fuel_types": ["e10"],
        },
    )

    assert result["type"] == FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"
    assert entry.data["location_source"] == "static"
    assert entry.data[CONF_LATITUDE] == 52.5


async def test_reconfigure_backward_compat_no_location_source(hass):
    """Test reconfigure with old entry that has no location_source key."""
    from pytest_homeassistant_custom_component.common import MockConfigEntry

    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_CLIENT_ID: "test_id",
            CONF_CLIENT_SECRET: "test_secret",
            "environment": "test",
            CONF_LATITUDE: 51.5074,
            CONF_LONGITUDE: -0.1278,
            "radius": 5.0,
            "update_interval": 30,
            "fuel_types": ["e10"],
        },
    )
    entry.add_to_hass(hass)

    # Step 1: defaults to static mode
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": "reconfigure", "entry_id": entry.entry_id},
    )
    assert result["step_id"] == "reconfigure"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"location_mode": "static"},
    )
    assert result["step_id"] == "reconfigure_static"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_LATITUDE: 51.5074,
            CONF_LONGITUDE: -0.1278,
            "radius": 5.0,
            "update_interval": 30,
            "fuel_types": ["e10"],
        },
    )

    assert result["type"] == FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"
