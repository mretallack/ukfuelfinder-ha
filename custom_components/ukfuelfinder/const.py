"""Constants for UK Fuel Finder integration."""

DOMAIN = "ukfuelfinder"

# Configuration keys
CONF_ENVIRONMENT = "environment"
CONF_RADIUS = "radius"
CONF_UPDATE_INTERVAL = "update_interval"

# Defaults
DEFAULT_ENVIRONMENT = "production"
DEFAULT_RADIUS = 5.0
DEFAULT_UPDATE_INTERVAL = 30

# Limits
MIN_RADIUS = 0.1
MAX_RADIUS = 50.0
MIN_UPDATE_INTERVAL = 5
MAX_UPDATE_INTERVAL = 1440

# Fuel types
FUEL_TYPES = [
    "unleaded",
    "super_unleaded",
    "diesel",
    "premium_diesel",
    "lpg",
]

# Attribution
ATTRIBUTION = "Data provided by UK Government Fuel Finder"
