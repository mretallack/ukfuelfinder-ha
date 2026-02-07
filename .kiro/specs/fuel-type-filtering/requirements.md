# Fuel Type Filtering and Cheapest Sensor - Requirements

## Overview

Enhance the UK Fuel Finder integration to allow users to filter which fuel types they want to track and provide a "cheapest fuel" sensor for easy automation and navigation.

## User Stories

### US-1: Fuel Type Selection During Setup

**WHEN** a user configures the UK Fuel Finder integration  
**THE SYSTEM SHALL** display a multi-select list of available fuel types  
**AND THE SYSTEM SHALL** allow the user to select one or more fuel types  
**AND THE SYSTEM SHALL** default to all fuel types if none are explicitly selected  
**AND THE SYSTEM SHALL** only create sensors for the selected fuel types

### US-2: Fuel Type Filtering

**WHEN** the integration fetches station data  
**THE SYSTEM SHALL** only create sensor entities for fuel types selected by the user  
**AND THE SYSTEM SHALL** skip stations that don't offer any of the selected fuel types  
**AND THE SYSTEM SHALL** update entities when fuel type availability changes

### US-3: Cheapest Fuel Sensor

**WHEN** the integration updates fuel prices  
**THE SYSTEM SHALL** create a "cheapest fuel" sensor for each selected fuel type  
**AND THE SYSTEM SHALL** set the sensor state to the lowest price found  
**AND THE SYSTEM SHALL** include the station name in the sensor attributes  
**AND THE SYSTEM SHALL** include the station address in the sensor attributes  
**AND THE SYSTEM SHALL** include the station location (latitude/longitude) in the sensor attributes  
**AND THE SYSTEM SHALL** include the distance from home in the sensor attributes  
**AND THE SYSTEM SHALL** include the brand in the sensor attributes  
**AND THE SYSTEM SHALL** include the phone number in the sensor attributes  
**AND THE SYSTEM SHALL** include the fuel type in the sensor attributes  
**AND THE SYSTEM SHALL** update when a cheaper price is found

### US-4: Cheapest Sensor on Map

**WHEN** a user adds the cheapest fuel sensor to a map card  
**THE SYSTEM SHALL** display the sensor at the station's location  
**AND THE SYSTEM SHALL** show the gas station icon  
**AND THE SYSTEM SHALL** allow the sensor to be used as a navigation destination

### US-5: Reconfiguration Support

**WHEN** a user reconfigures the integration  
**THE SYSTEM SHALL** allow changing the selected fuel types  
**AND THE SYSTEM SHALL** add sensors for newly selected fuel types  
**AND THE SYSTEM SHALL** remove sensors for deselected fuel types (with grace period)  
**AND THE SYSTEM SHALL** update the cheapest fuel sensors accordingly

## Acceptance Criteria

### AC-1: Fuel Type Selection UI
- Multi-select checkbox list in config flow
- All common UK fuel types listed (E10, E5, Diesel, Premium Diesel, etc.)
- "Select All" / "Deselect All" options
- At least one fuel type must be selected
- Selection persists in config entry

### AC-2: Filtered Sensor Creation
- Only selected fuel types create sensors
- Stations without selected fuel types are skipped
- Entity count matches selected fuel types × available stations
- No errors for missing fuel types

### AC-3: Cheapest Sensor Properties
- Entity ID format: `sensor.ukfuelfinder_cheapest_{fuel_type}`
- State: Lowest price in GBP
- State class: measurement (for statistics)
- Unit: GBP
- Icon: mdi:gas-station
- All station metadata in attributes

### AC-4: Cheapest Sensor Updates
- Updates when any station price changes
- Switches to different station if it becomes cheaper
- Handles station removal gracefully
- Maintains accuracy across coordinator updates

### AC-5: Map Integration
- Cheapest sensor has latitude/longitude attributes
- Displays at correct location on map
- Shows gas station icon
- Can be used in navigation automations

## Non-Functional Requirements

### Performance
- Fuel type filtering should not significantly impact update time
- Cheapest calculation should be O(n) where n = number of stations

### Usability
- Fuel type selection should be intuitive
- Cheapest sensor should be easily discoverable
- Sensor names should be clear and descriptive

### Compatibility
- Must work with existing entity lifecycle management
- Must work with existing stale device removal
- Must maintain backward compatibility (default to all fuel types)

## Out of Scope

- Historical cheapest price tracking (use statistics instead)
- Multi-fuel-type comparison in single sensor
- Price alerts (use automations)
- Route optimization to cheapest station
- Fuel type availability predictions

## Assumptions

- Users know which fuel types their vehicle uses
- Fuel type names are consistent in the API
- At least one station offers each selected fuel type
- Users want to minimize fuel cost (cheapest is best)

## Dependencies

- Existing coordinator data structure
- Existing sensor entity implementation
- Existing config flow infrastructure
- ukfuelfinder library provides fuel type information
