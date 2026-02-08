"""Data update coordinator for UK Fuel Finder."""

from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

from homeassistant.const import CONF_CLIENT_ID, CONF_CLIENT_SECRET, CONF_LATITUDE, CONF_LONGITUDE
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import CONF_ENVIRONMENT, CONF_RADIUS, CONF_UPDATE_INTERVAL, DOMAIN

_LOGGER = logging.getLogger(__name__)


class UKFuelFinderCoordinator(DataUpdateCoordinator):
    """Class to manage fetching UK Fuel Finder data."""

    def __init__(self, hass: HomeAssistant, entry_data: dict[str, Any]) -> None:
        """Initialize coordinator."""
        self.entry_data = entry_data
        self.config_entry = None  # Set by __init__.py after coordinator creation
        self.previous_stations: set[str] = set()
        self.missing_stations: dict[str, int] = {}  # station_id -> missing_count

        from ukfuelfinder import FuelFinderClient

        self.client = FuelFinderClient(
            client_id=entry_data[CONF_CLIENT_ID],
            client_secret=entry_data[CONF_CLIENT_SECRET],
            environment=entry_data[CONF_ENVIRONMENT],
        )

        update_interval = timedelta(minutes=entry_data[CONF_UPDATE_INTERVAL])

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=update_interval,
        )

    def get_cheapest_fuel(self, fuel_type: str) -> dict[str, Any] | None:
        """Find the cheapest price for a given fuel type.
        
        Args:
            fuel_type: Fuel type to search for (e.g., "e10", "b7")
            
        Returns:
            Dictionary with station info and price, or None if no stations have this fuel type
        """
        if not self.data or "stations" not in self.data:
            return None
            
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

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from API."""
        try:
            # Fetch nearby stations
            nearby_stations = await self.hass.async_add_executor_job(
                self.client.search_by_location,
                self.entry_data[CONF_LATITUDE],
                self.entry_data[CONF_LONGITUDE],
                self.entry_data[CONF_RADIUS],
            )

            # Fetch all prices
            all_pfs = await self.hass.async_add_executor_job(self.client.get_all_pfs_prices)

            # Build station data
            stations = {}

            for distance, station_info in nearby_stations:
                station_id = station_info.node_id

                # Get prices for this station from PFS objects
                station_prices = {}
                for pfs in all_pfs:
                    if pfs.node_id == station_id:
                        for fuel_price in pfs.fuel_prices:
                            if fuel_price.price is not None:
                                fuel_type = fuel_price.fuel_type.lower().replace(" ", "_")
                                station_prices[fuel_type] = fuel_price.price

                # Build address string from location
                address_parts = []
                if station_info.location:
                    if station_info.location.address_line_1:
                        address_parts.append(station_info.location.address_line_1)
                    if station_info.location.city:
                        address_parts.append(station_info.location.city)
                    if station_info.location.postcode:
                        address_parts.append(station_info.location.postcode)
                address = ", ".join(address_parts) if address_parts else None

                stations[station_id] = {
                    "info": {
                        "id": station_id,
                        "trading_name": station_info.trading_name,
                        "address": address,
                        "brand": station_info.brand_name,
                        "latitude": (
                            station_info.location.latitude if station_info.location else None
                        ),
                        "longitude": (
                            station_info.location.longitude if station_info.location else None
                        ),
                        "phone": station_info.public_phone_number,
                        # Metadata fields
                        "is_supermarket": station_info.is_supermarket_service_station,
                        "is_motorway": station_info.is_motorway_service_station,
                        "amenities": station_info.amenities or [],
                        "opening_times": station_info.opening_times or {},
                        "fuel_types_available": station_info.fuel_types or [],
                        "organization_name": station_info.mft_organisation_name,
                        "temporary_closure": station_info.temporary_closure,
                        "permanent_closure": station_info.permanent_closure,
                    },
                    "distance": distance,
                    "prices": station_prices,
                }

            # Handle stale station removal with grace period
            current_stations = set(stations.keys())

            # Increment counter for stations still missing
            for station_id in list(self.missing_stations.keys()):
                if station_id not in current_stations:
                    self.missing_stations[station_id] += 1

            # Track newly disappeared stations
            newly_disappeared = (
                self.previous_stations - current_stations - set(self.missing_stations.keys())
            )
            for station_id in newly_disappeared:
                self.missing_stations[station_id] = 1

            # Reset count for stations that reappeared
            reappeared = current_stations & set(self.missing_stations.keys())
            for station_id in reappeared:
                del self.missing_stations[station_id]

            # Remove devices after 2 update cycles (grace period)
            if self.config_entry:
                device_registry = dr.async_get(self.hass)
                for station_id, missing_count in list(self.missing_stations.items()):
                    if missing_count >= 2:
                        device = device_registry.async_get_device(
                            identifiers={(DOMAIN, station_id)}
                        )
                        if device:
                            device_registry.async_update_device(
                                device_id=device.id,
                                remove_config_entry_id=self.config_entry.entry_id,
                            )
                            _LOGGER.info(
                                "Removed stale station %s after %d update cycles",
                                station_id,
                                missing_count,
                            )
                        del self.missing_stations[station_id]

            self.previous_stations = current_stations

            return {"stations": stations}

        except Exception as err:
            if "authentication" in str(err).lower() or "unauthorized" in str(err).lower():
                raise ConfigEntryAuthFailed(f"Authentication failed: {err}") from err
            raise UpdateFailed(f"Error fetching data: {err}") from err
