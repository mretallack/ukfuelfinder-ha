"""UK Fuel Finder integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_LATITUDE, CONF_LONGITUDE
from homeassistant.core import HomeAssistant

from .const import CONF_LOCATION_SOURCE, DOMAIN, LOCATION_SOURCE_STATIC
from .coordinator import UKFuelFinderCoordinator

PLATFORMS = ["sensor"]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up UK Fuel Finder from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    coordinator = UKFuelFinderCoordinator(hass, entry.data)
    coordinator.config_entry = entry  # Set reference for device removal

    # Set up location manager (defaults to static for existing installations)
    location_source = entry.data.get(CONF_LOCATION_SOURCE, LOCATION_SOURCE_STATIC)
    coordinator.setup_location_manager(
        location_source=location_source,
        fallback_lat=entry.data[CONF_LATITUDE],
        fallback_lon=entry.data[CONF_LONGITUDE],
    )

    await coordinator.async_config_entry_first_refresh()

    # Start listening for location changes (after first refresh)
    await coordinator.location_manager.async_start()

    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    coordinator = hass.data[DOMAIN].get(entry.entry_id)

    # Stop location manager listener
    if coordinator and coordinator.location_manager:
        await coordinator.location_manager.async_stop()

    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)

    return unload_ok
