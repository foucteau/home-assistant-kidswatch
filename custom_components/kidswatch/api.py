from __future__ import annotations

import base64
import json
import logging
import time
from typing import Any

from aiohttp import ClientSession, ClientTimeout

from .crypto import KidsWatchCrypto
from .login import KidsWatchLogin
from .montre import KidsWatchMontre
from .parent import KidsWatchParent

_LOGGER = logging.getLogger(__name__)
API_VERSION = "0.1.8"


class KidsWatchError(Exception):
    """General KidsWatch error."""


class KidsWatchAuthenticationError(KidsWatchError):
    """KidsWatch authentication error."""


class KidsWatchProtocolError(KidsWatchError):
    """KidsWatch protocol error."""


class KidsWatchClient:
    """KidsWatch cloud API client."""

    BASE_URL = "https://m.kidswatch-eu.com/v2/"
    authentication_error = KidsWatchAuthenticationError
    protocol_error = KidsWatchProtocolError

    def __init__(
        self,
        session: ClientSession,
        phone: str,
        password: str,
        country_code: str = "+33",
        m2: str = "",
        time_zone: str = "UTC",
        user_lang: str = "en_US",
    ) -> None:
        self.session = session
        self.phone = phone.strip()
        self.password = password
        self.country_code = country_code.strip()
        self.m2 = m2.strip().lower()
        self.time_zone = time_zone
        self.user_lang = user_lang
        self.token = ""
        self.secret = ""
        self.qid = ""
        self.kids_data: dict[str, Any] = {}
        self.time_difference_ms = 0
        self.crypto = KidsWatchCrypto()
        self.login_api = KidsWatchLogin(self)
        self.montre = KidsWatchMontre(self)
        self.parent = KidsWatchParent(self)

    def _require_m2(self) -> None:
        if not self.m2:
            raise KidsWatchProtocolError("Missing m2 identifier.")

    def make_timestamp(self) -> str:
        return str(int(time.time() * 1000) + self.time_difference_ms)

    def make_id(self) -> str:
        self._require_m2()
        return self.crypto.md5(self.m2)

    def decode_response(self, response_text: str, seed: str, timestamp: str) -> dict[str, Any]:
        raw = response_text.strip()
        if not raw:
            raise KidsWatchProtocolError("Empty KidsWatch response.")

        try:
            result = json.loads(raw)
            if isinstance(result, dict):
                return result
        except json.JSONDecodeError:
            pass

        try:
            encrypted = base64.b64decode(raw, validate=True)
        except Exception as exc:
            raise KidsWatchProtocolError("KidsWatch response is neither JSON nor valid Base64.") from exc

        try:
            key = self.crypto.make_aes_key(
                m2=self.m2, seed=seed, timestamp=timestamp,
                token=self.token, secret=self.secret, qid=self.qid,
            )
            iv = self.crypto.make_aes_iv(
                m2=self.m2, seed=seed, timestamp=timestamp,
                token=self.token, secret=self.secret, qid=self.qid,
            )
            decrypted = self.crypto.aes_decrypt(encrypted, key, iv)
            result = json.loads(decrypted.decode("utf-8"))
        except Exception as exc:
            raise KidsWatchProtocolError("Unable to decode the KidsWatch response.") from exc

        if not isinstance(result, dict):
            raise KidsWatchProtocolError("Unexpected KidsWatch JSON response.")
        return result

    async def request(
        self,
        endpoint: str,
        parameters: dict[str, str] | None = None,
        *,
        authenticated: bool = True,
    ) -> dict[str, Any]:
        self._require_m2()
        if authenticated and not self.token:
            raise KidsWatchAuthenticationError("This request requires a KidsWatch session.")

        original_parameters = dict(parameters or {})
        timestamp = self.make_timestamp()
        seed = self.crypto.make_seed()
        original_parameters["ts"] = timestamp
        original_parameters["seed"] = seed
        original_parameters["m2"] = self.m2

        p = self.crypto.make_p(
            parameters=original_parameters,
            m2=self.m2,
            seed=seed,
            timestamp=timestamp,
            token=self.token if authenticated else "",
            secret=self.secret if authenticated else "",
            qid=self.qid if authenticated else "",
        )
        final_parameters = {
            "token": self.token if authenticated else "",
            "seed": seed,
            "id": self.make_id(),
            "ts": timestamp,
            "p": p,
        }
        headers = {
            "Accept-Language": self.user_lang.replace("_", "-"),
            "User-Agent": f"KidsWatchHomeAssistant/{API_VERSION}",
        }
        url = self.BASE_URL + endpoint.lstrip("/")
        _LOGGER.debug("KidsWatch request endpoint=%s authenticated=%s", endpoint, authenticated)

        try:
            async with self.session.get(
                url,
                params=final_parameters,
                headers=headers,
                timeout=ClientTimeout(total=30),
            ) as response:
                response_text = await response.text()
                if response.status != 200:
                    raise KidsWatchError(f"KidsWatch HTTP error {response.status}")
                result = self.decode_response(response_text, seed, timestamp)
                _LOGGER.debug(
                    "KidsWatch response endpoint=%s retcode=%s errcode=%s",
                    endpoint, result.get("retcode"), result.get("errcode"),
                )
                return result
        except (KidsWatchError, KidsWatchAuthenticationError, KidsWatchProtocolError):
            raise
        except Exception as exc:
            raise KidsWatchError(f"Unable to contact KidsWatch: {exc}") from exc

    async def login(self) -> bool:
        return await self.login_api.connect()

    async def get_kids(self) -> dict[str, Any]:
        return await self.montre.get_kids()

    async def refresh_kids(self) -> dict[str, Any]:
        result = await self.montre.get_kids()
        self.kids_data = result
        return result

    async def get_last_position(self, device_id: str) -> dict[str, Any]:
        return await self.montre.get_last_position(device_id)

    async def request_current_position(self, device_id: str) -> dict[str, Any]:
        return await self.montre.request_current_position(device_id)

    async def get_current_position(self, device_id: str) -> dict[str, Any]:
        return await self.request_current_position(device_id)

    async def get_week_steps(self, device_id: str) -> dict[str, Any]:
        return await self.montre.get_week_steps(device_id)
