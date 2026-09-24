from __future__ import annotations

import asyncio
import logging
from typing import Any

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo

from .const import DOMAIN
from .coordinator import KidsWatchCoordinator

_LOGGER = logging.getLogger(__name__)
POLL_INTERVAL_SECONDS = 3
MAX_WAIT_SECONDS = 45


def _extract_position(response: dict[str, Any], device_id: str) -> dict[str, Any] | None:
    device_pos = response.get("device_pos", [])
    if not isinstance(device_pos, list):
        return None
    for item in device_pos:
        if isinstance(item, dict) and str(item.get("device_id", "")) == device_id:
            return item
    if device_pos and isinstance(device_pos[0], dict):
        return device_pos[0]
    return None


class KidsWatchRefreshPositionButton(ButtonEntity):
    """Request a fresh watch position."""

    _attr_has_entity_name = True
    _attr_name = "Actualiser la position"
    _attr_icon = "mdi:crosshairs-gps"

    def __init__(self, coordinator: KidsWatchCoordinator, device_id: str, kid: dict[str, Any]) -> None:
        self.coordinator = coordinator
        self.device_id = device_id
        self._attr_unique_id = f"{device_id}_refresh_position"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, device_id)},
            name=kid.get("nickname") or "KidsWatch",
            manufacturer="KidsWatch",
            model=str(kid.get("device_type") or "KidsWatch"),
            sw_version=kid.get("ver") or kid.get("firmware_version") or kid.get("firmware"),
        )

    async def async_press(self) -> None:
        previous_position = self.coordinator.data.get("positions", {}).get(self.device_id, {})
        previous_locate_time = previous_position.get("locate_time")

        response = await self.coordinator.client.request_current_position(self.device_id)
        _LOGGER.debug(
            "KidsWatch current-position request returned retcode=%s errcode=%s",
            response.get("retcode"), response.get("errcode"),
        )

        attempts = MAX_WAIT_SECONDS // POLL_INTERVAL_SECONDS
        for attempt in range(1, attempts + 1):
            await asyncio.sleep(POLL_INTERVAL_SECONDS)
            last_result = await self.coordinator.client.get_last_position(self.device_id)
            position = _extract_position(last_result, self.device_id)
            new_locate_time = position.get("locate_time") if position else None
            if (
                position is not None
                and new_locate_time is not None
                and str(new_locate_time) != str(previous_locate_time)
            ):
                _LOGGER.debug(
                    "KidsWatch fresh position received after about %ss",
                    attempt * POLL_INTERVAL_SECONDS,
                )
                await self.coordinator.async_request_refresh()
                return

        _LOGGER.debug("KidsWatch no fresh position after %ss", MAX_WAIT_SECONDS)
        await self.coordinator.async_request_refresh()


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities
) -> None:
    coordinator: KidsWatchCoordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    async_add_entities([
        KidsWatchRefreshPositionButton(coordinator, device_id, kid)
        for device_id, kid in coordinator.data.get("kids", {}).items()
    ])
