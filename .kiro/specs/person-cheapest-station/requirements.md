# Requirements: Dynamic Location Tracking

## Origin

Feature request from Paul in the Home Assistant UK Community Facebook group (Jul 24, 2026):

> "Does anybody know if there a way of making the location dynamic on the UK fuel finder integration? Works fine whilst at home but when away from home it still shows the same options."

### Additional community feedback:

- **David**: "Does the integration use HA's home location? If so that can be made dynamic."
- **Paul**: "No it uses static longitude and latitude"
- **Ben**: "Be nice to use the HA Companion's GNSS data if that sensor is enabled in the HA companion app."
- **Andy**: "I'd like the ability to have multiple locations defined, each with some kind of name prefix which can be built into the sensor id string. I could then have multiple cards, one per location centre showing the cheapest locations in that area."
- **RoamingFree87**: "I have 2 different locations set in mine no issues one for home and one for work" (i.e. multiple integration instances already works)

## Problem Statement

The integration currently uses a static latitude/longitude configured during setup. When a user is away from home, the stations shown are still those near their home — not near their current location. Users want the integration to dynamically track their position and show relevant nearby stations.

## Feasibility Assessment

**Fully feasible with zero additional API cost.**

Investigation of the `ukfuelfinder` library reveals:

1. **`search_by_location` is NOT a location-specific API call** — it calls `get_all_pfs_info()` which fetches ALL stations nationally, then filters locally by haversine distance. There is no per-location API endpoint.

2. **Caching built into the library:**
   - Forecourt info (station locations/details): cached **1 hour** (3600s TTL)
   - Prices: cached **15 minutes** (900s TTL)
   - Cache is in-memory, keyed by endpoint + params

3. **Rate limits:**
   - Production: 120 req/min, 10,000/day
   - Test: 30 req/min, 5,000/day

4. **Impact on dynamic location:** Since all station data is already fetched nationally and cached, changing the search location is **purely a local re-filter operation** (haversine calculation). No additional API calls are needed when the user moves. We simply re-run the distance filtering against the cached station list with new coordinates.

**Conclusion:** Dynamic location tracking is essentially free in terms of API usage. The only API calls happen on the normal coordinator update interval — location changes just re-filter the existing data.

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

### US-2: Smart re-filtering on movement

**As a** Home Assistant user with dynamic location  
**I want** the integration to update station results when I move to a different area  
**So that** I see relevant stations without excessive computation

**Acceptance Criteria:**
- AC-2.1: WHEN the tracked entity's location changes, THE SYSTEM SHALL re-filter the cached station data using the new coordinates (haversine distance calculation)
- AC-2.2: THE SYSTEM SHALL NOT make additional API calls when location changes — only re-filter existing cached data
- AC-2.3: WHEN the tracked entity has no location (unavailable, unknown, no GPS), THE SYSTEM SHALL use the fallback static coordinates
- AC-2.4: THE SYSTEM SHALL debounce rapid location updates (minimum 30-second gap between recalculations) to avoid excessive CPU usage
- AC-2.5: THE SYSTEM SHALL continue to use the configured update interval for regular price/station data refreshes from the API
- AC-2.6: WHEN the coordinator fetches fresh data from the API (scheduled update), THE SYSTEM SHALL re-filter using the current tracked location

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

- NFR-1: THE SYSTEM SHALL NOT make any additional API calls due to location changes — all filtering is local against cached data
- NFR-2: THE SYSTEM SHALL handle the tracked entity becoming unavailable gracefully (fall back to static coordinates)
- NFR-3: THE SYSTEM SHALL work with any entity that has latitude/longitude attributes (person, device_tracker, zone, sensor with GPS)
- NFR-4: Distance calculation SHALL use haversine formula (matching the library's existing implementation)
- NFR-5: Re-filtering for location changes SHALL complete in < 100ms for the full national station dataset

---

## Out of Scope (for this iteration)

- Multiple simultaneous dynamic locations per integration instance (use multiple instances for now, per RoamingFree87's suggestion)
- Andy's "named prefix" request (could be a follow-up — the existing multi-instance approach already works)
- Routing/navigation to stations
- Geofence-based automations (users can build those with existing HA tools)

---

## Open Questions

1. ~~**Should we re-query `search_by_location` on movement, or pre-fetch a larger radius and filter locally?**~~ **RESOLVED**: The library already fetches ALL stations nationally. `search_by_location` is purely local filtering. No re-query needed — just re-filter with new coordinates.
2. ~~**What's the API rate limit?**~~ **RESOLVED**: Production: 120 req/min, 10,000/day. Not relevant since location changes don't trigger API calls.
3. **Should the debounce interval be configurable?** Proposed: no, fixed at 30 seconds. Keeps the config simple since re-filtering is cheap.
4. **Should we expose a "distance from person" attribute on existing station sensors?** This would be useful but might be confusing if multiple persons are tracked. Defer to design phase.
