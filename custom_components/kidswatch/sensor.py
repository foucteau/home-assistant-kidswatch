from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, UnitOfLength
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo, EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import KidsWatchCoordinator


def _device_info(kid: dict[str, Any]) -> DeviceInfo:
    device_id = str(kid.get("device_id", ""))
    return DeviceInfo(
        identifiers={(DOMAIN, device_id)},
        name=str(kid.get("nickname") or "KidsWatch"),
        manufacturer="KidsWatch",
        model=str(kid.get("device_type") or "KidsWatch"),
        sw_version=str(kid.get("ver") or ""),
    )


class KidsWatchSensorBase(CoordinatorEntity[KidsWatchCoordinator], SensorEntity):
    _attr_has_entity_name = True

    def __init__(self, coordinator: KidsWatchCoordinator, device_id: str, kid: dict[str, Any]) -> None:
        super().__init__(coordinator)
        self.device_id = device_id
        self.kid = kid

    @property
    def device_info(self) -> DeviceInfo:
        return _device_info(self.kid)

    @property
    def position(self) -> dict[str, Any]:
        return self.coordinator.data.get("positions", {}).get(self.device_id, {})


class KidsWatchBatterySensor(KidsWatchSensorBase):
    _attr_name = "Batterie"
    _attr_device_class = SensorDeviceClass.BATTERY
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator, device_id, kid):
        super().__init__(coordinator, device_id, kid)
        self._attr_unique_id = f"{device_id}_battery"

    @property
    def native_value(self):
        return self.position.get("b_r")


class KidsWatchStepsSensor(KidsWatchSensorBase):
    _attr_name = "Pas"
    _attr_native_unit_of_measurement = "pas"
    _attr_state_class = SensorStateClass.TOTAL

    def __init__(self, coordinator, device_id, kid):
        super().__init__(coordinator, device_id, kid)
        self._attr_unique_id = f"{device_id}_steps"

    @property
    def native_value(self):
        return self.position.get("step")


class KidsWatchAccuracySensor(KidsWatchSensorBase):
    _attr_name = "Précision GPS"
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_device_class = SensorDeviceClass.DISTANCE
    _attr_native_unit_of_measurement = UnitOfLength.METERS
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator, device_id, kid):
        super().__init__(coordinator, device_id, kid)
        self._attr_unique_id = f"{device_id}_gps_accuracy"

    @property
    def native_value(self):
        return self.position.get("rad")


class KidsWatchLatitudeSensor(KidsWatchSensorBase):
    _attr_name = "Latitude"

    def __init__(self, coordinator, device_id, kid):
        super().__init__(coordinator, device_id, kid)
        self._attr_unique_id = f"{device_id}_latitude"

    @property
    def native_value(self):
        try:
            value = self.position.get("lat")
            return None if value is None else float(value)
        except (TypeError, ValueError):
            return None


class KidsWatchLongitudeSensor(KidsWatchSensorBase):
    _attr_name = "Longitude"

    def __init__(self, coordinator, device_id, kid):
        super().__init__(coordinator, device_id, kid)
        self._attr_unique_id = f"{device_id}_longitude"

    @property
    def native_value(self):
        try:
            value = self.position.get("lng")
            return None if value is None else float(value)
        except (TypeError, ValueError):
            return None


class KidsWatchAddressSensor(KidsWatchSensorBase):
    _attr_name = "Adresse"

    def __init__(self, coordinator, device_id, kid):
        super().__init__(coordinator, device_id, kid)
        self._attr_unique_id = f"{device_id}_address"

    @property
    def native_value(self):
        return self.position.get("addr") or self.position.get("poi") or self.position.get("city")

    @property
    def extra_state_attributes(self):
        pos = self.position
        return {"city": pos.get("city"), "poi": pos.get("poi"), "is_indoor": pos.get("is_indoor")}


class KidsWatchLastLocateSensor(KidsWatchSensorBase):
    _attr_name = "Dernière localisation"
    _attr_device_class = SensorDeviceClass.TIMESTAMP

    def __init__(self, coordinator, device_id, kid):
        super().__init__(coordinator, device_id, kid)
        self._attr_unique_id = f"{device_id}_last_locate"

    @property
    def native_value(self):
        value = self.position.get("locate_time")
        if value in (None, ""):
            return None
        try:
            return datetime.fromtimestamp(int(value), tz=timezone.utc)
        except (TypeError, ValueError, OSError):
            return None


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator: KidsWatchCoordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    entities: list[SensorEntity] = []
    for device_id, kid in coordinator.data.get("kids", {}).items():
        entities.extend([
            KidsWatchBatterySensor(coordinator, device_id, kid),
            KidsWatchStepsSensor(coordinator, device_id, kid),
            KidsWatchAccuracySensor(coordinator, device_id, kid),
            KidsWatchLatitudeSensor(coordinator, device_id, kid),
            KidsWatchLongitudeSensor(coordinator, device_id, kid),
            KidsWatchAddressSensor(coordinator, device_id, kid),
            KidsWatchLastLocateSensor(coordinator, device_id, kid),
        ])
    async_add_entities(entities)
