from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .api import KidsWatchClient


class KidsWatchParent:
    """Parent-account KidsWatch API calls."""

    def __init__(self, client: "KidsWatchClient") -> None:
        self.client = client

    async def get_messages(self) -> dict[str, Any]:
        return await self.client.request("parents/getmsg", {}, authenticated=True)

    async def get_subscribed_messages(self) -> dict[str, Any]:
        return await self.client.request("subscribed/allmessage", {}, authenticated=True)
