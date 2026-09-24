# UK Fuel Finder Home Assistant Integration - Implementation Tasks

## Phase 1: Project Setup

- [x] **Task 1.1: Initialize project structure**
  - Create `custom_components/ukfuelfinder/` directory
  - Create `__init__.py`, `manifest.json`, `const.py`
  - Create `tests/` directory structure
  - Expected: Basic project skeleton in place

- [x] **Task 1.2: Create manifest.json**
  - Define domain, name, version
  - Add ukfuelfinder dependency (>=1.1.0)
  - Set config_flow to true
  - Add documentation and issue tracker URLs
  - Expected: Valid manifest.json that Home Assistant recognizes

- [x] **Task 1.3: Define constants**
  - Create `const.py` with domain, defaults, and configuration keys
  - Define supported fuel types
  - Define update intervals and limits
  - Expected: Centralized constants file

- [x] **Task 1.4: Setup test infrastructure**
  - Create `tests/conftest.py` with pytest fixtures
  - Setup mock Home Assistant instance
  - Create mock API response fixtures
  - Expected: Test framework ready for use

## Phase 2: Configuration Flow

- [x] **Task 2.1: Create config flow schema**
  - Define configuration schema in `config_flow.py`
  - Add field validators (latitude, longitude, radius)
  - Create user-friendly field descriptions
  - Expected: Schema that collects all required configuration

- [x] **Task 2.2: Implement config flow handler**
  - Create `ConfigFlow` class extending `ConfigFlow`
  - Implement `async_step_user()` for initial setup
  - Add form display and error handling
  - Expected: Basic config flow that displays form

- [x] **Task 2.3: Add credential validation**
  - Implement API connection test
  - Validate credentials before saving
  - Handle authentication errors gracefully
  - Expected: Only valid credentials are accepted

- [x] **Task 2.4: Create strings.json**
  - Add UI strings for config flow
  - Add error messages
  - Add field descriptions
  - Expected: User-friendly configuration interface

- [ ] **Task 2.5: Implement reauthentication flow**
  - Add `async_step_reauth()` method
  - Add `async_step_reauth_confirm()` method
  - Test new credentials before updating
  - Update config entry with new credentials
  - Expected: Users can update expired credentials via UI

- [ ] **Task 2.6: Implement reconfigure flow**
  - Add `async_step_reconfigure()` method
  - Allow changing location, radius, update interval
  - Pre-fill form with current values
  - Reload integration after reconfigure
  - Expected: Users can change settings without re-adding integration

- [x] **Task 2.7: Write config flow tests**
  - Test valid configuration acceptance
  - Test field validation
  - Test credential validation
  - Test reauthentication flow
  - Test reconfigure flow
  - Test error handling
  - Expected: Config flow tests passing with >80% coverage

## Phase 3: Data Coordinator

- [x] **Task 3.1: Create coordinator class**
  - Create `coordinator.py` with `DataUpdateCoordinator` subclass
  - Initialize ukfuelfinder client
  - Setup update interval from config
  - Expected: Basic coordinator structure

- [x] **Task 3.2: Implement data fetching**
  - Implement `_async_update_data()` method
  - Fetch stations using `search_by_location()`
  - Fetch prices using `get_all_pfs_prices()`
  - Parse and structure data
  - Expected: Coordinator fetches and returns structured data

- [x] **Task 3.3: Add distance calculation**
  - Calculate distance for each station from home
  - Sort stations by distance
  - Include distance in returned data
  - Expected: Distance data available for each station

- [x] **Task 3.4: Implement error handling**
  - Handle authentication errors
  - Handle rate limiting
  - Handle network errors
  - Implement retry logic
  - Expected: Coordinator handles errors gracefully

- [x] **Task 3.5: Write coordinator tests**
  - Test data fetching with mocked API
  - Test error handling scenarios
  - Test distance calculation
  - Test update scheduling
  - Expected: Coordinator tests passing with >80% coverage

## Phase 4: Integration Setup

- [x] **Task 4.1: Implement async_setup_entry**
  - Create `__init__.py` setup function
  - Initialize coordinator
  - Perform initial data fetch
  - Setup sensor platform
  - Expected: Integration loads successfully

- [x] **Task 4.2: Implement async_unload_entry**
  - Cleanup coordinator
  - Unload platforms
  - Release resources
  - Expected: Integration unloads cleanly

- [x] **Task 4.3: Add integration-level error handling**
  - Handle setup failures
  - Log errors appropriately
  - Mark integration as failed if needed
  - Expected: Robust integration lifecycle management

- [x] **Task 4.4: Write integration setup tests**
  - Test successful setup
  - Test setup failures
  - Test unload
  - Expected: Integration setup tests passing

## Phase 5: Sensor Platform

- [x] **Task 5.1: Create sensor platform file**
  - Create `sensor.py`
  - Implement `async_setup_entry()`
  - Define sensor entity class
  - Expected: Basic sensor platform structure

- [x] **Task 5.2: Implement FuelPriceSensor entity**
  - Extend `CoordinatorEntity` and `SensorEntity`
  - Implement required properties (name, state, unit)
  - Generate unique entity IDs
  - Use MONETARY device class with GBP unit
  - Convert prices from pence to pounds
  - Add suggested_display_precision for currency
  - Expected: Basic sensor entity that displays price correctly

- [x] **Task 5.3: Add entity attributes**
  - Implement `extra_state_attributes` property
  - Include station metadata (name, address, brand, etc.)
  - Include distance and location
  - Include facilities and phone
  - Include price_pence for original value
  - Expected: Rich entity attributes available

- [x] **Task 5.4: Implement device grouping**
  - Create device info for each station
  - Group fuel type sensors by station
  - Add device identifiers
  - Add gas station icon (mdi:gas-station)
  - Expected: Sensors grouped by station in UI

- [x] **Task 5.5: Handle entity lifecycle**
  - Create entities for new stations dynamically using coordinator listener
  - Update existing entities via coordinator
  - Remove entities for stations out of range (2-cycle grace period)
  - Track known sensors to prevent duplicates
  - Reset grace period counter when stations reappear
  - Expected: Dynamic entity management with stale device removal

- [x] **Task 5.6: Write sensor tests**
  - Test entity creation
  - Test state updates
  - Test attribute population
  - Test device grouping
  - Test entity removal
  - Test dynamic station addition
  - Test stale device removal with grace period
  - Test station reappearance during grace period
  - Expected: Sensor tests passing with >80% coverage (15/15 tests passing)

## Phase 6: Integration Testing

- [x] **Task 6.1: Create integration test suite**
  - Test full setup flow
  - Test entity creation from real-like data
  - Test update cycle
  - Expected: End-to-end integration tests

- [ ] **Task 6.2: Test error scenarios**
  - Test API unavailable
  - Test invalid credentials
  - Test network errors
  - Test rate limiting
  - Expected: Error handling verified

- [ ] **Task 6.3: Test edge cases**
  - Test no stations in radius
  - Test stations with missing data
  - Test location changes
  - Expected: Edge cases handled correctly

- [ ] **Task 6.4: Performance testing**
  - Test with many stations
  - Test update performance
  - Verify memory usage
  - Expected: Performance within acceptable limits

## Phase 7: Documentation

- [x] **Task 7.1: Create README.md**
  - Add overview and features
  - Add installation instructions (manual and HACS)
  - Add configuration prerequisites and steps
  - Add usage examples (entities, automations, dashboard cards)
  - Add map display documentation
  - Add troubleshooting section
  - Add contributing guidelines
  - Add license and acknowledgments
  - Expected: Comprehensive README for end users

- [ ] **Task 7.2: Create hacs.json**
  - Define HACS metadata
  - Set minimum Home Assistant version
  - Expected: HACS-compatible repository

- [x] **Task 7.3: Add code documentation**
  - Add docstrings to all classes and methods
  - Add inline comments for complex logic
  - Document data structures
  - Expected: Well-documented codebase

- [ ] **Task 7.4: Create example configurations**
  - Add example automations
  - Add example Lovelace cards
  - Add example use cases
  - Expected: Users can easily get started

- [x] **Task 7.5: Create TESTING.md**
  - Document test structure and approach
  - Document how to run tests
  - Document test coverage
  - Expected: Clear testing documentation

## Phase 8: Quality Assurance

- [x] **Task 8.1: Run linting**
  - Run black and isort on all code
  - Fix formatting issues
  - Ensure code style compliance
  - Expected: Clean formatting results

- [ ] **Task 8.2: Run type checking**
  - Run mypy on all code
  - Add type hints where missing
  - Fix type errors
  - Expected: Clean type checking results

- [x] **Task 8.3: Verify test coverage**
  - Run coverage report
  - Ensure >80% coverage
  - Add tests for uncovered code
  - Expected: Test coverage goal met (15/15 unit tests passing)

- [x] **Task 8.4: Manual testing**
  - Test in real Home Assistant instance
  - Test all user flows
  - Test error scenarios
  - Verify UI appearance
  - Expected: Integration works as expected

## Phase 9: Deployment

- [ ] **Task 9.1: Prepare for HACS release**
  - Verify repository structure matches HACS requirements
  - Ensure manifest.json has all required fields
  - Create GitHub release with version tag
  - Expected: HACS-compatible release

- [ ] **Task 9.2: Update README with installation**
  - Add HACS installation instructions
  - Add manual installation instructions
  - Add screenshots
  - Expected: Clear installation instructions

- [ ] **Task 9.3: Submit to HACS (optional)**
  - Submit repository to HACS default repositories
  - Provide required information
  - Expected: Integration available in HACS

- [ ] **Task 9.4: Create CHANGELOG.md**
  - Document all features in initial release
  - Follow Keep a Changelog format
  - Expected: Clear version history

## Phase 10: Future Core Submission (Optional)

- [ ] **Task 10.1: Submit to Home Assistant Brands**
  - Create brand assets (logo, icon)
  - Submit PR to home-assistant/brands
  - Expected: Integration has proper branding in HA

- [ ] **Task 10.2: Achieve Bronze tier quality scale**
  - Verify all Bronze tier requirements met
  - Update quality_scale.yaml
  - Expected: Ready for core submission

- [ ] **Task 10.3: Submit to Home Assistant Core**
  - Create PR to home-assistant/core
  - Respond to code review feedback
  - Expected: Integration accepted into core (long-term goal)

## Dependencies

- Task 2.x depends on Task 1.x (project setup)
- Task 2.5 and 2.6 (reauth/reconfigure) can be done after Task 2.4
- Task 3.x depends on Task 1.x (project setup)
- Task 4.x depends on Task 2.x and 3.x (config flow and coordinator)
- Task 5.x depends on Task 3.x and 4.x (coordinator and integration setup)
- Task 6.x depends on Task 5.x (sensor implementation)
- Task 7.x can be done in parallel with Task 6.x
- Task 8.x depends on all previous tasks
- Task 9.x depends on Task 8.x (QA complete)
- Task 10.x is optional and can be done after Task 9.x

## Resources Needed

- Home Assistant development environment
- UK Fuel Finder API credentials (test and production)
- ukfuelfinder Python library (pip install ukfuelfinder)
- pytest and pytest-homeassistant-custom-component
- Access to Home Assistant documentation
- HACS for testing installation

## Estimated Effort

- Phase 1: 2 hours
- Phase 2: 6 hours (includes reauth/reconfigure flows)
- Phase 3: 6 hours
- Phase 4: 3 hours
- Phase 5: 8 hours
- Phase 6: 6 hours
- Phase 7: 6 hours (includes comprehensive README)
- Phase 8: 4 hours
- Phase 9: 3 hours
- Phase 10: Variable (depends on core submission process)

**Total MVP: ~44 hours**
