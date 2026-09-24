"""Sensor platform for UK Fuel Finder."""

from __future__ import annotations

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import ATTRIBUTION, CONF_FUEL_TYPES, DOMAIN, FUEL_TYPES
from .coordinator import UKFuelFinderCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up UK Fuel Finder sensors."""
    coordinator: UKFuelFinderCoordinator = hass.data[DOMAIN][entry.entry_id]

    known_sensors: set[tuple[str, str]] = set()

    def _check_new_stations() -> None:
        """Check for new stations and create sensors."""
        if not coordinator.data or "stations" not in coordinator.data:
            return

        # Get selected fuel types from config (default to all for backward compatibility)
        selected_fuel_types = entry.data.get(CONF_FUEL_TYPES, FUEL_TYPES)

        new_entities = []

        # Create regular station sensors (filtered by fuel type)
        for station_id, station_data in coordinator.data["stations"].items():
            for fuel_type in station_data["prices"].keys():
                # Skip unselected fuel types
                if fuel_type not in selected_fuel_types:
                    continue

                sensor_key = (station_id, fuel_type)
                if sensor_key not in known_sensors:
                    known_sensors.add(sensor_key)
                    new_entities.append(
                        UKFuelFinderSensor(
                            coordinator,
                            station_id,
                            fuel_type,
                            station_data,
                        )
                    )

        # Create cheapest sensors (one per selected fuel type)
        for fuel_type in selected_fuel_types:
            sensor_key = ("cheapest", fuel_type)
            if sensor_key not in known_sensors:
                known_sensors.add(sensor_key)
                new_entities.append(UKFuelFinderCheapestSensor(coordinator, fuel_type))

        if new_entities:
            async_add_entities(new_entities)

    _check_new_stations()
    entry.async_on_unload(coordinator.async_add_listener(_check_new_stations))


class UKFuelFinderSensor(CoordinatorEntity[UKFuelFinderCoordinator], SensorEntity):
    """Representation of a UK Fuel Finder sensor."""

    _attr_has_entity_name = True
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = "GBP"
    _attr_suggested_display_precision = 2
    _attr_icon = "mdi:gas-station"

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
        price_timestamp = station.get("price_timestamps", {}).get(self._fuel_type)

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
            "price_last_updated": price_timestamp.isoformat() if price_timestamp else None,
            # Metadata fields
            "is_supermarket": info.get("is_supermarket"),
            "is_motorway": info.get("is_motorway"),
            "amenities": info.get("amenities", []),
            "opening_times": info.get("opening_times", {}),
            "fuel_types_available": info.get("fuel_types_available", []),
            "organization_name": info.get("organization_name"),
            "temporary_closure": info.get("temporary_closure"),
            "permanent_closure": info.get("permanent_closure"),
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
        """Return the cheapest price in pounds."""
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
            "price_last_updated": cheapest.get("price_last_updated"),
            "station_id": cheapest["station_id"],
            # Metadata fields
            "is_supermarket": cheapest.get("is_supermarket"),
            "is_motorway": cheapest.get("is_motorway"),
            "amenities": cheapest.get("amenities", []),
            "opening_times": cheapest.get("opening_times", {}),
            "fuel_types_available": cheapest.get("fuel_types_available", []),
            "organization_name": cheapest.get("organization_name"),
            "temporary_closure": cheapest.get("temporary_closure"),
            "permanent_closure": cheapest.get("permanent_closure"),
            "attribution": ATTRIBUTION,
        }

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        if not super().available:
            return False

        # Sensor is available if we can find at least one station with this fuel type
        cheapest = self.coordinator.get_cheapest_fuel(self._fuel_type)
        return cheapest is not None
