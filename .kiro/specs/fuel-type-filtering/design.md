# Fuel Type Filtering and Cheapest Sensor - Design

## Architecture Overview

This feature adds two main capabilities:
1. **Fuel Type Filtering**: Allow users to select which fuel types to track
2. **Cheapest Fuel Sensors**: Provide aggregate sensors showing the cheapest price for each fuel type

## Component Design

### 1. Configuration Flow Enhancement

#### Config Flow Schema Update

Add fuel type selection to the user step:

```python
FUEL_TYPES = [
    "e10",
    "e5", 
    "diesel",
    "premium_diesel",
    "super_unleaded",
    "lpg",
]

STEP_USER_DATA_SCHEMA = vol.Schema({
    # ... existing fields ...
    vol.Optional(CONF_FUEL_TYPES, default=FUEL_TYPES): cv.multi_select(
        {fuel_type: fuel_type.replace("_", " ").title() for fuel_type in FUEL_TYPES}
    ),
})
```

#### Validation

- At least one fuel type must be selected
- Fuel types stored as list in config entry data
- Default to all fuel types for backward compatibility

#### Reconfigure Flow

Add reconfigure step to config flow:

```python
async def async_step_reconfigure(self, user_input=None):
    """Handle reconfiguration of the integration."""
    if user_input is not None:
        # Update config entry with new values
        self.hass.config_entries.async_update_entry(
            self.config_entry,
            data={**self.config_entry.data, **user_input}
        )
        # Reload integration to apply changes
        await self.hass.config_entries.async_reload(self.config_entry.entry_id)
        return self.async_abort(reason="reconfigure_successful")
    
    # Pre-fill form with current values
    return self.async_show_form(
        step_id="reconfigure",
        data_schema=vol.Schema({
            vol.Required(CONF_LATITUDE, default=self.config_entry.data[CONF_LATITUDE]): cv.latitude,
            vol.Required(CONF_LONGITUDE, default=self.config_entry.data[CONF_LONGITUDE]): cv.longitude,
            vol.Required(CONF_RADIUS, default=self.config_entry.data[CONF_RADIUS]): vol.All(
                vol.Coerce(float), vol.Range(min=0.1, max=50)
            ),
            vol.Required(CONF_UPDATE_INTERVAL, default=self.config_entry.data[CONF_UPDATE_INTERVAL]): vol.All(
                vol.Coerce(int), vol.Range(min=5, max=1440)
            ),
            vol.Optional(
                CONF_FUEL_TYPES, 
                default=self.config_entry.data.get(CONF_FUEL_TYPES, FUEL_TYPES)
            ): cv.multi_select(
                {fuel_type: fuel_type.replace("_", " ").title() for fuel_type in FUEL_TYPES}
            ),
        }),
    )
```

**Key Points:**
- All configuration parameters can be changed (location, radius, interval, fuel types)
- Form pre-filled with current values
- Integration reloaded after reconfiguration
- Existing entity lifecycle handles station/sensor cleanup

### 2. Coordinator Enhancement

#### Data Structure

No changes needed - coordinator already provides all fuel types. Filtering happens at sensor creation.

#### Cheapest Price Calculation

Add method to coordinator:

```python
def get_cheapest_fuel(self, fuel_type: str) -> dict | None:
    """Find the cheapest price for a given fuel type."""
    cheapest = None
    cheapest_price = float('inf')
    
    for station_id, station_data in self.data["stations"].items():
        price = station_data["prices"].get(fuel_type)
        if price and price < cheapest_price:
            cheapest_price = price
            cheapest = {
                "station_id": station_id,
                "price": price,
                **station_data["info"],
                "distance": station_data["distance"],
            }
    
    return cheapest
```

### 3. Sensor Platform Enhancement

#### Entity Creation Logic

Update `_check_new_stations()` to filter by selected fuel types:

```python
def _check_new_stations() -> None:
    """Check for new stations and create sensors."""
    if not coordinator.data or "stations" not in coordinator.data:
        return
    
    # Get selected fuel types from config
    selected_fuel_types = entry.data.get(CONF_FUEL_TYPES, FUEL_TYPES)
    
    new_entities = []
    
    # Create regular station sensors (filtered)
    for station_id, station_data in coordinator.data["stations"].items():
        for fuel_type in station_data["prices"].keys():
            if fuel_type not in selected_fuel_types:
                continue  # Skip unselected fuel types
            
            sensor_key = (station_id, fuel_type)
            if sensor_key not in known_sensors:
                known_sensors.add(sensor_key)
                new_entities.append(
                    UKFuelFinderSensor(coordinator, station_id, fuel_type, station_data)
                )
    
    # Create cheapest sensors
    for fuel_type in selected_fuel_types:
        sensor_key = ("cheapest", fuel_type)
        if sensor_key not in known_sensors:
            known_sensors.add(sensor_key)
            new_entities.append(
                UKFuelFinderCheapestSensor(coordinator, fuel_type)
            )
    
    if new_entities:
        async_add_entities(new_entities)
```

#### New Sensor Class: UKFuelFinderCheapestSensor

```python
class UKFuelFinderCheapestSensor(CoordinatorEntity[UKFuelFinderCoordinator], SensorEntity):
    """Sensor showing the cheapest price for a fuel type."""
    
    _attr_has_entity_name = True
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = "GBP"
    _attr_suggested_display_precision = 2
    _attr_icon = "mdi:gas-station"
    
    def __init__(self, coordinator: UKFuelFinderCoordinator, fuel_type: str) -> None:
        """Initialize the cheapest sensor."""
        super().__init__(coordinator)
        self._fuel_type = fuel_type
        self._attr_unique_id = f"cheapest_{fuel_type}"
        self._attr_name = f"Cheapest {fuel_type.replace('_', ' ').title()}"
        
        # Device info for grouping
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, "cheapest")},
            name="Cheapest Fuel Prices",
            manufacturer="UK Fuel Finder",
            model="Aggregate Sensor",
        )
    
    @property
    def native_value(self) -> float | None:
        """Return the cheapest price."""
        cheapest = self.coordinator.get_cheapest_fuel(self._fuel_type)
        if not cheapest:
            return None
        return round(cheapest["price"] / 100, 3)
    
    @property
    def extra_state_attributes(self) -> dict[str, any]:
        """Return station attributes for the cheapest price."""
        cheapest = self.coordinator.get_cheapest_fuel(self._fuel_type)
        if not cheapest:
            return {}
        
        return {
            "station_name": cheapest["trading_name"],
            "brand": cheapest["brand"],
            "address": cheapest["address"],
            "distance_km": round(cheapest["distance"], 2),
            "latitude": cheapest["latitude"],
            "longitude": cheapest["longitude"],
            "phone": cheapest.get("phone"),
            "fuel_type": self._fuel_type,
            "price_pence": cheapest["price"],
            "station_id": cheapest["station_id"],
            "attribution": ATTRIBUTION,
        }
```

### 4. Constants Update

Add new constant:

```python
CONF_FUEL_TYPES = "fuel_types"

FUEL_TYPES = [
    "e10",
    "e5",
    "diesel", 
    "premium_diesel",
    "super_unleaded",
    "lpg",
]
```

## Data Flow

### Setup Flow

```
User selects fuel types
    ↓
Config flow validates (at least one selected)
    ↓
Store in config entry data
    ↓
Coordinator initializes
    ↓
Sensor platform reads selected fuel types
    ↓
Create filtered sensors + cheapest sensors
```

### Update Flow

```
Coordinator fetches all station data
    ↓
Sensor platform filters by selected fuel types
    ↓
Regular sensors update (filtered)
    ↓
Cheapest sensors calculate minimum price
    ↓
Cheapest sensors update attributes with station info
```

### Reconfiguration Flow

```
User changes fuel type selection and/or radius
    ↓
Config entry updated
    ↓
Integration reloaded
    ↓
Coordinator fetches stations with new radius
    ↓
Stations outside new radius marked as missing
    ↓
After 2 update cycles, stale devices removed
    ↓
Old fuel type sensors removed (via stale device removal)
    ↓
New sensors created for new selection
```

**Radius Change Handling:**

The existing stale device removal mechanism (with 2-cycle grace period) automatically handles radius changes:

1. **Radius decreased (e.g., 20km → 10km):**
   - Coordinator fetches stations within new 10km radius
   - Stations between 10-20km no longer appear in coordinator data
   - Existing stale device removal tracks missing stations
   - After 2 update cycles, devices for out-of-range stations are removed

2. **Radius increased (e.g., 10km → 20km):**
   - Coordinator fetches stations within new 20km radius
   - New stations (10-20km) appear in coordinator data
   - Dynamic entity creation adds sensors for new stations
   - Existing stations (0-10km) remain unchanged

No additional code needed - existing entity lifecycle management handles this automatically.

## Entity Naming

### Regular Sensors (unchanged)
- Format: `sensor.ukfuelfinder_{station_id}_{fuel_type}`
- Example: `sensor.ukfuelfinder_12345_e10`

### Cheapest Sensors
- Format: `sensor.ukfuelfinder_cheapest_{fuel_type}`
- Example: `sensor.ukfuelfinder_cheapest_e10`
- Example: `sensor.ukfuelfinder_cheapest_diesel`

## Device Grouping

### Station Devices (unchanged)
- One device per station
- Groups all fuel type sensors for that station

### Cheapest Device (new)
- Single device: "Cheapest Fuel Prices"
- Groups all cheapest sensors
- Separate from station devices

## Error Handling

### No Stations with Selected Fuel Type
- Sensor shows unavailable
- Log warning
- Attributes empty

### Price Data Missing
- Sensor shows unavailable
- Previous attributes retained
- Recovers on next update

### Invalid Fuel Type Selection
- Config flow validation prevents
- Fallback to all fuel types if config corrupted

## Performance Considerations

### Filtering Impact
- O(n) iteration over stations
- Minimal overhead (simple dict lookup)
- No API changes needed

### Cheapest Calculation
- O(n × m) where n = stations, m = fuel types
- Runs on each coordinator update
- Cached in coordinator data (no extra API calls)

### Memory Impact
- Cheapest sensors: ~6 additional entities (one per fuel type)
- Minimal memory overhead per sensor
- No additional data storage needed

## Backward Compatibility

### Existing Installations
- Default to all fuel types if CONF_FUEL_TYPES not in config
- Existing sensors continue to work
- Cheapest sensors added automatically

### Migration
- No migration needed
- Users can reconfigure to select specific fuel types
- No breaking changes

## Testing Strategy

### Unit Tests
- Test fuel type filtering logic
- Test cheapest calculation with various scenarios
- Test sensor creation with different fuel type selections
- Test attributes population

### Integration Tests
- Test config flow with fuel type selection
- Test sensor creation with filtered fuel types
- Test cheapest sensor updates
- Test reconfiguration flow

### Edge Cases
- No stations with selected fuel type
- Single station with multiple fuel types
- All stations have same price
- Station with missing price data
- Empty fuel type selection (validation)

## UI/UX Considerations

### Config Flow
- Clear labels for fuel types
- Helpful descriptions
- Visual feedback for selection
- Validation messages

### Sensor Display
- Clear naming (e.g., "Cheapest E10")
- Descriptive attributes
- Consistent with existing sensors
- Easy to add to dashboards

### Map Integration
- Cheapest sensor shows at station location
- Gas station icon
- Tappable for details
- Works with navigation

## Future Enhancements (Out of Scope)

- Fuel type availability notifications
- Price drop alerts
- Multi-fuel comparison
- Route optimization
- Historical price trends per fuel type
