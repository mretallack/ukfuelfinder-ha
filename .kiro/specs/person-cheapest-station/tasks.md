# Tasks: Dynamic Location Tracking

## CI Pipeline Reference

The GitHub Actions workflow (`.github/workflows/validate.yml`) runs on push to `main`/`dev` and all PRs:

| Job | What it checks | Local equivalent |
|-----|---------------|-----------------|
| **validate** | Code formatting | `black --check custom_components tests` |
| | Import order | `isort --check-only custom_components tests` |
| | Unit tests | `PYTHONPATH=. pytest tests/ -v --ignore=tests/test_api_integration.py -k "not integration"` |
| **validate-hacs** | HACS structure | Manual: check `manifest.json`, `hacs.json` if present |
| **validate-hassfest** | HA manifest | Manual: sorted keys in `manifest.json`, valid `strings.json` |

**Quick local CI check (run before every commit+push):**
```bash
source venv/bin/activate
black custom_components tests
isort custom_components tests
black --check custom_components tests
isort --check-only custom_components tests
PYTHONPATH=. pytest tests/ -v --ignore=tests/test_api_integration.py -k "not integration"
```

---

## Phase 1: Core Infrastructure

### Task 1.1: Add constants
- [x] Add `CONF_LOCATION_SOURCE = "location_source"` to `const.py`
- [x] Add `LOCATION_SOURCE_STATIC = "static"` to `const.py`

**File:** `custom_components/ukfuelfinder/const.py`  
**Expected outcome:** New constants available for use across the integration.

---

### Task 1.2: Create LocationManager class
- [x] Create new file `custom_components/ukfuelfinder/location.py`
- [x] Implement `LocationManager` class with:
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
- [x] Create `tests/test_location.py`
- [x] Test: static mode returns fallback coords
- [x] Test: static mode `async_start()` is no-op
- [x] Test: dynamic mode returns entity coords when available
- [x] Test: dynamic mode falls back when entity has no lat/lon
- [x] Test: dynamic mode falls back when entity is unavailable
- [x] Test: debounce prevents rapid callbacks (< 30s apart)
- [x] Test: debounce allows callback after 30s
- [x] Test: delayed callback fires with latest position after debounce window
- [x] Test: works with `person.*` entity
- [x] Test: works with `device_tracker.*` entity
- [x] Test: `async_stop()` removes listener

**File:** `tests/test_location.py`  
**Expected outcome:** All LocationManager tests pass.

---

## Phase 2: Coordinator Integration

### Task 2.1: Add LocationManager to coordinator
- [x] Add `setup_location_manager(location_source, fallback_lat, fallback_lon)` method to `UKFuelFinderCoordinator`
- [x] Store `self.location_manager` instance
- [x] Add `_on_location_changed()` async method that calls `self.async_request_refresh()`
- [x] Change `_async_update_data` to use `self.location_manager.latitude` / `self.location_manager.longitude` instead of `self.entry_data[CONF_LATITUDE]` / `self.entry_data[CONF_LONGITUDE]`

**File:** `custom_components/ukfuelfinder/coordinator.py`  
**Expected outcome:** Coordinator uses LocationManager for coordinates. Static mode behaviour identical to before.

---

### Task 2.2: Update integration setup/teardown
- [x] In `async_setup_entry`: read `CONF_LOCATION_SOURCE` from entry data (default to static)
- [x] Call `coordinator.setup_location_manager(...)` before first refresh
- [x] Call `coordinator.location_manager.async_start()` after first refresh
- [x] In `async_unload_entry`: call `coordinator.location_manager.async_stop()` before unloading

**File:** `custom_components/ukfuelfinder/__init__.py`  
**Expected outcome:** LocationManager lifecycle properly managed. Existing tests still pass.

---

### Task 2.3: Write coordinator integration tests
- [x] Test: coordinator uses LocationManager coords in `_async_update_data`
- [x] Test: `_on_location_changed` triggers `async_request_refresh`
- [x] Test: existing config (no `CONF_LOCATION_SOURCE`) defaults to static — identical behaviour
- [x] Test: setup and unload work with dynamic location source

**File:** `tests/test_coordinator.py` (extend existing)  
**Expected outcome:** Coordinator tests pass including new dynamic location scenarios.

---

## Phase 3: Config Flow

### Task 3.1: Update initial setup flow
- [x] Add `CONF_LOCATION_SOURCE` field to the user step schema
- [x] Build options list: "Static" + person entities + device_tracker entities
- [x] When dynamic selected: hide lat/lon fields, auto-store `hass.config.latitude/longitude`
- [x] When static selected: show lat/lon fields as before
- [x] Validate: if dynamic, check entity exists in HA

**File:** `custom_components/ukfuelfinder/config_flow.py`  
**Expected outcome:** Setup flow shows location source selector. Dynamic mode hides lat/lon.

---

### Task 3.2: Update reconfigure flow
- [x] Add `CONF_LOCATION_SOURCE` field to reconfigure step schema
- [x] Pre-populate with current value from `entry.data` (default: static)
- [x] Same dynamic/static logic as initial setup
- [x] Store updated `CONF_LOCATION_SOURCE` in `data_updates`

**File:** `custom_components/ukfuelfinder/config_flow.py`  
**Expected outcome:** Users can switch between static and dynamic in reconfigure.

---

### Task 3.3: Update UI strings
- [x] Add `location_source` field label and description to `strings.json`
- [x] Add "Static (manual coordinates)" option text
- [x] Copy to `translations/en.json`

**Files:** `custom_components/ukfuelfinder/strings.json`, `custom_components/ukfuelfinder/translations/en.json`  
**Expected outcome:** Config flow displays proper labels for the new field.

---

### Task 3.4: Write config flow tests
- [x] Test: user flow shows location source options
- [x] Test: selecting static shows lat/lon fields
- [x] Test: selecting dynamic entity hides lat/lon, stores HA home as fallback
- [x] Test: selecting non-existent entity shows error
- [x] Test: reconfigure allows switching static → dynamic
- [x] Test: reconfigure allows switching dynamic → static
- [x] Test: backward compat — old entry with no `CONF_LOCATION_SOURCE` reconfigures fine

**File:** `tests/test_config_flow.py` (extend existing)  
**Expected outcome:** All config flow tests pass.

---

## Phase 4: Sensor Updates

### Task 4.1: Add diagnostic attributes to cheapest sensors
- [x] In `UKFuelFinderCheapestSensor.extra_state_attributes`:
  - If `coordinator.location_manager.is_dynamic`: add `location_source`, `search_latitude`, `search_longitude`
- [x] These attributes are only added, never replace existing ones

**File:** `custom_components/ukfuelfinder/sensor.py`  
**Expected outcome:** Cheapest sensors show location source info when in dynamic mode.

---

### Task 4.2: Write sensor tests for new attributes
- [x] Test: cheapest sensor in static mode has no `location_source` attribute
- [x] Test: cheapest sensor in dynamic mode includes `location_source`, `search_latitude`, `search_longitude`
- [x] Test: existing sensor attributes unchanged in both modes

**File:** `tests/test_sensor.py` (extend existing)  
**Expected outcome:** Sensor tests pass, backward compatibility verified.

---

## Phase 5: Regression & Polish

### Task 5.1: Run full CI checks locally
- [x] Run `black --check custom_components tests` — verify formatting
- [x] Run `isort --check-only custom_components tests` — verify import order
- [x] Run `PYTHONPATH=. pytest tests/ -v --ignore=tests/test_api_integration.py -k "not integration"` — all tests pass
- [x] Verify `manifest.json` is valid JSON with sorted keys
- [x] Verify `strings.json` and `translations/en.json` match structure
- [x] Confirm all existing 30 tests still pass unchanged (backward compat proof)

**CI workflow runs (`.github/workflows/validate.yml`):**
1. `black --check custom_components tests`
2. `isort --check-only custom_components tests`
3. `PYTHONPATH=. pytest tests/ -v --ignore=tests/test_api_integration.py -k "not integration"`
4. HACS validation (structure/manifest — can't run locally, but check manifest manually)
5. hassfest validation (manifest/structure — can't run locally, but check manifest manually)

**Expected outcome:** All CI checks pass locally. Zero regressions.

**Note:** hassfest requires key order: `domain` first, `name` second, then remaining keys alphabetically.

---

### Task 5.2: End-to-end integration test
- [x] Write test: person entity moves → coordinator refreshes → station list changes → cheapest sensor updates
- [x] Write test: person goes unavailable → fallback to HA home → stations revert to home area
- [x] Write test: rapid location changes → debounce limits refreshes
- [x] Write test: setup with dynamic source, unload, verify no dangling listeners

**File:** `tests/test_dynamic_location.py` (new)  
**Expected outcome:** Full dynamic location flow verified end-to-end.

---

### Task 5.3: Strengthen existing config flow tests
- [x] Test: reconfigure flow (currently untested)
- [x] Test: reauth flow with dynamic location entry
- [x] Test: connection validation failure shows error
- [x] Test: no fuel types selected shows error

**File:** `tests/test_config_flow.py` (extend)  
**Expected outcome:** Config flow coverage increased from 2 tests to 10.

---

### Task 5.4: Update documentation
- [x] Update README.md with dynamic location feature description
- [x] Add configuration instructions for dynamic mode
- [x] Add troubleshooting section for dynamic location issues

**File:** `README.md`  
**Expected outcome:** Users can discover and configure the feature from documentation.

---

### Task 5.5: Final pre-push verification
- [x] Run `black custom_components tests` — format
- [x] Run `isort custom_components tests` — sort imports
- [x] Run `black --check custom_components tests` — verify clean
- [x] Run `isort --check-only custom_components tests` — verify clean
- [x] Run `PYTHONPATH=. pytest tests/ -v --ignore=tests/test_api_integration.py -k "not integration"` — ALL pass
- [x] Check `manifest.json` keys are sorted (domain, name, then alphabetical)
- [x] Check `strings.json` has entries for all new config fields
- [x] Check `translations/en.json` matches `strings.json` structure

**Expected outcome:** Code formatted, all tests green, manifest/strings valid, ready for PR.
