from __future__ import annotations

from typing import Any

from homeassistant.components.device_tracker.config_entry import TrackerEntity
from homeassistant.components.device_tracker.const import SourceType
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import KidsWatchCoordinator


class KidsWatchTracker(CoordinatorEntity[KidsWatchCoordinator], TrackerEntity):
    """Represent a KidsWatch GPS position."""

    _attr_has_entity_name = True
    _attr_name = "Position"

    def __init__(self, coordinator: KidsWatchCoordinator, device_id: str, kid: dict[str, Any]) -> None:
        super().__init__(coordinator)
        self.device_id = device_id
        self.kid = kid
        self._attr_unique_id = f"{device_id}_position"

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self.device_id)},
            name=str(self.kid.get("nickname") or "KidsWatch"),
            manufacturer="KidsWatch",
            model=str(self.kid.get("device_type") or "KidsWatch"),
            sw_version=str(self.kid.get("ver") or ""),
        )

    @property
    def position(self) -> dict[str, Any]:
        return self.coordinator.data.get("positions", {}).get(self.device_id, {})

    @property
    def source_type(self) -> SourceType:
        return SourceType.GPS

    @property
    def latitude(self) -> float | None:
        try:
            value = self.position.get("lat")
            return None if value is None else float(value)
        except (TypeError, ValueError):
            return None

    @property
    def longitude(self) -> float | None:
        try:
            value = self.position.get("lng")
            return None if value is None else float(value)
        except (TypeError, ValueError):
            return None

    @property
    def location_accuracy(self) -> int:
        try:
            return int(self.position.get("rad") or 0)
        except (TypeError, ValueError):
            return 0

    @property
    def extra_state_attributes(self):
        pos = self.position
        return {
            "battery": pos.get("b_r"),
            "steps": pos.get("step"),
            "locate_time": pos.get("locate_time"),
            "locate_status": pos.get("locate_status"),
            "device_state": pos.get("device_state"),
            "city": pos.get("city"),
            "address": pos.get("addr"),
            "poi": pos.get("poi"),
            "is_indoor": pos.get("is_indoor"),
        }


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator: KidsWatchCoordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    async_add_entities([
        KidsWatchTracker(coordinator, device_id, kid)
        for device_id, kid in coordinator.data.get("kids", {}).items()
    ])
