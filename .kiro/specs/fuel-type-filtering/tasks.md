# Fuel Type Filtering and Cheapest Sensor - Implementation Tasks

## Phase 1: Constants and Data Structures

- [ ] **Task 1.1: Add fuel type constants**
  - Add `CONF_FUEL_TYPES` constant to `const.py`
  - Add `FUEL_TYPES` list with all supported fuel types
  - Expected: Constants available for use in config flow and sensor platform

- [ ] **Task 1.2: Document fuel type mapping**
  - Document how API fuel types map to our constants
  - Add comments explaining fuel type normalization
  - Expected: Clear understanding of fuel type handling

## Phase 2: Configuration Flow Enhancement

- [ ] **Task 2.1: Update config flow schema**
  - Add fuel type multi-select to `STEP_USER_DATA_SCHEMA`
  - Use `cv.multi_select` with fuel type options
  - Default to all fuel types
  - Expected: Config flow shows fuel type selection

- [ ] **Task 2.2: Add fuel type validation**
  - Validate at least one fuel type is selected
  - Add error message for empty selection
  - Expected: Users cannot proceed without selecting fuel types

- [ ] **Task 2.3: Update strings.json**
  - Add fuel type selection label and description
  - Add validation error messages
  - Expected: User-friendly UI text

- [ ] **Task 2.4: Test config flow**
  - Test with single fuel type selection
  - Test with multiple fuel type selection
  - Test with all fuel types selected
  - Test validation (empty selection)
  - Expected: Config flow tests passing

## Phase 3: Coordinator Enhancement

- [ ] **Task 3.1: Add get_cheapest_fuel method**
  - Implement method to find cheapest price for a fuel type
  - Return station info with cheapest price
  - Handle case where no stations have the fuel type
  - Expected: Method returns cheapest station data or None

- [ ] **Task 3.2: Test cheapest calculation**
  - Test with multiple stations
  - Test with single station
  - Test with no stations
  - Test with missing price data
  - Test with tied prices (same price at multiple stations)
  - Expected: Coordinator tests passing

## Phase 4: Sensor Platform Enhancement

- [ ] **Task 4.1: Update sensor creation logic**
  - Read selected fuel types from config entry
  - Filter station sensors by selected fuel types
  - Skip stations without selected fuel types
  - Expected: Only selected fuel types create sensors

- [ ] **Task 4.2: Create UKFuelFinderCheapestSensor class**
  - Extend CoordinatorEntity and SensorEntity
  - Implement native_value property (cheapest price)
  - Implement extra_state_attributes (station info)
  - Set appropriate device_info for grouping
  - Expected: Cheapest sensor class implemented

- [ ] **Task 4.3: Add cheapest sensor creation**
  - Create one cheapest sensor per selected fuel type
  - Track cheapest sensors in known_sensors set
  - Expected: Cheapest sensors created on setup

- [ ] **Task 4.4: Test sensor filtering**
  - Test sensor creation with filtered fuel types
  - Test that unselected fuel types don't create sensors
  - Test cheapest sensor creation
  - Expected: Sensor tests passing

- [ ] **Task 4.5: Test cheapest sensor properties**
  - Test native_value calculation
  - Test extra_state_attributes population
  - Test sensor unavailable when no data
  - Test sensor updates when prices change
  - Expected: Cheapest sensor tests passing

## Phase 5: Integration Testing

- [ ] **Task 5.1: Test end-to-end flow**
  - Test setup with fuel type selection
  - Test sensor creation with filtered types
  - Test cheapest sensor creation
  - Test sensor updates
  - Expected: Integration tests passing

- [ ] **Task 5.2: Test reconfiguration**
  - Test changing fuel type selection
  - Test adding fuel types
  - Test removing fuel types
  - Expected: Reconfiguration works correctly

- [ ] **Task 5.3: Test edge cases**
  - Test with no stations having selected fuel type
  - Test with single station
  - Test with all stations having same price
  - Expected: Edge cases handled gracefully

## Phase 6: Documentation

- [ ] **Task 6.1: Update README**
  - Document fuel type filtering feature
  - Document cheapest sensor feature
  - Add examples of using cheapest sensor
  - Add map integration examples
  - Expected: README updated with new features

- [ ] **Task 6.2: Add configuration examples**
  - Show fuel type selection in setup
  - Show cheapest sensor in automations
  - Show cheapest sensor on map
  - Expected: Clear usage examples

- [ ] **Task 6.3: Update CHANGELOG**
  - Document new features
  - Document any breaking changes (none expected)
  - Expected: CHANGELOG updated

## Phase 7: Quality Assurance

- [ ] **Task 7.1: Run all tests**
  - Run unit tests
  - Run integration tests
  - Verify test coverage
  - Expected: All tests passing, >80% coverage

- [ ] **Task 7.2: Manual testing**
  - Test in real Home Assistant instance
  - Test fuel type selection UI
  - Test cheapest sensor on map
  - Test cheapest sensor in automations
  - Expected: Features work as expected

- [ ] **Task 7.3: Code review**
  - Review code for clarity
  - Review code for performance
  - Review code for maintainability
  - Expected: Code meets quality standards

## Dependencies

- Phase 2 depends on Phase 1 (constants)
- Phase 3 can be done in parallel with Phase 2
- Phase 4 depends on Phase 1 and Phase 3
- Phase 5 depends on Phase 2, 3, and 4
- Phase 6 can be done in parallel with Phase 5
- Phase 7 depends on all previous phases

## Estimated Effort

- Phase 1: 1 hour
- Phase 2: 3 hours
- Phase 3: 2 hours
- Phase 4: 4 hours
- Phase 5: 3 hours
- Phase 6: 2 hours
- Phase 7: 2 hours

**Total: ~17 hours**

## Success Criteria

- [ ] Users can select fuel types during setup
- [ ] Only selected fuel types create sensors
- [ ] Cheapest sensor shows lowest price for each fuel type
- [ ] Cheapest sensor includes all station metadata
- [ ] Cheapest sensor works on map
- [ ] Cheapest sensor works in automations
- [ ] All tests passing
- [ ] Documentation complete
- [ ] No performance degradation
- [ ] Backward compatible (defaults to all fuel types)
