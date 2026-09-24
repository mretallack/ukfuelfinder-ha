# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
