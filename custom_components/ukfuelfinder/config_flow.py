"""Config flow for UK Fuel Finder integration."""

from __future__ import annotations

from typing import Any

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_CLIENT_ID, CONF_CLIENT_SECRET, CONF_LATITUDE, CONF_LONGITUDE
from homeassistant.core import callback
from homeassistant.helpers.selector import (
    EntitySelector,
    EntitySelectorConfig,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
)

from .const import (
    CONF_ENVIRONMENT,
    CONF_FUEL_TYPES,
    CONF_LOCATION_SOURCE,
    CONF_RADIUS,
    CONF_UPDATE_INTERVAL,
    DEFAULT_ENVIRONMENT,
    DEFAULT_RADIUS,
    DEFAULT_UPDATE_INTERVAL,
    DOMAIN,
    FUEL_TYPES,
    LOCATION_SOURCE_STATIC,
    MAX_RADIUS,
    MAX_UPDATE_INTERVAL,
    MIN_RADIUS,
    MIN_UPDATE_INTERVAL,
)

LOCATION_MODE_STATIC = "static"
LOCATION_MODE_DYNAMIC = "dynamic"
CONF_LOCATION_MODE = "location_mode"


class UKFuelFinderConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for UK Fuel Finder."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._user_data: dict[str, Any] = {}

    # ──────────────────────────────────────────────
    # Initial setup: Step 1 - Credentials + location mode
    # ──────────────────────────────────────────────

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Handle step 1: credentials and location mode selection."""
        errors = {}

        if user_input is not None:
            # Validate credentials
            try:
                from ukfuelfinder import FuelFinderClient

                client = FuelFinderClient(
                    client_id=user_input[CONF_CLIENT_ID],
                    client_secret=user_input[CONF_CLIENT_SECRET],
                    environment=user_input[CONF_ENVIRONMENT],
                )

                await self.hass.async_add_executor_job(client.get_all_pfs_info)

            except Exception:
                errors["base"] = "cannot_connect"
            else:
                # Store and proceed to location step
                self._user_data = user_input
                location_mode = user_input.get(CONF_LOCATION_MODE, LOCATION_MODE_STATIC)

                if location_mode == LOCATION_MODE_DYNAMIC:
                    return await self.async_step_location_dynamic()
                return await self.async_step_location_static()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_CLIENT_ID): str,
                    vol.Required(CONF_CLIENT_SECRET): str,
                    vol.Required(CONF_ENVIRONMENT, default=DEFAULT_ENVIRONMENT): vol.In(
                        ["production", "test"]
                    ),
                    vol.Required(CONF_LOCATION_MODE, default=LOCATION_MODE_STATIC): SelectSelector(
                        SelectSelectorConfig(
                            options=[
                                {
                                    "label": "Static (manual coordinates)",
                                    "value": LOCATION_MODE_STATIC,
                                },
                                {
                                    "label": "Dynamic (follow a person or device)",
                                    "value": LOCATION_MODE_DYNAMIC,
                                },
                            ],
                            mode=SelectSelectorMode.DROPDOWN,
                        )
                    ),
                }
            ),
            errors=errors,
        )

    # ──────────────────────────────────────────────
    # Initial setup: Step 2a - Static location
    # ──────────────────────────────────────────────

    async def async_step_location_static(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Handle step 2: static location configuration."""
        errors = {}

        if user_input is not None:
            if not user_input.get(CONF_FUEL_TYPES):
                errors["base"] = "no_fuel_types"
            else:
                # Create unique ID
                await self.async_set_unique_id(self._user_data[CONF_CLIENT_ID])
                self._abort_if_unique_id_configured()

                # Merge data
                data = {
                    **self._user_data,
                    **user_input,
                    CONF_LOCATION_SOURCE: LOCATION_SOURCE_STATIC,
                }
                # Remove the location_mode key (not stored)
                data.pop(CONF_LOCATION_MODE, None)

                return self.async_create_entry(title="UK Fuel Finder", data=data)

        return self.async_show_form(
            step_id="location_static",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_LATITUDE, default=self.hass.config.latitude): cv.latitude,
                    vol.Required(CONF_LONGITUDE, default=self.hass.config.longitude): cv.longitude,
                    vol.Required(CONF_RADIUS, default=DEFAULT_RADIUS): vol.All(
                        vol.Coerce(float), vol.Range(min=MIN_RADIUS, max=MAX_RADIUS)
                    ),
                    vol.Required(CONF_UPDATE_INTERVAL, default=DEFAULT_UPDATE_INTERVAL): vol.All(
                        vol.Coerce(int),
                        vol.Range(min=MIN_UPDATE_INTERVAL, max=MAX_UPDATE_INTERVAL),
                    ),
                    vol.Optional(CONF_FUEL_TYPES, default=FUEL_TYPES): cv.multi_select(
                        {ft: ft.replace("_", " ").title() for ft in FUEL_TYPES}
                    ),
                }
            ),
            errors=errors,
        )

    # ──────────────────────────────────────────────
    # Initial setup: Step 2b - Dynamic location
    # ──────────────────────────────────────────────

    async def async_step_location_dynamic(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Handle step 2: dynamic location configuration."""
        errors = {}

        if user_input is not None:
            if not user_input.get(CONF_FUEL_TYPES):
                errors["base"] = "no_fuel_types"
            else:
                # Validate entity exists
                entity_id = user_input.get(CONF_LOCATION_SOURCE)
                if not entity_id or self.hass.states.get(entity_id) is None:
                    errors["base"] = "entity_not_found"

                if not errors:
                    # Create unique ID
                    await self.async_set_unique_id(self._user_data[CONF_CLIENT_ID])
                    self._abort_if_unique_id_configured()

                    # Merge data — use HA home as fallback lat/lon
                    data = {
                        **self._user_data,
                        **user_input,
                        CONF_LATITUDE: self.hass.config.latitude,
                        CONF_LONGITUDE: self.hass.config.longitude,
                    }
                    # Remove the location_mode key (not stored)
                    data.pop(CONF_LOCATION_MODE, None)

                    return self.async_create_entry(title="UK Fuel Finder", data=data)

        return self.async_show_form(
            step_id="location_dynamic",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_LOCATION_SOURCE): EntitySelector(
                        EntitySelectorConfig(
                            domain=["person", "device_tracker"],
                        )
                    ),
                    vol.Required(CONF_RADIUS, default=DEFAULT_RADIUS): vol.All(
                        vol.Coerce(float), vol.Range(min=MIN_RADIUS, max=MAX_RADIUS)
                    ),
                    vol.Required(CONF_UPDATE_INTERVAL, default=DEFAULT_UPDATE_INTERVAL): vol.All(
                        vol.Coerce(int),
                        vol.Range(min=MIN_UPDATE_INTERVAL, max=MAX_UPDATE_INTERVAL),
                    ),
                    vol.Optional(CONF_FUEL_TYPES, default=FUEL_TYPES): cv.multi_select(
                        {ft: ft.replace("_", " ").title() for ft in FUEL_TYPES}
                    ),
                }
            ),
            errors=errors,
        )

    # ──────────────────────────────────────────────
    # Reauthentication
    # ──────────────────────────────────────────────

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

                entry = self.hass.config_entries.async_get_entry(self.context["entry_id"])

                client = FuelFinderClient(
                    client_id=user_input[CONF_CLIENT_ID],
                    client_secret=user_input[CONF_CLIENT_SECRET],
                    environment=entry.data[CONF_ENVIRONMENT],
                )

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

    # ──────────────────────────────────────────────
    # Reconfigure: Step 1 - Choose location mode
    # ──────────────────────────────────────────────

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Handle reconfiguration step 1: choose location mode."""
        entry = self.hass.config_entries.async_get_entry(self.context["entry_id"])
        current_source = entry.data.get(CONF_LOCATION_SOURCE, LOCATION_SOURCE_STATIC)
        current_mode = (
            LOCATION_MODE_STATIC
            if current_source == LOCATION_SOURCE_STATIC
            else LOCATION_MODE_DYNAMIC
        )

        if user_input is not None:
            self._user_data = user_input
            location_mode = user_input.get(CONF_LOCATION_MODE, LOCATION_MODE_STATIC)

            if location_mode == LOCATION_MODE_DYNAMIC:
                return await self.async_step_reconfigure_dynamic()
            return await self.async_step_reconfigure_static()

        return self.async_show_form(
            step_id="reconfigure",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_LOCATION_MODE, default=current_mode): SelectSelector(
                        SelectSelectorConfig(
                            options=[
                                {
                                    "label": "Static (manual coordinates)",
                                    "value": LOCATION_MODE_STATIC,
                                },
                                {
                                    "label": "Dynamic (follow a person or device)",
                                    "value": LOCATION_MODE_DYNAMIC,
                                },
                            ],
                            mode=SelectSelectorMode.DROPDOWN,
                        )
                    ),
                }
            ),
        )

    # ──────────────────────────────────────────────
    # Reconfigure: Step 2a - Static location
    # ──────────────────────────────────────────────

    async def async_step_reconfigure_static(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Handle reconfigure step 2: static location."""
        errors = {}
        entry = self.hass.config_entries.async_get_entry(self.context["entry_id"])

        if user_input is not None:
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
                        CONF_LOCATION_SOURCE: LOCATION_SOURCE_STATIC,
                    },
                )

        return self.async_show_form(
            step_id="reconfigure_static",
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
                        default=entry.data.get(CONF_FUEL_TYPES, FUEL_TYPES),
                    ): cv.multi_select({ft: ft.replace("_", " ").title() for ft in FUEL_TYPES}),
                }
            ),
            errors=errors,
        )

    # ──────────────────────────────────────────────
    # Reconfigure: Step 2b - Dynamic location
    # ──────────────────────────────────────────────

    async def async_step_reconfigure_dynamic(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Handle reconfigure step 2: dynamic location."""
        errors = {}
        entry = self.hass.config_entries.async_get_entry(self.context["entry_id"])

        if user_input is not None:
            if not user_input.get(CONF_FUEL_TYPES):
                errors["base"] = "no_fuel_types"
            else:
                entity_id = user_input.get(CONF_LOCATION_SOURCE)
                if not entity_id or self.hass.states.get(entity_id) is None:
                    errors["base"] = "entity_not_found"

                if not errors:
                    return self.async_update_reload_and_abort(
                        entry,
                        data_updates={
                            CONF_LATITUDE: self.hass.config.latitude,
                            CONF_LONGITUDE: self.hass.config.longitude,
                            CONF_RADIUS: user_input[CONF_RADIUS],
                            CONF_UPDATE_INTERVAL: user_input[CONF_UPDATE_INTERVAL],
                            CONF_FUEL_TYPES: user_input[CONF_FUEL_TYPES],
                            CONF_LOCATION_SOURCE: user_input[CONF_LOCATION_SOURCE],
                        },
                    )

        # Default entity to current if already dynamic
        current_source = entry.data.get(CONF_LOCATION_SOURCE, LOCATION_SOURCE_STATIC)
        default_entity = (
            current_source if current_source != LOCATION_SOURCE_STATIC else vol.UNDEFINED
        )

        schema: dict[Any, Any] = {
            vol.Required(CONF_LOCATION_SOURCE, default=default_entity): EntitySelector(
                EntitySelectorConfig(
                    domain=["person", "device_tracker"],
                )
            ),
            vol.Required(CONF_RADIUS, default=entry.data[CONF_RADIUS]): vol.All(
                vol.Coerce(float), vol.Range(min=MIN_RADIUS, max=MAX_RADIUS)
            ),
            vol.Required(CONF_UPDATE_INTERVAL, default=entry.data[CONF_UPDATE_INTERVAL]): vol.All(
                vol.Coerce(int),
                vol.Range(min=MIN_UPDATE_INTERVAL, max=MAX_UPDATE_INTERVAL),
            ),
            vol.Optional(
                CONF_FUEL_TYPES,
                default=entry.data.get(CONF_FUEL_TYPES, FUEL_TYPES),
            ): cv.multi_select({ft: ft.replace("_", " ").title() for ft in FUEL_TYPES}),
        }

        return self.async_show_form(
            step_id="reconfigure_dynamic",
            data_schema=vol.Schema(schema),
            errors=errors,
        )
