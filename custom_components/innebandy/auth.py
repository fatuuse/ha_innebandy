"""Autentisering mot api.innebandy.se.

Flöde:
  1. GET  /auth/startkit   → accessToken (JWT, ingen auth krävs)
  2. POST /auth/handshake  → session-cookie + {ss, st, vf}
"""
from __future__ import annotations
import logging
import time
from datetime import datetime, timezone
from typing import Any

import aiohttp
from .const import HEADERS_FORM, HEADERS_JSON, IBIS_HANDSHAKE_URL, IBIS_STARTKIT_URL, TOKEN_EXPIRY_BUFFER

_LOGGER = logging.getLogger(__name__)
COOKIE_NAME = ".IbisApi.Session"


class IbisSession:
    def __init__(self) -> None:
        self.access_token: str = ""
        self.expires_at: float = 0.0
        self.session_secret: str = ""
        self.session_cookie: str = ""

    @property
    def is_expired(self) -> bool:
        return time.time() >= self.expires_at - TOKEN_EXPIRY_BUFFER

    @property
    def auth_header(self) -> str:
        return f"Bearer {self.access_token}"


class IbisAuth:
    def __init__(self, session: aiohttp.ClientSession) -> None:
        self._http = session
        self._ibis = IbisSession()

    async def async_ensure_token(self) -> IbisSession:
        if self._ibis.is_expired:
            await self._refresh()
        return self._ibis

    async def _refresh(self) -> None:
        token, exp = await self._startkit()
        self._ibis.access_token = token
        self._ibis.expires_at = exp
        await self._handshake()

    async def _startkit(self) -> tuple[str, float]:
        async with self._http.get(IBIS_STARTKIT_URL, headers=HEADERS_JSON) as resp:
            resp.raise_for_status()
            data: dict[str, Any] = await resp.json()
        exp_str: str = data["accessTokenExpiration"]
        exp_dt = datetime.fromisoformat(exp_str.replace("Z", "+00:00"))
        _LOGGER.debug("Startkit OK – exp %s", exp_str)
        return data["accessToken"], exp_dt.timestamp()

    async def _handshake(self) -> None:
        headers = {**HEADERS_FORM, "Authorization": self._ibis.auth_header}
        async with self._http.post(IBIS_HANDSHAKE_URL, headers=headers, data=b"") as resp:
            resp.raise_for_status()
            data: dict[str, Any] = await resp.json()
            raw = resp.headers.get("set-cookie", "")
            if COOKIE_NAME in raw:
                self._ibis.session_cookie = (
                    raw.split(f"{COOKIE_NAME}=")[1].split(";")[0]
                )
        self._ibis.session_secret = data.get("ss", "")
        _LOGGER.debug("Handshake OK – vf=%s", data.get("vf"))
