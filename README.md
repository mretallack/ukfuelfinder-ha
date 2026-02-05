# UK Fuel Finder for Home Assistant

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/custom-components/hacs)

A Home Assistant custom component that integrates with the UK Government Fuel Finder API to monitor fuel prices at nearby petrol stations.

## Features

- 🔍 **Automatic Station Discovery** - Finds fuel stations within your specified radius
- 💰 **Real-time Price Monitoring** - Track fuel prices for multiple fuel types
- 📊 **Historical Data** - Graph price trends over time
- 🗺️ **Map Integration** - View stations on your Home Assistant map
- 🔄 **Automatic Updates** - Configurable update intervals (5-1440 minutes)
- 🔐 **Secure Credential Management** - Easy reauthentication when credentials change
- ⚙️ **Reconfigurable** - Change location and settings without re-adding

## Supported Fuel Types

- Unleaded Petrol (E10)
- Super Unleaded Petrol
- Diesel
- Premium Diesel
- LPG

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

## Usage

### Entities

The integration creates sensor entities for each fuel type at each station:

- **Entity ID Format**: `sensor.ukfuelfinder_{station_id}_{fuel_type}`
- **State**: Fuel price in pence (GBp)
- **Attributes**:
  - Station name
  - Brand
  - Address
  - Distance from home (km)
  - Latitude and longitude
  - Phone number
  - Fuel type

### Example Automation

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
          message: >
            Fuel price dropped to {{ states('sensor.ukfuelfinder_12345_unleaded') }}p
            at {{ state_attr('sensor.ukfuelfinder_12345_unleaded', 'station_name') }}
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
