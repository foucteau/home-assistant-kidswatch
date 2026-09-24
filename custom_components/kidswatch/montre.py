from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .api import KidsWatchClient


class KidsWatchMontre:
    """Watch-related KidsWatch API calls."""

    def __init__(self, client: "KidsWatchClient") -> None:
        self.client = client

    async def get_kids(self) -> dict[str, Any]:
        return await self.client.request("parents/kids", {}, authenticated=True)

    async def get_last_position(self, device_id: str) -> dict[str, Any]:
        return await self.client.request(
            "kids/lastpos", {"device_id": str(device_id)}, authenticated=True
        )

    async def request_current_position(self, device_id: str) -> dict[str, Any]:
        return await self.client.request(
            "kids/currentpos", {"device_id": str(device_id)}, authenticated=True
        )

    async def get_current_position(self, device_id: str) -> dict[str, Any]:
        return await self.request_current_position(device_id)

    async def get_week_steps(self, device_id: str) -> dict[str, Any]:
        return await self.client.request(
            "kids/weekstep", {"device_id": str(device_id)}, authenticated=True
        )
