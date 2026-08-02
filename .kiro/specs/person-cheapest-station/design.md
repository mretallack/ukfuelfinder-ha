# Design: Dynamic Location Tracking

## Architecture Overview

The feature adds an optional dynamic location source to the existing integration. When configured, the coordinator uses a tracked entity's GPS position instead of static coordinates to filter nearby stations.

```
┌─────────────────────────────────────────────────────────────────┐
│                     Home Assistant Core                          │
│                                                                 │
│  ┌──────────────┐    state_changed     ┌─────────────────────┐ │
│  │ Person /     │ ──────────────────── │ UKFuelFinder        │ │
│  │ DeviceTracker│    (lat/lon)         │ Integration         │ │
│  └──────────────┘                      │                     │ │
│                                        │  ┌───────────────┐  │ │
│                                        │  │ LocationMgr   │  │ │
│                                        │  │ - get_coords  │  │ │
│                                        │  │ - debounce    │  │ │
│                                        │  │ - fallback    │  │ │
│                                        │  └───────┬───────┘  │ │
│                                        │          │           │ │
│                                        │  ┌───────▼───────┐  │ │
│                                        │  │ Coordinator   │  │ │
│                                        │  │ - _async_     │  │ │
│                                        │  │   update_data │  │ │
│                                        │  │ - re-filter   │  │ │
│                                        │  └───────┬───────┘  │ │
│                                        │          │           │ │
│                                        │  ┌───────▼───────┐  │ │
│                                        │  │ Sensors       │  │ │
│                                        │  │ - stations    │  │ │
│                                        │  │ - cheapest    │  │ │
│                                        │  └───────────────┘  │ │
│                                        └─────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                              │
                    ┌─────────▼──────────┐
                    │  ukfuelfinder lib  │
                    │  - get_all_pfs_info │ (cached 1hr)
                    │  - get_all_pfs_    │
                    │    prices          │ (cached 15min)
                    │  - _haversine      │
                    └────────────────────┘
```

## Component Design

### 1. Configuration Changes

#### New constants (`const.py`)

```python
CONF_LOCATION_SOURCE = "location_source"
LOCATION_SOURCE_STATIC = "static"
```

#### Config flow changes (`config_flow.py`)

Add a "Location source" selector to both the initial setup and reconfigure flows:

- **Options**: "Static (manual coordinates)" + all `person.*` and `device_tracker.*` entities
- **Default**: "Static" (backward compatible)
- **When dynamic is selected**: lat/lon fields become "Fallback latitude/longitude" (still required)
- **Storage**: `entry.data[CONF_LOCATION_SOURCE]` = entity_id or `"static"`

```python
# Build location source options
location_options = {LOCATION_SOURCE_STATIC: "Static (manual coordinates)"}
# Add person entities
for entity_id in hass.states.async_entity_ids("person"):
    state = hass.states.get(entity_id)
    name = state.attributes.get("friendly_name", entity_id)
    location_options[entity_id] = f"Track: {name}"
# Add device_tracker entities  
for entity_id in hass.states.async_entity_ids("device_tracker"):
    state = hass.states.get(entity_id)
    name = state.attributes.get("friendly_name", entity_id)
    location_options[entity_id] = f"Track: {name}"
```

### 2. Location Manager (new module: `location.py`)

Encapsulates all dynamic location logic in a single class:

```python
class LocationManager:
    """Manages dynamic or static location for the integration."""

    def __init__(
        self,
        hass: HomeAssistant,
        location_source: str,  # entity_id or "static"
        fallback_latitude: float,
        fallback_longitude: float,
        on_location_changed: Callable[[], Coroutine],
    ):
        ...

    @property
    def latitude(self) -> float:
        """Current latitude (from tracked entity or fallback)."""

    @property
    def longitude(self) -> float:
        """Current longitude (from tracked entity or fallback)."""

    @property
    def is_dynamic(self) -> bool:
        """Whether using dynamic location tracking."""

    @property
    def source_entity_id(self) -> str | None:
        """The entity being tracked, or None if static."""

    async def async_start(self) -> None:
        """Start listening for entity state changes."""

    async def async_stop(self) -> None:
        """Stop listening and clean up."""
```

**Debouncing logic:**
- Tracks `_last_recalc_time` 
- On state change, checks if 30 seconds have passed since last recalc
- If not, schedules a delayed callback (fire-once timer)
- This ensures at most one recalc per 30 seconds, but never misses the final position

**Fallback logic:**
- If tracked entity has no `latitude`/`longitude` attributes → use fallback
- If tracked entity state is `unavailable` or `unknown` → use fallback
- Log a warning when falling back

### 3. Coordinator Changes (`coordinator.py`)

#### Data structure change

Currently `_async_update_data` calls `search_by_location` with static coords. The change:

```python
# Before
nearby_stations = await self.hass.async_add_executor_job(
    self.client.search_by_location,
    self.entry_data[CONF_LATITUDE],
    self.entry_data[CONF_LONGITUDE],
    self.entry_data[CONF_RADIUS],
)

# After
nearby_stations = await self.hass.async_add_executor_job(
    self.client.search_by_location,
    self.location_manager.latitude,
    self.location_manager.longitude,
    self.entry_data[CONF_RADIUS],
)
```

#### Location change handling

When `LocationManager` fires `on_location_changed`:

```python
async def _on_location_changed(self) -> None:
    """Handle dynamic location change — re-filter stations."""
    # Request a coordinator refresh (re-runs _async_update_data)
    # Since library caches data, this won't make new API calls
    # It just re-filters with new coordinates
    await self.async_request_refresh()
```

This is elegant because:
- `async_request_refresh()` is the standard HA coordinator pattern
- The library's internal cache means `search_by_location` and `get_all_pfs_prices` return cached data
- Station sensors automatically update via the coordinator listener pattern
- The existing grace period logic handles stations appearing/disappearing

### 4. Integration Setup Changes (`__init__.py`)

```python
async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up UK Fuel Finder from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    # Create location manager
    location_source = entry.data.get(CONF_LOCATION_SOURCE, LOCATION_SOURCE_STATIC)
    
    coordinator = UKFuelFinderCoordinator(hass, entry.data)
    coordinator.config_entry = entry

    # Initialize location manager (coordinator method)
    coordinator.setup_location_manager(
        location_source=location_source,
        fallback_lat=entry.data[CONF_LATITUDE],
        fallback_lon=entry.data[CONF_LONGITUDE],
    )

    await coordinator.async_config_entry_first_refresh()
    
    # Start listening for location changes (after first refresh)
    await coordinator.location_manager.async_start()

    hass.data[DOMAIN][entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    coordinator = hass.data[DOMAIN].get(entry.entry_id)
    if coordinator and coordinator.location_manager:
        await coordinator.location_manager.async_stop()

    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok
```

### 5. Sensor Changes (`sensor.py`)

Minimal changes needed:

- **Station sensors**: No change — they already read from `coordinator.data["stations"]` which will be dynamically filtered
- **Cheapest sensors**: No change — `get_cheapest_fuel()` already operates on the filtered station set
- **New diagnostic attribute** (optional): Add `search_centre_latitude`, `search_centre_longitude`, `location_source` to cheapest sensor attributes

```python
# In UKFuelFinderCheapestSensor.extra_state_attributes
if self.coordinator.location_manager.is_dynamic:
    attrs["location_source"] = self.coordinator.location_manager.source_entity_id
    attrs["search_latitude"] = self.coordinator.location_manager.latitude
    attrs["search_longitude"] = self.coordinator.location_manager.longitude
```

## Sequence Diagrams

### Initial Setup (Dynamic Location)

```
User          ConfigFlow         __init__         Coordinator      LocationMgr
 │                │                  │                │                │
 │─ configure ───▶│                  │                │                │
 │  (entity_id)   │                  │                │                │
 │                │─ create_entry ──▶│                │                │
 │                │                  │─ create ──────▶│                │
 │                │                  │                │─ create ──────▶│
 │                │                  │                │                │
 │                │                  │─ first_refresh▶│                │
 │                │                  │                │─ get lat/lon ─▶│
 │                │                  │                │◀─ coords ──────│
 │                │                  │                │─ search_by_loc │
 │                │                  │                │  (uses cache)  │
 │                │                  │                │                │
 │                │                  │─ async_start ─────────────────▶│
 │                │                  │                │                │─ listen
 │                │                  │                │                │  state
```

### Location Change Flow

```
Person Entity    LocationMgr       Coordinator       Library         Sensors
     │                │                │                │               │
     │─ state_changed▶│                │                │               │
     │  (new lat/lon) │                │                │               │
     │                │─ debounce chk  │                │               │
     │                │  (30s passed?) │                │               │
     │                │                │                │               │
     │                │─ async_request_refresh ────────▶│               │
     │                │                │                │               │
     │                │                │─ search_by_loc▶│               │
     │                │                │  (new coords)  │               │
     │                │                │                │─ cache hit    │
     │                │                │                │  (no API call)│
     │                │                │◀─ filtered ────│               │
     │                │                │                │               │
     │                │                │─ update data ──────────────────▶
     │                │                │                │               │─ update
     │                │                │                │               │  states
```

### Fallback Flow

```
Person Entity    LocationMgr       Coordinator
     │                │                │
     │─ unavailable ─▶│                │
     │                │─ use fallback  │
     │                │  (static coords)│
     │                │─ log warning   │
     │                │─ async_request_refresh ▶│
     │                │                │─ search_by_location(fallback_lat, fallback_lon)
```

## Backward Compatibility

**Guarantee: Existing installations will continue to work identically after update with zero user action.**

### Config Entry Compatibility

- **No migration required**: The `VERSION` remains at `1` — no `async_migrate_entry` needed
- **Missing key handled gracefully**: All code that reads `CONF_LOCATION_SOURCE` uses `.get()` with a default:
  ```python
  location_source = entry.data.get(CONF_LOCATION_SOURCE, LOCATION_SOURCE_STATIC)
  ```
- **Existing `entry.data` unchanged**: Existing entries have `{client_id, client_secret, environment, latitude, longitude, radius, update_interval, fuel_types}` — all still used as before. The new `CONF_LOCATION_SOURCE` key simply won't exist in old entries.

### Coordinator Compatibility

- **LocationManager in static mode = identical behaviour**: When `location_source == "static"`, the LocationManager simply returns `fallback_latitude` and `fallback_longitude` — the same values currently passed directly. No state listener is registered, no debouncing runs.
- **`_async_update_data` logic unchanged**: The only difference is where lat/lon comes from (LocationManager property vs direct `entry_data` access). The filtering, station building, grace period, and price matching logic is untouched.

### Sensor Compatibility

- **Entity IDs unchanged**: Format remains `sensor.ukfuelfinder_{station_id}_{fuel_type}` and `sensor.ukfuelfinder_cheapest_{fuel_type}` — no location component in the ID
- **Sensor attributes unchanged**: All existing attributes remain in the same format. New attributes (e.g. `location_source`) are only *added*, never replace existing ones.
- **Device IDs unchanged**: Device identifiers remain `(DOMAIN, station_id)` and `(DOMAIN, "cheapest")`
- **State class, units, icons unchanged**: `measurement`, `GBP`, `mdi:gas-station` all preserved

### Config Flow Compatibility

- **Existing reconfigure flow still works**: The location source field defaults to "Static" so users who open reconfigure see their current behaviour pre-selected
- **Validation unchanged**: All existing validation (radius limits, update interval limits, fuel type checks) remains

### What existing users will see after update

| Aspect | Before | After |
|--------|--------|-------|
| Integration behaviour | Static location | Static location (identical) |
| Sensors | Same entities, same states | Same entities, same states |
| Config UI | No location source field | Location source field appears (defaulted to "Static") |
| API calls | Same schedule | Same schedule |
| Performance | Same | Same (no extra listeners in static mode) |

### Defensive coding patterns

```python
# Always default to static — never crash on missing key
CONF_LOCATION_SOURCE = "location_source"
LOCATION_SOURCE_STATIC = "static"

# In coordinator __init__
location_source = self.entry_data.get(CONF_LOCATION_SOURCE, LOCATION_SOURCE_STATIC)

# LocationManager does nothing in static mode
class LocationManager:
    async def async_start(self) -> None:
        if not self.is_dynamic:
            return  # No-op for static mode — no listeners registered

    async def async_stop(self) -> None:
        if not self.is_dynamic:
            return  # Nothing to clean up
```

## Error Handling

| Scenario | Behaviour |
|----------|-----------|
| Tracked entity doesn't exist | Log error, use fallback, show repair notification |
| Tracked entity has no lat/lon | Use fallback coords, log warning |
| Tracked entity goes unavailable | Use fallback coords, resume when available |
| Location changes rapidly (driving) | Debounce at 30s, only latest position used |
| Library cache miss during re-filter | Normal API call happens (within rate limits) |

## File Changes Summary

| File | Change Type | Description |
|------|-------------|-------------|
| `const.py` | Modified | Add `CONF_LOCATION_SOURCE`, `LOCATION_SOURCE_STATIC` |
| `config_flow.py` | Modified | Add location source selector to user/reconfigure steps |
| `location.py` | **New** | `LocationManager` class |
| `coordinator.py` | Modified | Use `LocationManager` for coordinates, add `_on_location_changed` |
| `__init__.py` | Modified | Setup/teardown `LocationManager` lifecycle |
| `sensor.py` | Modified | Add diagnostic attributes to cheapest sensors (optional) |
| `strings.json` | Modified | Add UI strings for location source |
| `translations/en.json` | Modified | Add English translations |

## Testing Strategy

1. **Unit tests for LocationManager:**
   - Returns fallback when no tracked entity
   - Returns entity coords when available
   - Debounce prevents rapid-fire callbacks
   - Fallback on entity unavailable/unknown
   - Works with person, device_tracker, and any entity with lat/lon

2. **Unit tests for Coordinator changes:**
   - Uses LocationManager coords in `_async_update_data`
   - Handles `_on_location_changed` callback
   - Existing grace period logic still works with dynamic stations

3. **Unit tests for Config Flow:**
   - Location source selector shows available entities
   - Static mode stores no entity_id
   - Dynamic mode stores entity_id
   - Reconfigure allows switching between static/dynamic

4. **Integration tests:**
   - Full flow: person moves → stations update → cheapest updates
   - Fallback: person unavailable → uses static coords
   - Grace period: drive away → old stations linger → eventually removed

5. **Backward compatibility tests:**
   - Existing config entry (no `CONF_LOCATION_SOURCE`) loads successfully
   - Static mode produces identical results to pre-feature behaviour
   - All existing unit tests pass without modification (regression check)
   - Entity IDs remain stable after upgrade

## Implementation Considerations

### Why `async_request_refresh()` instead of manual re-filtering?

Using the coordinator's built-in refresh mechanism:
- Automatically notifies all sensor entities of new data
- Respects the coordinator's error handling and retry logic  
- Triggers the existing `_check_new_stations` listener for dynamic entity creation
- Library cache ensures no redundant API calls
- Keeps the data flow simple and testable

### Why not a separate "per-person" coordinator?

The user request is "make location dynamic" — not "add per-person sensors alongside static ones". A single coordinator with a switchable location source is simpler, aligns with the request, and avoids duplicating the entire sensor/device structure. Users who want multiple locations can already use multiple integration instances.

### Grace period interaction with movement

When a user drives away from home:
1. First refresh at new location: old stations no longer in radius → `missing_stations` counter starts
2. If user returns within 2 refreshes: stations reappear, counter resets
3. If user stays away: after 2 cycles, old station devices removed
4. This naturally handles the "driving" scenario — you see a mix of old and new stations briefly, then only new ones

The existing grace period (2 update cycles, not 2 location changes) works well because:
- Update cycles are time-based (configured interval, e.g. 30 min)
- A typical drive might trigger several location updates but only 1-2 scheduled refreshes
- Stations "stick around" for a reasonable time during transitions
