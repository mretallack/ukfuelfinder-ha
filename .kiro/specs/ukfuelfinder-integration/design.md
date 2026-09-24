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

## Credential Management

### Reauthentication Flow

When API credentials expire or change, users need to update them without removing and re-adding the integration.

**Implementation:**
```python
async def async_step_reauth(self, entry_data: Mapping[str, Any]) -> ConfigFlowResult:
    """Handle reauthentication when credentials fail."""
    return await self.async_step_reauth_confirm()

async def async_step_reauth_confirm(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
    """Confirm reauthentication with new credentials."""
    if user_input:
        # Test new credentials
        client = FuelFinderClient(
            client_id=user_input["client_id"],
            client_secret=user_input["client_secret"],
            environment=self.config_entry.data["environment"]
        )
        try:
            # Verify credentials work
            await client.test_connection()
        except AuthenticationError:
            return self.async_show_form(
                step_id="reauth_confirm",
                errors={"base": "invalid_auth"}
            )
        
        # Update config entry with new credentials
        return self.async_update_reload_and_abort(
            self._get_reauth_entry(),
            data_updates={
                "client_id": user_input["client_id"],
                "client_secret": user_input["client_secret"]
            }
        )
```

**Trigger Reauthentication:**
- When coordinator receives `AuthenticationError` from API
- Automatically shows notification to user
- User clicks notification to start reauth flow

### Reconfigure Flow

Allow users to change non-credential settings (location, radius, update interval) without re-adding integration.

**Implementation:**
```python
async def async_step_reconfigure(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
    """Handle reconfiguration of the integration."""
    if user_input:
        # Validate new settings
        return self.async_update_reload_and_abort(
            self._get_reconfigure_entry(),
            data_updates={
                "latitude": user_input["latitude"],
                "longitude": user_input["longitude"],
                "radius": user_input["radius"],
                "update_interval": user_input["update_interval"]
            }
        )
    
    # Show form with current values pre-filled
    return self.async_show_form(
        step_id="reconfigure",
        data_schema=vol.Schema({
            vol.Required("latitude", default=self.config_entry.data["latitude"]): cv.latitude,
            vol.Required("longitude", default=self.config_entry.data["longitude"]): cv.longitude,
            vol.Required("radius", default=self.config_entry.data["radius"]): vol.All(vol.Coerce(float), vol.Range(min=0.1, max=50)),
            vol.Required("update_interval", default=self.config_entry.data["update_interval"]): vol.All(vol.Coerce(int), vol.Range(min=5, max=1440))
        })
    )
```

## HACS Compatibility

### Repository Structure Requirements

For HACS distribution, the repository must follow this structure:

```
ukfuelfinder-ha/
├── custom_components/
│   └── ukfuelfinder/
│       ├── __init__.py
│       ├── manifest.json
│       ├── config_flow.py
│       ├── const.py
│       ├── coordinator.py
│       ├── sensor.py
│       ├── strings.json
│       └── translations/
│           └── en.json
├── README.md
├── hacs.json (optional)
├── LICENSE
└── .github/
    └── workflows/
        └── validate.yml
```

### manifest.json Requirements

Must include these keys for HACS:
```json
{
  "domain": "ukfuelfinder",
  "name": "UK Fuel Finder",
  "version": "1.0.0",
  "documentation": "https://github.com/mretallack/ukfuelfinder-ha",
  "issue_tracker": "https://github.com/mretallack/ukfuelfinder-ha/issues",
  "codeowners": ["@mretallack"],
  "requirements": ["ukfuelfinder>=1.0.0"],
  "config_flow": true,
  "iot_class": "cloud_polling"
}
```

### hacs.json (Optional)

```json
{
  "name": "UK Fuel Finder",
  "render_readme": true,
  "homeassistant": "2024.1.0"
}
```

### Home Assistant Brands

Must add integration to [home-assistant/brands](https://github.com/home-assistant/brands) repository for proper UI display.

## Home Assistant Core Submission (Future)

### Quality Scale Requirements

To submit to Home Assistant core, must meet **Bronze tier** minimum:

**Bronze Tier Requirements:**
- ✓ Config flow for UI setup
- ✓ Basic coding standards
- ✓ Automated setup tests
- ✓ Basic documentation

**Silver Tier (Recommended):**
- ✓ Everything in Bronze
- ✓ Active code owners
- ✓ Error recovery and reconnection
- ✓ Reauthentication flow
- ✓ Detailed documentation with troubleshooting

**Gold Tier (Aspirational):**
- ✓ Everything in Silver
- ✓ Automatic discovery (not applicable for this integration)
- ✓ Reconfigure flow
- ✓ Full translations support
- ✓ 95%+ test coverage
- ✓ Extensive end-user documentation
- ✓ Diagnostics support

### quality_scale.yaml

Track implementation progress:
```yaml
rules:
  config_flow: done
  test_before_configure: done
  unique_config_entry: done
  config_entry_unloading: done
  reauthentication_flow: done
  reconfiguration_flow: done
  entity_unique_id: done
  has_entity_name: done
  entity_unavailable: done
  integration_owner: done
  test_coverage: in_progress
  diagnostics: planned
  discovery:
    status: exempt
    comment: Integration requires API credentials, cannot auto-discover
```

## README.md Structure

The README.md must include:

### 1. Overview
- Brief description of integration
- Features list
- Screenshot of entities in Home Assistant

### 2. Installation

**Manual Installation:**
```markdown
1. Copy `custom_components/ukfuelfinder` to your Home Assistant `custom_components` directory
2. Restart Home Assistant
3. Go to Settings > Devices & Services
4. Click Add Integration
5. Search for "UK Fuel Finder"
```

**HACS Installation:**
```markdown
1. Open HACS
2. Go to Integrations
3. Click the three dots menu
4. Select "Custom repositories"
5. Add `https://github.com/mretallack/ukfuelfinder-ha`
6. Select "Integration" as category
7. Click "UK Fuel Finder" in the list
8. Click "Download"
9. Restart Home Assistant
```

### 3. Configuration

**Prerequisites:**
- UK Fuel Finder API credentials from [developer.fuel-finder.service.gov.uk](https://www.developer.fuel-finder.service.gov.uk)
- Your home location coordinates

**Setup Steps:**
1. Add integration through UI
2. Enter API credentials
3. Enter location and radius
4. Configure update interval

### 4. Usage

**Entities Created:**
- One sensor per fuel type per station
- Format: `sensor.ukfuelfinder_{station_id}_{fuel_type}`
- State: Price in pence (GBp)

**Entity Attributes:**
- Station name, brand, address
- Distance from home
- Location coordinates
- Phone number
- Facilities

**Example Automation:**
```yaml
automation:
  - alias: "Notify when fuel price drops"
    trigger:
      - platform: numeric_state
        entity_id: sensor.ukfuelfinder_12345_unleaded
        below: 140
    action:
      - service: notify.mobile_app
        data:
          message: "Fuel price dropped to {{ states('sensor.ukfuelfinder_12345_unleaded') }}p at {{ state_attr('sensor.ukfuelfinder_12345_unleaded', 'station_name') }}"
```

**Example Dashboard Card:**
```yaml
type: entities
title: Nearby Fuel Stations
entities:
  - sensor.ukfuelfinder_12345_unleaded
  - sensor.ukfuelfinder_12345_diesel
  - sensor.ukfuelfinder_67890_unleaded
```

### 5. Troubleshooting

**Integration won't load:**
- Check Home Assistant logs for errors
- Verify API credentials are correct
- Ensure ukfuelfinder library is installed

**No stations found:**
- Increase search radius
- Verify location coordinates are correct
- Check if stations exist in your area

**Authentication errors:**
- Credentials may have expired
- Click "Fix" on integration card to reauthenticate
- Verify credentials at developer portal

**Entities unavailable:**
- Check internet connection
- Verify API service is operational
- Check Home Assistant logs for errors

### 6. Contributing

Link to CONTRIBUTING.md with:
- How to report bugs
- How to request features
- Development setup instructions
- Code style guidelines

### 7. License

MIT License with attribution to UK Government Fuel Finder API

### 8. Acknowledgments

- Data provided by UK Government Fuel Finder service
- Uses [ukfuelfinder](https://github.com/mretallack/ukfuelfinder) Python library

## Future Enhancements

### Phase 2 (Post-MVP)
- Options flow for runtime configuration changes ✓ (now in MVP)
- Service to manually refresh specific stations
- Service to search for cheapest fuel in radius
- Binary sensor for "price below threshold"

### Phase 3
- Multiple location support
- Price change notifications
- Integration with route planning
- Fuel consumption tracking
