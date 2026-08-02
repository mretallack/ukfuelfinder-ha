"""Location management for UK Fuel Finder integration."""

from __future__ import annotations

import logging
import time
from collections.abc import Callable, Coroutine
from typing import Any

from homeassistant.const import (
    ATTR_LATITUDE,
    ATTR_LONGITUDE,
    STATE_UNAVAILABLE,
    STATE_UNKNOWN,
)
from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.helpers.event import async_track_state_change_event

from .const import LOCATION_SOURCE_STATIC

_LOGGER = logging.getLogger(__name__)

DEBOUNCE_SECONDS = 30


class LocationManager:
    """Manages dynamic or static location for the integration."""

    def __init__(
        self,
        hass: HomeAssistant,
        location_source: str,
        fallback_latitude: float,
        fallback_longitude: float,
        on_location_changed: Callable[[], Coroutine[Any, Any, None]],
    ) -> None:
        """Initialize the location manager.

        Args:
            hass: Home Assistant instance.
            location_source: Entity ID to track, or "static" for fixed coordinates.
            fallback_latitude: Fallback latitude (HA home or user-configured).
            fallback_longitude: Fallback longitude (HA home or user-configured).
            on_location_changed: Async callback to invoke when location changes.
        """
        self._hass = hass
        self._location_source = location_source
        self._fallback_latitude = fallback_latitude
        self._fallback_longitude = fallback_longitude
        self._on_location_changed = on_location_changed
        self._unsub_state_change: Callable[[], None] | None = None
        self._last_recalc_time: float = 0.0
        self._pending_timer: Callable[[], None] | None = None

    @property
    def is_dynamic(self) -> bool:
        """Whether using dynamic location tracking."""
        return self._location_source != LOCATION_SOURCE_STATIC

    @property
    def source_entity_id(self) -> str | None:
        """The entity being tracked, or None if static."""
        if self.is_dynamic:
            return self._location_source
        return None

    @property
    def latitude(self) -> float:
        """Current latitude (from tracked entity or fallback)."""
        if not self.is_dynamic:
            return self._fallback_latitude

        state = self._hass.states.get(self._location_source)
        if state is None or state.state in (STATE_UNAVAILABLE, STATE_UNKNOWN):
            return self._fallback_latitude

        lat = state.attributes.get(ATTR_LATITUDE)
        if lat is None:
            return self._fallback_latitude

        return float(lat)

    @property
    def longitude(self) -> float:
        """Current longitude (from tracked entity or fallback)."""
        if not self.is_dynamic:
            return self._fallback_longitude

        state = self._hass.states.get(self._location_source)
        if state is None or state.state in (STATE_UNAVAILABLE, STATE_UNKNOWN):
            return self._fallback_longitude

        lon = state.attributes.get(ATTR_LONGITUDE)
        if lon is None:
            return self._fallback_longitude

        return float(lon)

    @property
    def using_fallback(self) -> bool:
        """Whether currently using fallback coordinates."""
        if not self.is_dynamic:
            return False

        state = self._hass.states.get(self._location_source)
        if state is None or state.state in (STATE_UNAVAILABLE, STATE_UNKNOWN):
            return True

        return (
            state.attributes.get(ATTR_LATITUDE) is None
            or state.attributes.get(ATTR_LONGITUDE) is None
        )

    async def async_start(self) -> None:
        """Start listening for entity state changes."""
        if not self.is_dynamic:
            return  # No-op for static mode

        self._unsub_state_change = async_track_state_change_event(
            self._hass, [self._location_source], self._handle_state_change
        )

        # Log initial state
        if self.using_fallback:
            _LOGGER.warning(
                "Location source '%s' has no GPS fix. Using fallback coordinates "
                "(HA home: %s, %s)",
                self._location_source,
                self._fallback_latitude,
                self._fallback_longitude,
            )

    async def async_stop(self) -> None:
        """Stop listening and clean up."""
        if not self.is_dynamic:
            return  # Nothing to clean up

        if self._unsub_state_change:
            self._unsub_state_change()
            self._unsub_state_change = None

        if self._pending_timer:
            self._pending_timer()
            self._pending_timer = None

    @callback
    def _handle_state_change(self, event: Event) -> None:
        """Handle tracked entity state change with debounce."""
        new_state = event.data.get("new_state")
        if new_state is None:
            return

        # Check if new state has location data
        new_lat = new_state.attributes.get(ATTR_LATITUDE)
        new_lon = new_state.attributes.get(ATTR_LONGITUDE)

        if new_lat is None or new_lon is None:
            # Entity lost GPS — will use fallback on next coord read
            _LOGGER.warning(
                "Location source '%s' lost GPS fix. Using fallback coordinates",
                self._location_source,
            )

        # Debounce: only trigger callback if enough time has passed
        now = time.monotonic()
        elapsed = now - self._last_recalc_time

        if elapsed >= DEBOUNCE_SECONDS:
            self._last_recalc_time = now
            self._cancel_pending_timer()
            self._hass.async_create_task(self._on_location_changed())
        else:
            # Schedule a delayed callback for the remaining time
            remaining = DEBOUNCE_SECONDS - elapsed
            self._schedule_delayed_callback(remaining)

    def _schedule_delayed_callback(self, delay: float) -> None:
        """Schedule a delayed callback, cancelling any existing one."""
        self._cancel_pending_timer()

        @callback
        def _fire_callback(_now: Any) -> None:
            """Fire the location changed callback."""
            self._pending_timer = None
            self._last_recalc_time = time.monotonic()
            self._hass.async_create_task(self._on_location_changed())

        self._pending_timer = self._hass.helpers.event.async_call_later(delay, _fire_callback)

    def _cancel_pending_timer(self) -> None:
        """Cancel any pending delayed callback."""
        if self._pending_timer:
            self._pending_timer()
            self._pending_timer = None
