# UK Fuel Finder Home Assistant Integration - Design

## Architecture Overview

The integration follows Home Assistant's standard architecture pattern with config flow, coordinator, and platform entities.

```
┌─────────────────────────────────────────────────────────────┐
│                     Home Assistant Core                      │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                  UK Fuel Finder Integration                  │
│                                                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Config Flow  │  │ Coordinator  │  │   Sensors    │      │
│  │              │  │              │  │              │      │
│  │ - Setup UI   │  │ - Polling    │  │ - Price      │      │
│  │ - Validation │  │ - Updates    │  │ - Metadata   │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│                              │                               │
└──────────────────────────────┼───────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                  ukfuelfinder Library                        │
│                                                               │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              FuelFinderClient                        │   │
│  │  - OAuth authentication                              │   │
│  │  - API requests                                      │   │
│  │  - Caching                                           │   │
│  │  - Rate limiting                                     │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│              UK Government Fuel Finder API                   │
└─────────────────────────────────────────────────────────────┘
```

## Component Structure

```
custom_components/ukfuelfinder/
├── __init__.py           # Integration setup and coordinator
├── manifest.json         # Integration metadata
├── config_flow.py        # UI configuration flow
├── const.py             # Constants and defaults
├── sensor.py            # Sensor platform implementation
├── coordinator.py       # Data update coordinator
├── strings.json         # UI strings for translations
└── translations/
    └── en.json          # English translations
```

## Data Flow

### Initial Setup Flow

```
User adds integration
        │
        ▼
Config Flow prompts for:
  - Client ID
  - Client Secret
  - Environment (prod/test)
  - Latitude
  - Longitude
  - Radius (km)
  - Update interval
        │
        ▼
Validate credentials
  - Test API connection
  - Verify OAuth token
        │
        ▼
Create config entry
        │
        ▼
Initialize coordinator
        │
        ▼
Perform initial data fetch
        │
        ▼
Create sensor entities
```

### Update Cycle Flow

```
Timer triggers update
        │
        ▼
Coordinator requests data
        │
        ▼
FuelFinderClient fetches:
  - All stations in radius
  - Current fuel prices
        │
        ▼
Calculate distances
        │
        ▼
Group by station
        │
        ▼
Update sensor entities:
  - Set state (price)
  - Update attributes
        │
        ▼
Trigger state change events
```

## Key Components

### 1. Config Flow (`config_flow.py`)

Handles user configuration through the UI.

**Schema:**
```python
{
    "client_id": str,
    "client_secret": str,
    "environment": "production" | "test",
    "latitude": float,
    "longitude": float,
    "radius": float (default: 5.0),
    "update_interval": int (default: 30, min: 5)
}
```

**Validation:**
- Client ID and secret are required
- Latitude: -90 to 90
- Longitude: -180 to 180
- Radius: 0.1 to 50 km
- Update interval: 5 to 1440 minutes
- Test API connection before saving

### 2. Data Update Coordinator (`coordinator.py`)

Manages periodic data updates and caching.

**Responsibilities:**
- Schedule updates based on configured interval
- Fetch data from ukfuelfinder library
- Calculate distances from home location
- Distribute data to sensor entities
- Handle API errors and retries

**Data Structure:**
```python
{
    "stations": {
        "station_id_1": {
            "info": {
                "id": str,
                "trading_name": str,
                "address": str,
                "brand": str,
                "latitude": float,
                "longitude": float,
                "phone": str,
                "facilities": list[str],
            },
            "distance": float,
            "prices": {
                "unleaded": float,
                "super_unleaded": float,
                "diesel": float,
                "premium_diesel": float,
                "lpg": float,
            },
            "last_updated": datetime,
        },
        ...
    }
}
```

### 3. Sensor Platform (`sensor.py`)

Creates and manages sensor entities for fuel prices.

**Entity Naming:**
- Format: `sensor.ukfuelfinder_{station_id}_{fuel_type}`
- Example: `sensor.ukfuelfinder_12345_unleaded`

**Entity State:**
- Value: Fuel price in pence (e.g., 145.9)
- Unit: GBp (Great British pence)

**Entity Attributes:**
```python
{
    "station_name": str,
    "brand": str,
    "address": str,
    "distance_km": float,
    "latitude": float,
    "longitude": float,
    "phone": str,
    "facilities": list[str],
    "fuel_type": str,
    "last_updated": datetime,
    "attribution": "Data provided by UK Government Fuel Finder",
}
```

**Device Grouping:**
- Each station is a device
- Fuel type sensors are entities within the device
- Device info includes station name, brand, and location

## API Integration

### ukfuelfinder Library Usage

```python
from ukfuelfinder import FuelFinderClient

# Initialize client
client = FuelFinderClient(
    client_id=config["client_id"],
    client_secret=config["client_secret"],
    environment=config["environment"]
)

# Fetch nearby stations
nearby_stations = client.search_by_location(
    latitude=config["latitude"],
    longitude=config["longitude"],
    radius_km=config["radius"]
)

# Returns: list[(distance, PFSInfo)]
for distance, station in nearby_stations:
    # Get prices for this station
    prices = client.get_all_pfs_prices()
    # Filter for this station's prices
    station_prices = [p for p in prices if p.pfs_id == station.pfs_id]
```

### Error Handling

**API Errors:**
- `AuthenticationError`: Log error, mark entities unavailable, notify user
- `RateLimitError`: Wait and retry with exponential backoff
- `NetworkError`: Log warning, retry on next cycle
- `ValidationError`: Log error, mark entities unavailable

**Recovery Strategy:**
- Maintain last known good data
- Mark entities as unavailable on persistent errors
- Automatically recover when API becomes available
- Log all errors for debugging

## Entity Lifecycle

### Creation
1. Coordinator fetches station data
2. For each station and fuel type combination:
   - Create unique entity ID
   - Initialize entity with station metadata
   - Register entity with Home Assistant

### Updates
1. Coordinator fetches updated prices
2. Compare with existing entities
3. Update entity states and attributes
4. Trigger state change events

### Removal
1. Station no longer in radius
2. Mark entity as unavailable
3. Remove entity after grace period (2 update cycles)

## Configuration Storage

**Config Entry Data:**
```python
{
    "client_id": str,
    "client_secret": str,  # Stored securely
    "environment": str,
    "latitude": float,
    "longitude": float,
    "radius": float,
    "update_interval": int,
}
```

**Options Flow:**
- Allow changing radius
- Allow changing update interval
- Allow changing location
- Require re-authentication for credential changes

## Testing Strategy

### Unit Tests

**Config Flow Tests:**
- Valid configuration accepted
- Invalid credentials rejected
- Field validation (ranges, formats)
- API connection test

**Coordinator Tests:**
- Data fetching and parsing
- Error handling and recovery
- Update scheduling
- Distance calculation

**Sensor Tests:**
- Entity creation
- State updates
- Attribute population
- Device grouping

### Integration Tests

**Full Flow Tests:**
- Complete setup through config flow
- Entity creation and updates
- API interaction (mocked)
- Error scenarios

**Mock Data:**
- Sample API responses
- Various station configurations
- Error responses
- Edge cases (no stations, missing data)

### Test Coverage Goals
- Minimum 80% code coverage
- All error paths tested
- All user flows tested

## Performance Considerations

### API Call Optimization
- Use incremental updates when available
- Cache station information (changes infrequently)
- Only fetch prices on update cycle
- Respect API rate limits

### Memory Management
- Limit stored historical data
- Clean up removed entities
- Efficient data structures

### Update Frequency
- Default: 30 minutes (balance freshness vs. API usage)
- Minimum: 5 minutes (respect rate limits)
- Maximum: 24 hours (ensure data freshness)

## Security Considerations

- Store API credentials securely in config entry
- Never log credentials
- Use HTTPS for all API calls (handled by library)
- Validate all user inputs
- Sanitize station data before display

## Future Enhancements

### Phase 2 (Post-MVP)
- Options flow for runtime configuration changes
- Service to manually refresh specific stations
- Service to search for cheapest fuel in radius
- Binary sensor for "price below threshold"

### Phase 3
- Multiple location support
- Price change notifications
- Integration with route planning
- Fuel consumption tracking
