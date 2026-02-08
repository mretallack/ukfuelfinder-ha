# UK Fuel Finder for Home Assistant

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/custom-components/hacs)

A Home Assistant custom component that integrates with the UK Government Fuel Finder API to monitor fuel prices at nearby petrol stations.

## Features

- 🔍 **Automatic Station Discovery** - Finds fuel stations within your specified radius
- 💰 **Real-time Price Monitoring** - Track fuel prices for multiple fuel types
- 🎯 **Cheapest Fuel Sensors** - Automatically find the cheapest price for each fuel type
- 🏪 **Rich Station Metadata** - Supermarket, motorway, amenities, opening times, and more
- ⚙️ **Fuel Type Filtering** - Choose which fuel types to track
- 📊 **Historical Data** - Graph price trends over time
- 🗺️ **Map Integration** - View stations and cheapest prices on your Home Assistant map
- 🔄 **Automatic Updates** - Configurable update intervals (5-1440 minutes)
- 🔐 **Secure Credential Management** - Easy reauthentication when credentials change
- ⚙️ **Reconfigurable** - Change location, radius, and fuel types without re-adding

## Supported Fuel Types

- E10 (Unleaded Petrol, 10% ethanol)
- E5 (Premium Unleaded, 5% ethanol)
- B7 (Diesel, 7% biodiesel)
- B7 Standard (Standard Diesel)
- B7 Premium (Premium Diesel)
- LPG (Liquefied Petroleum Gas)

## Installation

### HACS (Recommended)

1. Open HACS in Home Assistant
2. Go to "Integrations"
3. Click the three dots menu (⋮) in the top right
4. Select "Custom repositories"
5. Add this repository URL: `https://github.com/mretallack/ukfuelfinder-ha`
6. Select "Integration" as the category
7. Click "Add"
8. Find "UK Fuel Finder" in the list and click "Download"
9. Restart Home Assistant

### Manual Installation

1. Copy the `custom_components/ukfuelfinder` directory to your Home Assistant `custom_components` directory
2. Restart Home Assistant

## Configuration

### Prerequisites

- UK Fuel Finder API credentials from [developer.fuel-finder.service.gov.uk](https://www.developer.fuel-finder.service.gov.uk)
- Your home location coordinates (latitude and longitude)

### Setup

1. Go to **Settings** → **Devices & Services**
2. Click **Add Integration**
3. Search for "UK Fuel Finder"
4. Enter your configuration:
   - **Client ID**: Your API client ID
   - **Client Secret**: Your API client secret
   - **Environment**: Choose "production" or "test"
   - **Latitude**: Your location latitude
   - **Longitude**: Your location longitude
   - **Search Radius**: Distance in kilometers (0.1-50 km)
   - **Update Interval**: How often to fetch prices (5-1440 minutes)
   - **Fuel Types**: Select which fuel types to track (defaults to all)

### Reconfiguration

You can change your settings at any time:

1. Go to **Settings** → **Devices & Services**
2. Find "UK Fuel Finder" and click **Configure**
3. Update any settings (location, radius, update interval, fuel types)
4. Click **Submit** - the integration will reload with new settings

## Usage

### Station Sensors

The integration creates sensor entities for each fuel type at each station:

- **Entity ID Format**: `sensor.ukfuelfinder_{station_id}_{fuel_type}`
- **State**: Fuel price in pounds (GBP)
- **Unit**: GBP (British Pounds)
- **State Class**: `measurement` (enables long-term statistics)
- **Attributes**:
  - Station name, brand, address
  - Distance from home (km)
  - Latitude/longitude
  - Phone number
  - Is supermarket station
  - Is motorway station
  - Available amenities (toilets, car wash, AdBlue, etc.)
  - Opening times
  - All available fuel types
  - Organization name
  - Closure status

### Cheapest Fuel Sensors

For each selected fuel type, a "cheapest" sensor shows the lowest price in your area:

- **Entity ID Format**: `sensor.ukfuelfinder_cheapest_{fuel_type}`
- **State**: Lowest price in pounds (GBP)
- **Attributes**: All details of the station with the cheapest price
- **Map Integration**: Shows the cheapest station location on maps
- **Use in Automations**: Navigate to cheapest station, price alerts, etc.

**Example Entities:**
- `sensor.ukfuelfinder_cheapest_e10` - Cheapest E10 petrol
- `sensor.ukfuelfinder_cheapest_b7` - Cheapest diesel

### Entities
  - Latitude and longitude
  - Phone number
  - Price in pence (for reference)

#### Why `measurement` state class?

Fuel price sensors use `state_class: measurement` instead of `device_class: monetary` to enable **long-term statistics** in Home Assistant. This allows you to:

- View price trends over time in the Statistics card
- Track min/max/average prices per hour
- Create historical price graphs
- Use price data in the Energy dashboard

While fuel prices are monetary values, they represent **current market rates** (measurements) rather than accumulated costs (totals). This classification follows Home Assistant's best practices for rate-based pricing sensors and enables richer data visualization.
  - Fuel type

### Example Automations

#### Notify when cheapest fuel price drops

```yaml
automation:
  - alias: "Notify when E10 price drops below £1.40"
    trigger:
      - platform: numeric_state
        entity_id: sensor.ukfuelfinder_cheapest_e10
        below: 1.40
    action:
      - service: notify.mobile_app
        data:
          message: >
            E10 now £{{ states('sensor.ukfuelfinder_cheapest_e10') }} at 
            {{ state_attr('sensor.ukfuelfinder_cheapest_e10', 'station_name') }}
            ({{ state_attr('sensor.ukfuelfinder_cheapest_e10', 'distance_km') }}km away)
```

#### Navigate to cheapest station

```yaml
automation:
  - alias: "Navigate to cheapest diesel"
    trigger:
      - platform: state
        entity_id: input_boolean.find_cheap_diesel
        to: "on"
    action:
      - service: notify.mobile_app
        data:
          message: "Navigate to cheapest diesel?"
          data:
            actions:
              - action: "NAVIGATE"
                title: "Navigate"
                uri: >
                  geo:{{ state_attr('sensor.ukfuelfinder_cheapest_b7', 'latitude') }},
                  {{ state_attr('sensor.ukfuelfinder_cheapest_b7', 'longitude') }}
```

#### Alert if supermarket station is cheapest

```yaml
automation:
  - alias: "Alert when supermarket has cheapest fuel"
    trigger:
      - platform: state
        entity_id: sensor.ukfuelfinder_cheapest_e10
    condition:
      - condition: template
        value_template: >
          {{ state_attr('sensor.ukfuelfinder_cheapest_e10', 'is_supermarket') == true }}
    action:
      - service: notify.mobile_app
        data:
          message: >
            Cheapest E10 is at supermarket: 
            {{ state_attr('sensor.ukfuelfinder_cheapest_e10', 'station_name') }}
```

### Example Dashboard Card

```yaml
type: entities
title: Nearby Fuel Stations
entities:
  - entity: sensor.ukfuelfinder_12345_unleaded
    name: Shell - Unleaded
  - entity: sensor.ukfuelfinder_12345_diesel
    name: Shell - Diesel
  - entity: sensor.ukfuelfinder_67890_unleaded
    name: BP - Unleaded
```

### Price History Graph

```yaml
type: history-graph
title: Fuel Price Trends
entities:
  - sensor.ukfuelfinder_12345_unleaded
  - sensor.ukfuelfinder_67890_unleaded
hours_to_show: 168
```

### Displaying Stations on the Map

Fuel stations can be displayed on the Home Assistant map with gas station icons (⛽). Add them to a map card:

**UI Method:**
1. Edit your map card (or create a new one)
2. Click "Add Entity"
3. Select a fuel price sensor (e.g., `sensor.ukfuelfinder_12345_unleaded`)
4. Set "Label mode" to "Icon"
5. Uncheck "Focus" (prevents zooming to the station)
6. Repeat for other stations

**YAML Method:**
```yaml
type: map
entities:
  - entity: sensor.ukfuelfinder_12345_unleaded
    label_mode: icon
    focus: false
  - entity: sensor.ukfuelfinder_12345_diesel
    label_mode: icon
    focus: false
  - entity: sensor.ukfuelfinder_67890_unleaded
    label_mode: icon
    focus: false
```

The stations will appear on the map with gas station icons at their actual locations.

## Troubleshooting

### Integration won't load

- Check Home Assistant logs for errors
- Verify API credentials are correct
- Ensure the `ukfuelfinder` Python library is installed

### No stations found

- Increase your search radius
- Verify location coordinates are correct
- Check if fuel stations exist in your area using the [Fuel Finder website](https://www.fuel-finder.service.gov.uk)

### Authentication errors

- Your credentials may have expired or been revoked
- Click the "Fix" button on the integration card to reauthenticate
- Verify your credentials at the [developer portal](https://www.developer.fuel-finder.service.gov.uk)

### Entities unavailable

- Check your internet connection
- Verify the API service is operational
- Check Home Assistant logs for specific error messages
- The integration will automatically retry on the next update cycle

### Changing settings

- To change location, radius, or update interval: Click "Configure" on the integration card
- To change API credentials: Click "Fix" when authentication fails, or remove and re-add the integration

## Data Attribution

Data provided by the UK Government Fuel Finder service under the [Open Government Licence v3.0](https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/).

## Testing

### Running Tests

The integration includes comprehensive unit and integration tests.

**Install test dependencies:**
```bash
pip install -r requirements-dev.txt
```

**Run all unit tests:**
```bash
pytest tests/ -v -k "not integration"
```

**Run specific test files:**
```bash
pytest tests/test_config_flow.py -v
pytest tests/test_coordinator.py -v
pytest tests/test_sensor.py -v
pytest tests/test_init.py -v
```

**Run integration tests (requires API credentials):**
```bash
export FUEL_FINDER_CLIENT_ID="your_client_id"
export FUEL_FINDER_CLIENT_SECRET="your_client_secret"
pytest tests/test_integration_simple.py -v
```

### Test Coverage

- **Config Flow**: User setup, reauthentication, reconfiguration
- **Coordinator**: API polling, error handling, auth failures
- **Sensors**: Entity creation, state updates, attributes
- **Integration**: Setup, unload, entry management
- **API Integration**: Real API calls, data validation

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## Support

- **Issues**: [GitHub Issues](https://github.com/mretallack/ukfuelfinder-ha/issues)
- **API Support**: [Contact Fuel Finder Team](https://www.developer.fuel-finder.service.gov.uk/contact-us)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Uses the [ukfuelfinder](https://github.com/mretallack/ukfuelfinder) Python library
- Data provided by the UK Government Fuel Finder service
