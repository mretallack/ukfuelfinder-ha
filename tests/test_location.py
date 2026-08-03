"""Test LocationManager for UK Fuel Finder."""

import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.const import (
    ATTR_LATITUDE,
    ATTR_LONGITUDE,
    STATE_HOME,
    STATE_NOT_HOME,
    STATE_UNAVAILABLE,
    STATE_UNKNOWN,
)
from homeassistant.core import Event, State

from custom_components.ukfuelfinder.const import LOCATION_SOURCE_STATIC
from custom_components.ukfuelfinder.location import DEBOUNCE_SECONDS, LocationManager


@pytest.fixture
def mock_hass():
    """Create a mock Home Assistant instance."""
    hass = MagicMock()
    hass.states = MagicMock()
    hass.helpers = MagicMock()
    hass.async_create_task = MagicMock()
    return hass


@pytest.fixture
def on_location_changed():
    """Create a mock callback."""
    return AsyncMock()


# --- Static mode tests ---


async def test_static_mode_returns_fallback_coords(mock_hass, on_location_changed):
    """Test static mode returns fallback coordinates."""
    mgr = LocationManager(
        hass=mock_hass,
        location_source=LOCATION_SOURCE_STATIC,
        fallback_latitude=51.5,
        fallback_longitude=-0.1,
        on_location_changed=on_location_changed,
    )

    assert mgr.latitude == 51.5
    assert mgr.longitude == -0.1
    assert mgr.is_dynamic is False
    assert mgr.source_entity_id is None
    assert mgr.using_fallback is False


async def test_static_mode_start_is_noop(mock_hass, on_location_changed):
    """Test async_start is a no-op in static mode."""
    mgr = LocationManager(
        hass=mock_hass,
        location_source=LOCATION_SOURCE_STATIC,
        fallback_latitude=51.5,
        fallback_longitude=-0.1,
        on_location_changed=on_location_changed,
    )

    await mgr.async_start()
    # No state change listener should be registered
    assert mgr._unsub_state_change is None


async def test_static_mode_stop_is_noop(mock_hass, on_location_changed):
    """Test async_stop is a no-op in static mode."""
    mgr = LocationManager(
        hass=mock_hass,
        location_source=LOCATION_SOURCE_STATIC,
        fallback_latitude=51.5,
        fallback_longitude=-0.1,
        on_location_changed=on_location_changed,
    )

    await mgr.async_stop()
    # Should not raise any errors


# --- Dynamic mode tests ---


async def test_dynamic_mode_returns_entity_coords(mock_hass, on_location_changed):
    """Test dynamic mode returns entity coordinates when available."""
    mock_state = MagicMock(spec=State)
    mock_state.state = STATE_HOME
    mock_state.attributes = {ATTR_LATITUDE: 52.0, ATTR_LONGITUDE: -1.5}
    mock_hass.states.get.return_value = mock_state

    mgr = LocationManager(
        hass=mock_hass,
        location_source="person.mark",
        fallback_latitude=51.5,
        fallback_longitude=-0.1,
        on_location_changed=on_location_changed,
    )

    assert mgr.latitude == 52.0
    assert mgr.longitude == -1.5
    assert mgr.is_dynamic is True
    assert mgr.source_entity_id == "person.mark"
    assert mgr.using_fallback is False


async def test_dynamic_mode_fallback_when_no_lat_lon(mock_hass, on_location_changed):
    """Test dynamic mode falls back when entity has no lat/lon attributes."""
    mock_state = MagicMock(spec=State)
    mock_state.state = STATE_HOME
    mock_state.attributes = {}  # No lat/lon
    mock_hass.states.get.return_value = mock_state

    mgr = LocationManager(
        hass=mock_hass,
        location_source="person.mark",
        fallback_latitude=51.5,
        fallback_longitude=-0.1,
        on_location_changed=on_location_changed,
    )

    assert mgr.latitude == 51.5
    assert mgr.longitude == -0.1
    assert mgr.using_fallback is True


async def test_dynamic_mode_fallback_when_entity_unavailable(mock_hass, on_location_changed):
    """Test dynamic mode falls back when entity is unavailable."""
    mock_state = MagicMock(spec=State)
    mock_state.state = STATE_UNAVAILABLE
    mock_state.attributes = {ATTR_LATITUDE: 52.0, ATTR_LONGITUDE: -1.5}
    mock_hass.states.get.return_value = mock_state

    mgr = LocationManager(
        hass=mock_hass,
        location_source="person.mark",
        fallback_latitude=51.5,
        fallback_longitude=-0.1,
        on_location_changed=on_location_changed,
    )

    assert mgr.latitude == 51.5
    assert mgr.longitude == -0.1
    assert mgr.using_fallback is True


async def test_dynamic_mode_fallback_when_entity_unknown(mock_hass, on_location_changed):
    """Test dynamic mode falls back when entity state is unknown."""
    mock_state = MagicMock(spec=State)
    mock_state.state = STATE_UNKNOWN
    mock_state.attributes = {}
    mock_hass.states.get.return_value = mock_state

    mgr = LocationManager(
        hass=mock_hass,
        location_source="device_tracker.phone",
        fallback_latitude=51.5,
        fallback_longitude=-0.1,
        on_location_changed=on_location_changed,
    )

    assert mgr.latitude == 51.5
    assert mgr.longitude == -0.1
    assert mgr.using_fallback is True


async def test_dynamic_mode_fallback_when_entity_not_found(mock_hass, on_location_changed):
    """Test dynamic mode falls back when entity doesn't exist."""
    mock_hass.states.get.return_value = None

    mgr = LocationManager(
        hass=mock_hass,
        location_source="person.nonexistent",
        fallback_latitude=51.5,
        fallback_longitude=-0.1,
        on_location_changed=on_location_changed,
    )

    assert mgr.latitude == 51.5
    assert mgr.longitude == -0.1
    assert mgr.using_fallback is True


async def test_dynamic_mode_start_registers_listener(mock_hass, on_location_changed):
    """Test async_start registers a state change listener."""
    mock_hass.states.get.return_value = None  # No GPS initially

    mgr = LocationManager(
        hass=mock_hass,
        location_source="person.mark",
        fallback_latitude=51.5,
        fallback_longitude=-0.1,
        on_location_changed=on_location_changed,
    )

    with patch(
        "custom_components.ukfuelfinder.location.async_track_state_change_event"
    ) as mock_track:
        mock_track.return_value = MagicMock()
        await mgr.async_start()
        mock_track.assert_called_once_with(mock_hass, ["person.mark"], mgr._handle_state_change)
        assert mgr._unsub_state_change is not None


async def test_dynamic_mode_stop_removes_listener(mock_hass, on_location_changed):
    """Test async_stop removes the state change listener."""
    mgr = LocationManager(
        hass=mock_hass,
        location_source="person.mark",
        fallback_latitude=51.5,
        fallback_longitude=-0.1,
        on_location_changed=on_location_changed,
    )

    unsub_mock = MagicMock()
    mgr._unsub_state_change = unsub_mock

    await mgr.async_stop()
    unsub_mock.assert_called_once()
    assert mgr._unsub_state_change is None


# --- Debounce tests ---


async def test_debounce_allows_first_callback(mock_hass, on_location_changed):
    """Test first location change triggers callback immediately."""
    mgr = LocationManager(
        hass=mock_hass,
        location_source="person.mark",
        fallback_latitude=51.5,
        fallback_longitude=-0.1,
        on_location_changed=on_location_changed,
    )
    mgr._last_recalc_time = 0.0  # Long ago

    # Create a state change event
    new_state = MagicMock(spec=State)
    new_state.attributes = {ATTR_LATITUDE: 52.0, ATTR_LONGITUDE: -1.5}
    event = MagicMock(spec=Event)
    event.data = {"new_state": new_state}

    mgr._handle_state_change(event)

    # Callback should be scheduled via async_create_task
    mock_hass.async_create_task.assert_called_once()


async def test_debounce_prevents_rapid_callbacks(mock_hass, on_location_changed):
    """Test rapid location changes are debounced."""
    mgr = LocationManager(
        hass=mock_hass,
        location_source="person.mark",
        fallback_latitude=51.5,
        fallback_longitude=-0.1,
        on_location_changed=on_location_changed,
    )
    # Set last recalc to "just now"
    mgr._last_recalc_time = time.monotonic()

    new_state = MagicMock(spec=State)
    new_state.attributes = {ATTR_LATITUDE: 52.0, ATTR_LONGITUDE: -1.5}
    event = MagicMock(spec=Event)
    event.data = {"new_state": new_state}

    mgr._handle_state_change(event)

    # Should NOT trigger immediate callback
    mock_hass.async_create_task.assert_not_called()
    # Should schedule a delayed callback
    mock_hass.helpers.event.async_call_later.assert_called_once()


async def test_debounce_allows_callback_after_interval(mock_hass, on_location_changed):
    """Test callback is allowed after debounce interval passes."""
    mgr = LocationManager(
        hass=mock_hass,
        location_source="person.mark",
        fallback_latitude=51.5,
        fallback_longitude=-0.1,
        on_location_changed=on_location_changed,
    )
    # Set last recalc to more than DEBOUNCE_SECONDS ago
    mgr._last_recalc_time = time.monotonic() - (DEBOUNCE_SECONDS + 1)

    new_state = MagicMock(spec=State)
    new_state.attributes = {ATTR_LATITUDE: 52.0, ATTR_LONGITUDE: -1.5}
    event = MagicMock(spec=Event)
    event.data = {"new_state": new_state}

    mgr._handle_state_change(event)

    # Should trigger immediate callback
    mock_hass.async_create_task.assert_called_once()


async def test_debounce_no_event_on_none_new_state(mock_hass, on_location_changed):
    """Test no callback when event has no new_state."""
    mgr = LocationManager(
        hass=mock_hass,
        location_source="person.mark",
        fallback_latitude=51.5,
        fallback_longitude=-0.1,
        on_location_changed=on_location_changed,
    )

    event = MagicMock(spec=Event)
    event.data = {"new_state": None}

    mgr._handle_state_change(event)

    mock_hass.async_create_task.assert_not_called()
    mock_hass.helpers.event.async_call_later.assert_not_called()


# --- Works with different entity types ---


async def test_works_with_person_entity(mock_hass, on_location_changed):
    """Test LocationManager works with person entities."""
    mock_state = MagicMock(spec=State)
    mock_state.state = STATE_HOME
    mock_state.attributes = {ATTR_LATITUDE: 51.5, ATTR_LONGITUDE: -0.1}
    mock_hass.states.get.return_value = mock_state

    mgr = LocationManager(
        hass=mock_hass,
        location_source="person.john",
        fallback_latitude=50.0,
        fallback_longitude=0.0,
        on_location_changed=on_location_changed,
    )

    assert mgr.latitude == 51.5
    assert mgr.longitude == -0.1
    assert mgr.source_entity_id == "person.john"


async def test_works_with_device_tracker_entity(mock_hass, on_location_changed):
    """Test LocationManager works with device_tracker entities."""
    mock_state = MagicMock(spec=State)
    mock_state.state = STATE_NOT_HOME
    mock_state.attributes = {ATTR_LATITUDE: 53.0, ATTR_LONGITUDE: -2.0}
    mock_hass.states.get.return_value = mock_state

    mgr = LocationManager(
        hass=mock_hass,
        location_source="device_tracker.phone_gps",
        fallback_latitude=50.0,
        fallback_longitude=0.0,
        on_location_changed=on_location_changed,
    )

    assert mgr.latitude == 53.0
    assert mgr.longitude == -2.0
    assert mgr.source_entity_id == "device_tracker.phone_gps"
