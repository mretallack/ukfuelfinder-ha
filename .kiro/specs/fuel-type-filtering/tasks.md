# Fuel Type Filtering and Cheapest Sensor - Implementation Tasks

## Phase 1: Constants and Data Structures

- [x] **Task 1.1: Add fuel type constants**
- [x] **Task 1.2: Document fuel type mapping**

## Phase 2: Configuration Flow Enhancement

- [x] **Task 2.1: Update config flow schema**
- [x] **Task 2.2: Add fuel type validation**
- [x] **Task 2.3: Implement reconfigure flow**
- [x] **Task 2.4: Update strings.json**
- [x] **Task 2.5: Test config flow**

## Phase 3: Coordinator Enhancement

- [x] **Task 3.1: Add metadata fields to coordinator data structure**
- [x] **Task 3.2: Add get_cheapest_fuel method**
- [x] **Task 3.3: Test coordinator data structure**
- [x] **Task 3.4: Test cheapest calculation**
- [ ] **Task 3.5: Add price timestamp storage**
  - Store `price_timestamps` dict alongside `prices` in coordinator data
  - Extract `price_last_updated` from each `FuelPrice` object
  - Handle None timestamps gracefully
  - Expected: Coordinator data includes price timestamps per fuel type

## Phase 4: Sensor Platform Enhancement

- [x] **Task 4.1: Update regular sensor attributes with metadata**
- [x] **Task 4.2: Update sensor creation logic**
- [x] **Task 4.3: Create UKFuelFinderCheapestSensor class**
- [x] **Task 4.4: Add cheapest sensor creation**
- [x] **Task 4.5: Test sensor filtering**
- [x] **Task 4.6: Test sensor attributes**
- [x] **Task 4.7: Test cheapest sensor properties**
- [ ] **Task 4.8: Add price_last_updated to regular sensor attributes**
  - Get timestamp from `station["price_timestamps"][fuel_type]`
  - Convert datetime to ISO 8601 format string
  - Handle None timestamps
  - Expected: Regular sensors show price_last_updated attribute
- [ ] **Task 4.9: Add price_last_updated to cheapest sensor attributes**
  - Include timestamp in get_cheapest_fuel() return value
  - Convert to ISO format in cheapest sensor attributes
  - Expected: Cheapest sensors show when price was last updated
- [ ] **Task 4.10: Test price timestamp attributes**
  - Test regular sensor includes timestamp
  - Test cheapest sensor includes timestamp
  - Test None timestamp handling
  - Expected: Timestamp tests passing

## Phase 5: Integration Testing

- [x] **Task 5.1: Test end-to-end flow** - Covered by existing integration tests
- [x] **Task 5.2: Test reconfiguration** - Tested via config flow validation
- [x] **Task 5.3: Test edge cases** - Covered by cheapest sensor tests

## Phase 6: Documentation

- [x] **Task 6.1: Update README**
- [x] **Task 6.2: Add configuration examples**
- [x] **Task 6.3: Update CHANGELOG**
- [ ] **Task 6.4: Document price_last_updated attribute**
  - Add to README sensor attributes section
  - Explain what the timestamp represents
  - Add example showing how to use in automations
  - Expected: Users understand price timestamp feature

## Phase 7: Quality Assurance

- [x] **Task 7.1: Run all tests** - 25 passed, 2 skipped
- [ ] **Task 7.2: Manual testing** - Requires real Home Assistant instance
- [x] **Task 7.3: Code review** - Code is clean and maintainable

## Dependencies

- Phase 2 depends on Phase 1 (constants)
- Phase 3 can be done in parallel with Phase 2
- Phase 4 depends on Phase 1 and Phase 3
- Phase 5 depends on Phase 2, 3, and 4
- Phase 6 can be done in parallel with Phase 5
- Phase 7 depends on all previous phases

## Estimated Effort

- Phase 1: 1 hour ✅
- Phase 2: 3 hours ✅
- Phase 3: 2 hours ✅ + 0.5 hours (price timestamps)
- Phase 4: 4 hours ✅ + 1 hour (price timestamp attributes + tests)
- Phase 5: 3 hours ✅
- Phase 6: 2 hours ✅ + 0.5 hours (timestamp documentation)
- Phase 7: 2 hours ⚠️ (manual testing pending)

**Original Total: ~17 hours**
**Additional for price timestamps: ~2 hours**
**New Total: ~19 hours**

## Success Criteria

- [x] Users can select fuel types during setup
- [x] Users can reconfigure all settings (location, radius, interval, fuel types)
- [x] Only selected fuel types create sensors
- [x] Cheapest sensor shows lowest price for each fuel type
- [x] Cheapest sensor includes all station metadata
- [x] Regular sensors include all station metadata
- [x] Metadata fields handle None/empty values gracefully
- [x] Cheapest sensor works on map (has lat/long attributes)
- [x] Cheapest sensor works in automations (documented with examples)
- [x] All tests passing (25 passed, 2 skipped)
- [x] Documentation complete (README + CHANGELOG updated)
- [x] No performance degradation (O(n) filtering, O(n) cheapest calculation)
- [x] Backward compatible (defaults to all fuel types)
- [ ] Price last updated timestamp shown on all sensors
- [ ] Users can identify stale/outdated prices
- [ ] Timestamp in human-readable ISO 8601 format
