"""Data update coordinator for UK Fuel Finder."""

from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

from homeassistant.const import CONF_CLIENT_ID, CONF_CLIENT_SECRET, CONF_LATITUDE, CONF_LONGITUDE
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import CONF_ENVIRONMENT, CONF_RADIUS, CONF_UPDATE_INTERVAL, DOMAIN

_LOGGER = logging.getLogger(__name__)


class UKFuelFinderCoordinator(DataUpdateCoordinator):
    """Class to manage fetching UK Fuel Finder data."""

    def __init__(self, hass: HomeAssistant, entry_data: dict[str, Any]) -> None:
        """Initialize coordinator."""
        self.entry_data = entry_data

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
            all_prices = await self.hass.async_add_executor_job(self.client.get_all_pfs_prices)

            # Build station data
            stations = {}

            for distance, station_info in nearby_stations:
                station_id = station_info.pfs_id

                # Get prices for this station
                station_prices = {}
                for price in all_prices:
                    if price.pfs_id == station_id:
                        fuel_type = price.fuel_type.lower().replace(" ", "_")
                        station_prices[fuel_type] = price.price

                stations[station_id] = {
                    "info": {
                        "id": station_id,
                        "trading_name": station_info.trading_name,
                        "address": station_info.address,
                        "brand": station_info.brand,
                        "latitude": station_info.latitude,
                        "longitude": station_info.longitude,
                        "phone": getattr(station_info, "phone", None),
                    },
                    "distance": distance,
                    "prices": station_prices,
                }

            return {"stations": stations}

        except Exception as err:
            if "authentication" in str(err).lower() or "unauthorized" in str(err).lower():
                raise ConfigEntryAuthFailed(f"Authentication failed: {err}") from err
            raise UpdateFailed(f"Error fetching data: {err}") from err
