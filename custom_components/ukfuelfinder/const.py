"""Constants for UK Fuel Finder integration."""

DOMAIN = "ukfuelfinder"

# Configuration keys
CONF_ENVIRONMENT = "environment"
CONF_RADIUS = "radius"
CONF_UPDATE_INTERVAL = "update_interval"
CONF_FUEL_TYPES = "fuel_types"

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
# Maps to API fuel type codes (normalized to lowercase with underscores)
# API returns: E10, E5, B7, B7_STANDARD, B7_PREMIUM, LPG, etc.
# We normalize to: e10, e5, b7, b7_standard, b7_premium, lpg
FUEL_TYPES = [
    "e10",           # Unleaded petrol (10% ethanol)
    "e5",            # Premium unleaded (5% ethanol) 
    "b7",            # Diesel (7% biodiesel)
    "b7_standard",   # Standard diesel
    "b7_premium",    # Premium diesel
    "lpg",           # Liquefied petroleum gas
]

# Attribution
ATTRIBUTION = "Data provided by UK Government Fuel Finder"
