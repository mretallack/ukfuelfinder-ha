# Requirements: Dynamic Location Tracking

## Origin

Feature request from Paul Dye in the Home Assistant UK Community Facebook group (Jul 24, 2026):

> "Does anybody know if there a way of making the location dynamic on the UK fuel finder integration? Works fine whilst at home but when away from home it still shows the same options."

### Additional community feedback:

- **David Emerson**: "Does the integration use HA's home location? If so that can be made dynamic."
- **Paul Dye**: "No it uses static longitude and latitude"
- **Ben Simmons**: "Be nice to use the HA Companion's GNSS data if that sensor is enabled in the HA companion app."
- **Andy Whitworth**: "I'd like the ability to have multiple locations defined, each with some kind of name prefix which can be built into the sensor id string. I could then have multiple cards, one per location centre showing the cheapest locations in that area."
- **RoamingFree87**: "I have 2 different locations set in mine no issues one for home and one for work" (i.e. multiple integration instances already works)

## Problem Statement

The integration currently uses a static latitude/longitude configured during setup. When a user is away from home, the stations shown are still those near their home — not near their current location. Users want the integration to dynamically track their position and show relevant nearby stations.

## Feasibility Assessment

**Feasible, with trade-offs to consider:**

- The API call `search_by_location` accepts lat/lon/radius — we can call it with a dynamic location
- However, calling the API every time a person moves would be excessive
- Sensible approach: allow a person/device_tracker entity as the location source, and re-query when the person has moved significantly (e.g. > 1km from last query location)
- The existing `get_all_pfs_prices` call returns ALL station prices nationally — we already have this. Only the station discovery (`search_by_location`) is location-dependent.

**Key insight**: `get_all_pfs_prices` returns prices for all stations. If we cache station info broadly, we could potentially just re-filter locally without extra API calls. But `search_by_location` is needed to discover which stations exist in an area.

---

## User Stories

### US-1: Dynamic location source

**As a** Home Assistant user  
**I want to** configure my UK Fuel Finder integration to track a person or device_tracker entity as its location source  
**So that** the stations shown change based on where I currently am

**Acceptance Criteria:**
- AC-1.1: WHEN configuring the integration, THE SYSTEM SHALL offer an optional "Location source" field with options: "Static (manual coordinates)" or a list of person/device_tracker entities
- AC-1.2: WHEN "Static" is selected, THE SYSTEM SHALL behave as today (fixed lat/lon)
- AC-1.3: WHEN a person/device_tracker entity is selected, THE SYSTEM SHALL use that entity's latitude/longitude as the search centre
- AC-1.4: WHEN reconfiguring, THE SYSTEM SHALL allow changing between static and dynamic location source
- AC-1.5: WHEN a person entity is selected, THE SYSTEM SHALL still require a fallback static lat/lon (used when person has no GPS fix)

---

### US-2: Smart re-query on movement

**As a** Home Assistant user with dynamic location  
**I want** the integration to fetch new station data when I move to a different area  
**So that** I see relevant stations without excessive API calls

**Acceptance Criteria:**
- AC-2.1: WHEN the tracked entity's location changes by more than a configurable threshold (default: 1km) from the last query location, THE SYSTEM SHALL re-query `search_by_location` with the new coordinates
- AC-2.2: THE SYSTEM SHALL NOT re-query more frequently than once per 5 minutes regardless of movement
- AC-2.3: WHEN the tracked entity has no location (unavailable, unknown, no GPS), THE SYSTEM SHALL use the fallback static coordinates
- AC-2.4: WHEN the tracked entity returns to within the threshold of the last query location, THE SYSTEM SHALL NOT re-query
- AC-2.5: THE SYSTEM SHALL continue to use the configured update interval for regular price refreshes at the current location

---

### US-3: Sensor continuity during location changes

**As a** Home Assistant user  
**I want** a smooth transition when my location changes  
**So that** sensors don't disappear/reappear disruptively

**Acceptance Criteria:**
- AC-3.1: WHEN new stations are discovered at a new location, THE SYSTEM SHALL add new sensor entities
- AC-3.2: WHEN stations from the previous location are no longer in range, THE SYSTEM SHALL use the existing grace period logic (2 update cycles) before removing them
- AC-3.3: THE SYSTEM SHALL update cheapest/closest sensors immediately when new station data arrives
- AC-3.4: THE SYSTEM SHALL maintain entity history — sensors that reappear (e.g. user returns home) SHALL resume their existing entity rather than creating a new one

---

### US-4: Cheapest station updates with location

**As a** Home Assistant user  
**I want** the "cheapest" sensors to reflect the cheapest station near my current location (not my home)  
**So that** the recommendations are relevant to where I am now

**Acceptance Criteria:**
- AC-4.1: WHEN using dynamic location, the cheapest sensors SHALL reflect stations near the current tracked location
- AC-4.2: THE SYSTEM SHALL update the cheapest sensors whenever the station data is refreshed (either from movement-triggered re-query or scheduled update)

---

### US-5: Location source display

**As a** Home Assistant user  
**I want** to see what location the integration is currently using  
**So that** I can verify it's tracking me correctly

**Acceptance Criteria:**
- AC-5.1: THE SYSTEM SHALL expose a diagnostic sensor or attribute showing the current search centre coordinates
- AC-5.2: THE SYSTEM SHALL expose the tracked entity ID and last query time as attributes
- AC-5.3: WHEN using dynamic location, THE SYSTEM SHALL show the distance from the last query point in the integration's device info or a diagnostic entity

---

## Non-Functional Requirements

- NFR-1: THE SYSTEM SHALL NOT exceed the API rate limits — movement threshold and minimum query interval prevent excessive calls
- NFR-2: THE SYSTEM SHALL handle the tracked entity becoming unavailable gracefully (fall back to static coordinates)
- NFR-3: THE SYSTEM SHALL work with any entity that has latitude/longitude attributes (person, device_tracker, zone, sensor with GPS)
- NFR-4: Distance threshold calculation SHALL use haversine formula

---

## Out of Scope (for this iteration)

- Multiple simultaneous dynamic locations per integration instance (use multiple instances for now, per RoamingFree87's suggestion)
- Andy Whitworth's "named prefix" request (could be a follow-up — the existing multi-instance approach already works)
- Routing/navigation to stations
- Geofence-based automations (users can build those with existing HA tools)

---

## Open Questions

1. **Should we re-query `search_by_location` on movement, or pre-fetch a larger radius and filter locally?** Pre-fetching a larger radius means more stations in memory but fewer API calls. Re-querying gives accurate results but uses API quota.
2. **What's the API rate limit?** Need to confirm before deciding the movement threshold defaults.
3. **Should the movement threshold be configurable?** Proposed: yes, with a sensible default (1km).
