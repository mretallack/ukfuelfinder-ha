"""Sensor platform for UK Fuel Finder."""

from __future__ import annotations

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import ATTRIBUTION, DOMAIN
from .coordinator import UKFuelFinderCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up UK Fuel Finder sensors."""
    coordinator: UKFuelFinderCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities = []

    if coordinator.data and "stations" in coordinator.data:
        for station_id, station_data in coordinator.data["stations"].items():
            for fuel_type, price in station_data["prices"].items():
                entities.append(
                    UKFuelFinderSensor(
                        coordinator,
                        station_id,
                        fuel_type,
                        station_data,
                    )
                )

    async_add_entities(entities)


class UKFuelFinderSensor(CoordinatorEntity[UKFuelFinderCoordinator], SensorEntity):
    """Representation of a UK Fuel Finder sensor."""

    _attr_has_entity_name = True
    _attr_device_class = SensorDeviceClass.MONETARY
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = "GBP"

    def __init__(
        self,
        coordinator: UKFuelFinderCoordinator,
        station_id: str,
        fuel_type: str,
        station_data: dict,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)

        self._station_id = station_id
        self._fuel_type = fuel_type
        self._attr_unique_id = f"{station_id}_{fuel_type}"

        # Set entity name to fuel type
        self._attr_name = fuel_type.replace("_", " ").title()

        # Device info for grouping
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, station_id)},
            name=station_data["info"]["trading_name"],
            manufacturer=station_data["info"]["brand"],
            model="Fuel Station",
        )

    @property
    def native_value(self) -> float | None:
        """Return the state of the sensor in pounds."""
        if not self.coordinator.data or "stations" not in self.coordinator.data:
            return None

        station = self.coordinator.data["stations"].get(self._station_id)
        if not station:
            return None

        price_pence = station["prices"].get(self._fuel_type)
        if price_pence is None:
            return None

        # Convert pence to pounds
        return round(price_pence / 100, 3)

    @property
    def extra_state_attributes(self) -> dict[str, any]:
        """Return additional attributes."""
        if not self.coordinator.data or "stations" not in self.coordinator.data:
            return {}

        station = self.coordinator.data["stations"].get(self._station_id)
        if not station:
            return {}

        info = station["info"]
        price_pence = station["prices"].get(self._fuel_type)

        return {
            "station_name": info["trading_name"],
            "brand": info["brand"],
            "address": info["address"],
            "distance_km": round(station["distance"], 2),
            "latitude": info["latitude"],
            "longitude": info["longitude"],
            "phone": info.get("phone"),
            "fuel_type": self._fuel_type,
            "price_pence": price_pence,
            "attribution": ATTRIBUTION,
        }

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        if not super().available:
            return False

        if not self.coordinator.data or "stations" not in self.coordinator.data:
            return False

        station = self.coordinator.data["stations"].get(self._station_id)
        return station is not None and self._fuel_type in station.get("prices", {})
