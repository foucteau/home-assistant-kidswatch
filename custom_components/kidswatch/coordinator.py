from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import KidsWatchClient

_LOGGER = logging.getLogger(__name__)
UPDATE_INTERVAL = timedelta(seconds=60)


class KidsWatchCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinate KidsWatch cloud updates."""

    def __init__(self, hass: HomeAssistant, client: KidsWatchClient) -> None:
        self.client = client
        self._update_cycle = 0
        super().__init__(hass, _LOGGER, name="KidsWatch", update_interval=UPDATE_INTERVAL)

    async def _async_update_data(self) -> dict[str, Any]:
        self._update_cycle += 1
        try:
            kids_result = await self.client.refresh_kids()
            if kids_result.get("retcode") != 0:
                raise UpdateFailed(f"parents/kids retcode={kids_result.get('retcode')}")

            kids_by_id: dict[str, dict[str, Any]] = {}
            positions: dict[str, dict[str, Any]] = {}
            for kid in kids_result.get("kids_list", []):
                if not isinstance(kid, dict):
                    continue
                device_id = str(kid.get("device_id") or "")
                if not device_id:
                    continue
                kids_by_id[device_id] = kid

                last_result = await self.client.get_last_position(device_id)
                device_pos = last_result.get("device_pos", [])
                position = None
                if isinstance(device_pos, list):
                    for item in device_pos:
                        if isinstance(item, dict) and str(item.get("device_id", "")) == device_id:
                            position = item
                            break
                    if position is None and device_pos and isinstance(device_pos[0], dict):
                        position = device_pos[0]
                if position is not None:
                    positions[device_id] = position

            _LOGGER.debug(
                "KidsWatch update cycle %s: %d watch(es), %d position(s)",
                self._update_cycle, len(kids_by_id), len(positions),
            )
            return {"kids": kids_by_id, "positions": positions}
        except UpdateFailed:
            raise
        except Exception as exc:
            raise UpdateFailed(f"KidsWatch update failed: {exc}") from exc
