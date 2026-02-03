# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
