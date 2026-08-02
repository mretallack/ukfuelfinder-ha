# Tasks: Dynamic Location Tracking

## Phase 1: Core Infrastructure

### Task 1.1: Add constants
- [ ] Add `CONF_LOCATION_SOURCE = "location_source"` to `const.py`
- [ ] Add `LOCATION_SOURCE_STATIC = "static"` to `const.py`

**File:** `custom_components/ukfuelfinder/const.py`  
**Expected outcome:** New constants available for use across the integration.

---

### Task 1.2: Create LocationManager class
- [ ] Create new file `custom_components/ukfuelfinder/location.py`
- [ ] Implement `LocationManager` class with:
  - `__init__(hass, location_source, fallback_latitude, fallback_longitude, on_location_changed)`
  - `latitude` property — returns tracked entity lat or fallback
  - `longitude` property — returns tracked entity lon or fallback
  - `is_dynamic` property — True if tracking an entity
  - `source_entity_id` property — the tracked entity_id or None
  - `async_start()` — registers state change listener (no-op if static)
  - `async_stop()` — removes listener (no-op if static)
  - Debounce logic: 30-second minimum between triggering `on_location_changed`
  - Fallback logic: use fallback coords when entity unavailable/unknown/no lat/lon
  - Warning log when falling back

**File:** `custom_components/ukfuelfinder/location.py`  
**Expected outcome:** Self-contained location management that works in both static and dynamic modes.

---

### Task 1.3: Write LocationManager unit tests
- [ ] Create `tests/test_location.py`
- [ ] Test: static mode returns fallback coords
- [ ] Test: static mode `async_start()` is no-op
- [ ] Test: dynamic mode returns entity coords when available
- [ ] Test: dynamic mode falls back when entity has no lat/lon
- [ ] Test: dynamic mode falls back when entity is unavailable
- [ ] Test: debounce prevents rapid callbacks (< 30s apart)
- [ ] Test: debounce allows callback after 30s
- [ ] Test: delayed callback fires with latest position after debounce window
- [ ] Test: works with `person.*` entity
- [ ] Test: works with `device_tracker.*` entity
- [ ] Test: `async_stop()` removes listener

**File:** `tests/test_location.py`  
**Expected outcome:** All LocationManager tests pass.

---

## Phase 2: Coordinator Integration

### Task 2.1: Add LocationManager to coordinator
- [ ] Add `setup_location_manager(location_source, fallback_lat, fallback_lon)` method to `UKFuelFinderCoordinator`
- [ ] Store `self.location_manager` instance
- [ ] Add `_on_location_changed()` async method that calls `self.async_request_refresh()`
- [ ] Change `_async_update_data` to use `self.location_manager.latitude` / `self.location_manager.longitude` instead of `self.entry_data[CONF_LATITUDE]` / `self.entry_data[CONF_LONGITUDE]`

**File:** `custom_components/ukfuelfinder/coordinator.py`  
**Expected outcome:** Coordinator uses LocationManager for coordinates. Static mode behaviour identical to before.

---

### Task 2.2: Update integration setup/teardown
- [ ] In `async_setup_entry`: read `CONF_LOCATION_SOURCE` from entry data (default to static)
- [ ] Call `coordinator.setup_location_manager(...)` before first refresh
- [ ] Call `coordinator.location_manager.async_start()` after first refresh
- [ ] In `async_unload_entry`: call `coordinator.location_manager.async_stop()` before unloading

**File:** `custom_components/ukfuelfinder/__init__.py`  
**Expected outcome:** LocationManager lifecycle properly managed. Existing tests still pass.

---

### Task 2.3: Write coordinator integration tests
- [ ] Test: coordinator uses LocationManager coords in `_async_update_data`
- [ ] Test: `_on_location_changed` triggers `async_request_refresh`
- [ ] Test: existing config (no `CONF_LOCATION_SOURCE`) defaults to static — identical behaviour
- [ ] Test: setup and unload work with dynamic location source

**File:** `tests/test_coordinator.py` (extend existing)  
**Expected outcome:** Coordinator tests pass including new dynamic location scenarios.

---

## Phase 3: Config Flow

### Task 3.1: Update initial setup flow
- [ ] Add `CONF_LOCATION_SOURCE` field to the user step schema
- [ ] Build options list: "Static" + person entities + device_tracker entities
- [ ] When dynamic selected: hide lat/lon fields, auto-store `hass.config.latitude/longitude`
- [ ] When static selected: show lat/lon fields as before
- [ ] Validate: if dynamic, check entity exists in HA

**File:** `custom_components/ukfuelfinder/config_flow.py`  
**Expected outcome:** Setup flow shows location source selector. Dynamic mode hides lat/lon.

---

### Task 3.2: Update reconfigure flow
- [ ] Add `CONF_LOCATION_SOURCE` field to reconfigure step schema
- [ ] Pre-populate with current value from `entry.data` (default: static)
- [ ] Same dynamic/static logic as initial setup
- [ ] Store updated `CONF_LOCATION_SOURCE` in `data_updates`

**File:** `custom_components/ukfuelfinder/config_flow.py`  
**Expected outcome:** Users can switch between static and dynamic in reconfigure.

---

### Task 3.3: Update UI strings
- [ ] Add `location_source` field label and description to `strings.json`
- [ ] Add "Static (manual coordinates)" option text
- [ ] Copy to `translations/en.json`

**Files:** `custom_components/ukfuelfinder/strings.json`, `custom_components/ukfuelfinder/translations/en.json`  
**Expected outcome:** Config flow displays proper labels for the new field.

---

### Task 3.4: Write config flow tests
- [ ] Test: user flow shows location source options
- [ ] Test: selecting static shows lat/lon fields
- [ ] Test: selecting dynamic entity hides lat/lon, stores HA home as fallback
- [ ] Test: selecting non-existent entity shows error
- [ ] Test: reconfigure allows switching static → dynamic
- [ ] Test: reconfigure allows switching dynamic → static
- [ ] Test: backward compat — old entry with no `CONF_LOCATION_SOURCE` reconfigures fine

**File:** `tests/test_config_flow.py` (extend existing)  
**Expected outcome:** All config flow tests pass.

---

## Phase 4: Sensor Updates

### Task 4.1: Add diagnostic attributes to cheapest sensors
- [ ] In `UKFuelFinderCheapestSensor.extra_state_attributes`:
  - If `coordinator.location_manager.is_dynamic`: add `location_source`, `search_latitude`, `search_longitude`
- [ ] These attributes are only added, never replace existing ones

**File:** `custom_components/ukfuelfinder/sensor.py`  
**Expected outcome:** Cheapest sensors show location source info when in dynamic mode.

---

### Task 4.2: Write sensor tests for new attributes
- [ ] Test: cheapest sensor in static mode has no `location_source` attribute
- [ ] Test: cheapest sensor in dynamic mode includes `location_source`, `search_latitude`, `search_longitude`
- [ ] Test: existing sensor attributes unchanged in both modes

**File:** `tests/test_sensor.py` (extend existing)  
**Expected outcome:** Sensor tests pass, backward compatibility verified.

---

## Phase 5: Regression & Polish

### Task 5.1: Run full existing test suite
- [ ] Run all existing tests without modification
- [ ] Verify 0 failures — confirms backward compatibility
- [ ] Fix any regressions

**Expected outcome:** All 30+ existing tests pass unchanged.

---

### Task 5.2: End-to-end integration test
- [ ] Write test: person entity moves → coordinator refreshes → station list changes → cheapest sensor updates
- [ ] Write test: person goes unavailable → fallback to HA home → stations revert to home area
- [ ] Write test: rapid location changes → debounce limits refreshes

**File:** `tests/test_dynamic_location.py` (new)  
**Expected outcome:** Full dynamic location flow verified end-to-end.

---

### Task 5.3: Update documentation
- [ ] Update README.md with dynamic location feature description
- [ ] Add configuration instructions for dynamic mode
- [ ] Add troubleshooting section for dynamic location issues

**File:** `README.md`  
**Expected outcome:** Users can discover and configure the feature from documentation.

---

### Task 5.4: Format, lint, and final check
- [ ] Run `black` and `isort` on all modified files
- [ ] Run full test suite
- [ ] Verify no regressions

**Expected outcome:** Code formatted, all tests green, ready for review.
