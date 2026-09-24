from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .api import KidsWatchClient


class KidsWatchLogin:
    """Handle KidsWatch authentication."""

    def __init__(self, client: "KidsWatchClient") -> None:
        self.client = client

    async def connect(self) -> bool:
        parameters = {
            "country_code": self.client.country_code,
            "phone_number": self.client.phone,
            "password": self.client.crypto.md5(self.client.password),
            "time_zone": self.client.time_zone,
            "user_lang": self.client.user_lang,
        }
        result = await self.client.request("login/postIndex", parameters, authenticated=False)

        if result.get("retcode") != 0:
            message = result.get("errmsg") or result.get("err_msg") or "KidsWatch login rejected."
            raise self.client.authentication_error(str(message))

        token = result.get("token")
        if not token:
            raise self.client.authentication_error("Login succeeded but no token was returned.")

        self.client.token = str(token)
        secret = result.get("secret")
        qid = result.get("qid")
        self.client.secret = "" if secret is None else str(secret)
        self.client.qid = "" if qid is None else str(qid)
        return True
