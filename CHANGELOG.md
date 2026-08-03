# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.6.0] - 2026-08-03

### Added
- **Dynamic location tracking** — configure the integration to follow a person or device tracker entity instead of using fixed coordinates
- Multi-step config flow with location mode selector (Static / Dynamic)
- EntitySelector for choosing person/device_tracker entities (filterable, searchable)
- Location change debouncing (30-second minimum between recalculations)
- Fallback to Home Assistant home coordinates when tracked entity has no GPS fix
- Diagnostic attributes on cheapest sensors in dynamic mode (`location_source`, `search_latitude`, `search_longitude`)
- Support for multiple integration entries with the same API credentials (one static + multiple dynamic)
- Dynamic entry titles include tracked entity name (e.g. "UK Fuel Finder (Mark)")
- Dynamic entry device names use person's friendly name for clear identification in entity picker

### Changed
- Config flow now uses two steps: credentials/mode selection, then location-specific settings
- CI upgraded from Python 3.11 to Python 3.12 (required by newer HA core)
- New entries (v1.6.0+) use namespaced sensor unique IDs to avoid conflicts between instances

### Notes
- **Fully backward compatible**: Existing installations continue to work identically with no changes required
- Existing sensor entity IDs are unchanged — only newly created entries use namespaced IDs
- Dynamic location re-filtering uses cached station data (no additional API calls)
- The ukfuelfinder library fetches all stations nationally and filters locally, making location changes essentially free

## [1.5.2] - 2026-02-27

### Fixed
- Manifest keys sorted in required order (domain, name, then alphabetical)
- Bumped GitHub Actions checkout to v4 and setup-python to v5 (Node.js 20 deprecation)

## [1.5.1] - 2026-02-27

### Added
- Hassfest validation GitHub Action (required for HACS default store submission)
- Country code (`GB`) in `hacs.json` for UK-specific filtering in HACS store

## [1.5.0] - 2026-02-27

### Added
- Brand icon for HACS store and Home Assistant UI (fuel pump icon)
- HACS validation GitHub Action for automated compatibility checks
- Daily scheduled CI validation
- Icon attribution in README

### Changed
- README updated with integration icon and HACS publishing improvements

## [1.4.0] - 2026-02-26

### Changed
- Updated ukfuelfinder Python library requirement from >=2.0.0 to >=3.0.0
- Compatible with ukfuelfinder 3.0.0 API changes

### Notes
- The ukfuelfinder 3.0.0 library includes breaking changes in the underlying API:
  - `mft_organisation_name` field removed from API responses (now returns `None`)
  - Field is now `Optional[str]` in the library models
- All existing functionality continues to work (field gracefully handles `None` values)
- All tests pass with ukfuelfinder 3.0.0

## [1.3.0] - 2026-02-19

### Changed
- Updated ukfuelfinder Python library requirement from >=1.2.0 to >=2.0.0
- Compatible with ukfuelfinder 2.0.0 API changes (backward compatible mode enabled by default)

### Notes
- The ukfuelfinder 2.0.0 library includes breaking changes in the underlying API:
  - Removed `success` and `message` fields from API responses (not used by this integration)
  - Added `price_change_effective_timestamp` field to fuel price responses (available but not yet utilized)
  - Invalid batch numbers now return HTTP 404 instead of 400 (not applicable to this integration)
  - Latitude/longitude coordinates now use double precision
- All existing functionality continues to work without changes
- All tests pass with ukfuelfinder 2.0.0

## [1.2.0] - 2026-02-17

### Changed
- Updated ukfuelfinder Python library requirement from >=1.1.0 to >=1.2.0
- GitHub workflow updated to install ukfuelfinder>=1.2.0

## [1.1.0] - 2026-02-08

### Added
- **Fuel Type Filtering**: Select which fuel types to track during setup and reconfiguration
- **Cheapest Fuel Sensors**: Automatic sensors showing the lowest price for each fuel type in your area
- **Price Last Updated Timestamp**: All sensors now show when the station last updated their price (`price_last_updated`)
  - Helps identify stale or incorrect prices
  - ISO 8601 format for easy parsing
  - Available on both regular and cheapest sensors
- **Rich Station Metadata**: All sensors now include:
  - Is supermarket station (`is_supermarket`)
  - Is motorway station (`is_motorway`)
  - Available amenities (`amenities`) - toilets, car wash, AdBlue, etc.
  - Opening times (`opening_times`) - hours by day of week
  - All available fuel types at station (`fuel_types_available`)
  - Legal organization name (`organization_name`)
  - Closure status (`temporary_closure`, `permanent_closure`)
- **Map Integration for Cheapest Sensors**: Cheapest sensors include lat/long for map display and navigation
- **Reconfigure Support for Fuel Types**: Change fuel type selection without removing integration

### Changed
- Fuel type codes updated to match API format (e10, e5, b7, b7_standard, b7_premium, lpg)
- Reconfigure flow now supports changing all settings including fuel types
- Improved sensor attributes with comprehensive station information

### Fixed
- Fuel type normalization now consistent with API responses

## [1.0.0] - 2026-02-03

### Added
- Initial release
- Config flow for UI-based setup
- Automatic discovery of fuel stations within configurable radius
- Real-time fuel price monitoring for multiple fuel types
- Support for unleaded, super unleaded, diesel, premium diesel, and LPG
- Sensor entities with price as state and station metadata as attributes
- Device grouping by station
- Reauthentication flow for expired credentials
- Reconfigure flow for changing location and settings
- Map integration showing station locations
- Historical data support for price trend graphing
- Configurable update intervals (5-1440 minutes)
- HACS compatibility
