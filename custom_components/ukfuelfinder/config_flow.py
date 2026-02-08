"""Config flow for UK Fuel Finder integration."""

from __future__ import annotations

from typing import Any

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_CLIENT_ID, CONF_CLIENT_SECRET, CONF_LATITUDE, CONF_LONGITUDE
from homeassistant.core import callback

from .const import (
    CONF_ENVIRONMENT,
    CONF_FUEL_TYPES,
    CONF_RADIUS,
    CONF_UPDATE_INTERVAL,
    DEFAULT_ENVIRONMENT,
    DEFAULT_RADIUS,
    DEFAULT_UPDATE_INTERVAL,
    DOMAIN,
    FUEL_TYPES,
    MAX_RADIUS,
    MAX_UPDATE_INTERVAL,
    MIN_RADIUS,
    MIN_UPDATE_INTERVAL,
)


class UKFuelFinderConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for UK Fuel Finder."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            # Validate at least one fuel type selected
            if not user_input.get(CONF_FUEL_TYPES):
                errors["base"] = "no_fuel_types"
            else:
                # Validate credentials
                try:
                    from ukfuelfinder import FuelFinderClient

                    client = FuelFinderClient(
                        client_id=user_input[CONF_CLIENT_ID],
                        client_secret=user_input[CONF_CLIENT_SECRET],
                        environment=user_input[CONF_ENVIRONMENT],
                    )

                    # Test connection
                    await self.hass.async_add_executor_job(client.get_all_pfs_info)

                except Exception:
                    errors["base"] = "cannot_connect"
                else:
                    # Create unique ID based on client_id
                    await self.async_set_unique_id(user_input[CONF_CLIENT_ID])
                    self._abort_if_unique_id_configured()

                    return self.async_create_entry(
                        title="UK Fuel Finder",
                        data=user_input,
                    )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_CLIENT_ID): str,
                    vol.Required(CONF_CLIENT_SECRET): str,
                    vol.Required(CONF_ENVIRONMENT, default=DEFAULT_ENVIRONMENT): vol.In(
                        ["production", "test"]
                    ),
                    vol.Required(
                        CONF_LATITUDE,
                        default=self.hass.config.latitude,
                    ): cv.latitude,
                    vol.Required(
                        CONF_LONGITUDE,
                        default=self.hass.config.longitude,
                    ): cv.longitude,
                    vol.Required(CONF_RADIUS, default=DEFAULT_RADIUS): vol.All(
                        vol.Coerce(float), vol.Range(min=MIN_RADIUS, max=MAX_RADIUS)
                    ),
                    vol.Required(CONF_UPDATE_INTERVAL, default=DEFAULT_UPDATE_INTERVAL): vol.All(
                        vol.Coerce(int),
                        vol.Range(min=MIN_UPDATE_INTERVAL, max=MAX_UPDATE_INTERVAL),
                    ),
                    vol.Optional(CONF_FUEL_TYPES, default=FUEL_TYPES): cv.multi_select(
                        {fuel_type: fuel_type.replace("_", " ").title() for fuel_type in FUEL_TYPES}
                    ),
                }
            ),
            errors=errors,
        )

    async def async_step_reauth(
        self, entry_data: dict[str, Any]
    ) -> config_entries.ConfigFlowResult:
        """Handle reauthentication."""
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Confirm reauthentication."""
        errors = {}

        if user_input is not None:
            try:
                from ukfuelfinder import FuelFinderClient

                entry = self._get_reauth_entry()

                client = FuelFinderClient(
                    client_id=user_input[CONF_CLIENT_ID],
                    client_secret=user_input[CONF_CLIENT_SECRET],
                    environment=entry.data[CONF_ENVIRONMENT],
                )

                # Test connection
                await self.hass.async_add_executor_job(client.get_all_pfs_info)

            except Exception:
                errors["base"] = "invalid_auth"
            else:
                return self.async_update_reload_and_abort(
                    entry,
                    data_updates={
                        CONF_CLIENT_ID: user_input[CONF_CLIENT_ID],
                        CONF_CLIENT_SECRET: user_input[CONF_CLIENT_SECRET],
                    },
                )

        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_CLIENT_ID): str,
                    vol.Required(CONF_CLIENT_SECRET): str,
                }
            ),
            errors=errors,
        )

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Handle reconfiguration."""
        errors = {}
        entry = self._get_reconfigure_entry()

        if user_input is not None:
            # Validate at least one fuel type selected
            if not user_input.get(CONF_FUEL_TYPES):
                errors["base"] = "no_fuel_types"
            else:
                return self.async_update_reload_and_abort(
                    entry,
                    data_updates={
                        CONF_LATITUDE: user_input[CONF_LATITUDE],
                        CONF_LONGITUDE: user_input[CONF_LONGITUDE],
                        CONF_RADIUS: user_input[CONF_RADIUS],
                        CONF_UPDATE_INTERVAL: user_input[CONF_UPDATE_INTERVAL],
                        CONF_FUEL_TYPES: user_input[CONF_FUEL_TYPES],
                    },
                )

        return self.async_show_form(
            step_id="reconfigure",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_LATITUDE, default=entry.data[CONF_LATITUDE]): cv.latitude,
                    vol.Required(CONF_LONGITUDE, default=entry.data[CONF_LONGITUDE]): cv.longitude,
                    vol.Required(CONF_RADIUS, default=entry.data[CONF_RADIUS]): vol.All(
                        vol.Coerce(float), vol.Range(min=MIN_RADIUS, max=MAX_RADIUS)
                    ),
                    vol.Required(
                        CONF_UPDATE_INTERVAL, default=entry.data[CONF_UPDATE_INTERVAL]
                    ): vol.All(
                        vol.Coerce(int),
                        vol.Range(min=MIN_UPDATE_INTERVAL, max=MAX_UPDATE_INTERVAL),
                    ),
                    vol.Optional(
                        CONF_FUEL_TYPES,
                        default=entry.data.get(CONF_FUEL_TYPES, FUEL_TYPES)
                    ): cv.multi_select(
                        {fuel_type: fuel_type.replace("_", " ").title() for fuel_type in FUEL_TYPES}
                    ),
                }
            ),
            errors=errors,
        )
