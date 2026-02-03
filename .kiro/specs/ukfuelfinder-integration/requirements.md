# UK Fuel Finder Home Assistant Integration - Requirements

## Overview

A Home Assistant custom component that integrates with the UK Government Fuel Finder API via the `ukfuelfinder` Python library. The integration provides real-time fuel price monitoring for nearby petrol stations.

## User Stories

### Configuration

**US-1: Initial Setup**
- WHEN a user adds the UK Fuel Finder integration through the UI
- THE SYSTEM SHALL prompt for API credentials (client_id, client_secret)
- AND THE SYSTEM SHALL prompt for location coordinates (latitude, longitude)
- AND THE SYSTEM SHALL prompt for search radius in kilometers
- AND THE SYSTEM SHALL validate credentials before completing setup

**US-2: Environment Selection**
- WHEN a user configures the integration
- THE SYSTEM SHALL allow selection between "production" and "test" API environments
- AND THE SYSTEM SHALL default to "production" environment

**US-3: Update Interval Configuration**
- WHEN a user configures the integration
- THE SYSTEM SHALL allow setting the update interval (default: 30 minutes)
- AND THE SYSTEM SHALL enforce a minimum interval of 5 minutes to respect API rate limits

### Station Discovery

**US-4: Nearby Station Detection**
- WHEN the integration performs an update
- THE SYSTEM SHALL fetch all fuel stations within the configured radius
- AND THE SYSTEM SHALL create entities for each discovered station
- AND THE SYSTEM SHALL remove entities for stations no longer in range

**US-5: Station Entity Naming**
- WHEN a station entity is created
- THE SYSTEM SHALL use the format `sensor.ukfuelfinder_{station_id}_{fuel_type}`
- AND THE SYSTEM SHALL use lowercase with underscores for entity IDs
- AND THE SYSTEM SHALL ensure entity IDs are unique

### Fuel Price Entities

**US-6: Fuel Type Sensors**
- WHEN a station reports fuel prices
- THE SYSTEM SHALL create a separate sensor entity for each fuel type available
- AND THE SYSTEM SHALL set the entity state to the fuel price in pence
- AND THE SYSTEM SHALL use "GBp" as the unit of measurement

**US-7: Supported Fuel Types**
- WHEN creating fuel type sensors
- THE SYSTEM SHALL support the following fuel types:
  - Unleaded petrol (E10)
  - Super unleaded petrol
  - Diesel
  - Premium diesel
  - LPG
  - Any other fuel types reported by the API

**US-8: Price Updates**
- WHEN fuel prices are updated from the API
- THE SYSTEM SHALL update the corresponding sensor entity states
- AND THE SYSTEM SHALL preserve the last update timestamp
- AND THE SYSTEM SHALL trigger state change events for automations

### Station Metadata

**US-9: Station Attributes**
- WHEN a fuel price sensor is created
- THE SYSTEM SHALL include the following attributes:
  - Station name (trading_name)
  - Address (full address)
  - Brand
  - Distance from home (in km)
  - Latitude and longitude
  - Phone number (if available)
  - Opening hours (if available)
  - Facilities (car wash, shop, 24-hour, EV charging, etc.)
  - Last price update timestamp

**US-10: Distance Calculation**
- WHEN displaying station information
- THE SYSTEM SHALL calculate distance from the configured home location
- AND THE SYSTEM SHALL update distance if home location changes
- AND THE SYSTEM SHALL display distance in kilometers with 2 decimal places

### Data Management

**US-11: Periodic Updates**
- WHEN the update interval elapses
- THE SYSTEM SHALL fetch updated fuel prices from the API
- AND THE SYSTEM SHALL use incremental updates when possible to reduce API calls
- AND THE SYSTEM SHALL handle API rate limiting gracefully

**US-12: Error Handling**
- WHEN an API error occurs
- THE SYSTEM SHALL log the error with appropriate severity
- AND THE SYSTEM SHALL mark affected entities as unavailable
- AND THE SYSTEM SHALL retry on the next update cycle
- AND THE SYSTEM SHALL not crash or disable the integration

**US-13: Authentication Management**
- WHEN the OAuth token expires
- THE SYSTEM SHALL automatically refresh the token
- AND THE SYSTEM SHALL continue operation without user intervention
- AND THE SYSTEM SHALL log authentication failures for user attention

### Integration Features

**US-14: Map Display**
- WHEN viewing the Home Assistant map
- THE SYSTEM SHALL display station locations as markers
- AND THE SYSTEM SHALL show station name and cheapest fuel price on marker click

**US-15: Historical Data**
- WHEN fuel prices are updated
- THE SYSTEM SHALL store historical data for graphing
- AND THE SYSTEM SHALL allow users to create price trend graphs
- AND THE SYSTEM SHALL retain history according to Home Assistant recorder settings

**US-16: Service Actions**
- WHEN the integration is loaded
- THE SYSTEM SHALL provide a service to manually trigger an update
- AND THE SYSTEM SHALL provide a service to search for stations by location

### Testing Requirements

**US-17: Unit Tests**
- WHEN code is committed
- THE SYSTEM SHALL include unit tests for:
  - Config flow validation
  - API client wrapper
  - Entity creation and updates
  - Error handling
  - Data parsing

**US-18: Integration Tests**
- WHEN testing the integration
- THE SYSTEM SHALL include integration tests for:
  - Full setup flow
  - Entity lifecycle (create, update, remove)
  - API interaction with mocked responses
  - Error recovery scenarios

## Acceptance Criteria

### Functional
- ✓ Integration appears in Home Assistant integrations list
- ✓ Config flow guides user through setup with validation
- ✓ Entities are created for each station and fuel type combination
- ✓ Entity states reflect current fuel prices in pence
- ✓ Entity attributes contain complete station metadata
- ✓ Prices update automatically at configured intervals
- ✓ Stations appear on Home Assistant map
- ✓ Historical price data can be graphed

### Non-Functional
- ✓ API calls are minimized through caching and incremental updates
- ✓ Integration handles API errors gracefully without crashing
- ✓ OAuth token refresh is automatic and transparent
- ✓ Entity IDs are stable across restarts
- ✓ Code follows Home Assistant integration quality standards
- ✓ Test coverage exceeds 80%

## Out of Scope

- Price alerts and notifications (can be done via Home Assistant automations)
- Route planning and fuel cost optimization
- Multi-location monitoring (users can add multiple integration instances)
- Custom fuel type filtering (users can hide unwanted entities)
- Price forecasting and analytics
