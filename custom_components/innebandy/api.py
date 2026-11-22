"""API-klient mot api.innebandy.se."""
from __future__ import annotations
import logging
from datetime import datetime
from typing import Any

import aiohttp
from .auth import IbisAuth
from .const import (
    HEADERS_JSON,
    IBIS_TEAM_MATCHES_URL,
    IBIS_TEAM_URL,
    IBIS_VENUE_MATCHES_URL,
    IBIS_VENUE_URL,
    MATCH_STATUS_LIVE,
    NULL_DATE,
)

_LOGGER = logging.getLogger(__name__)


class Match:
    """Representerar en innebandymatch."""

    def __init__(self, raw: dict[str, Any]) -> None:
        self.match_id: int           = raw["MatchID"]
        self.status: int             = raw.get("MatchStatus", 1)
        self.competition: str        = raw.get("CompetitionName", "")
        self.round_name: str         = raw.get("RoundName", "")
        self.home_team: str          = raw.get("HomeTeam", "")
        self.away_team: str          = raw.get("AwayTeam", "")
        self.home_team_id: int       = raw.get("HomeTeamID", 0)
        self.away_team_id: int       = raw.get("AwayTeamID", 0)
        self.goals_home: int | None  = raw.get("GoalsHomeTeam")
        self.goals_away: int | None  = raw.get("GoalsAwayTeam")
        self.has_result: bool        = raw.get("HasFinalResult", False)
        self.cancelled: bool         = raw.get("Cancelled", False)
        self.postponed: bool         = raw.get("Postponed", False)
        self.abandoned: bool         = raw.get("Abandoned", False)
        self.time_missing: bool      = raw.get("MatchTimeMissing", False)
        self.venue: str              = raw.get("Venue", "").strip()
        self.venue_id: int           = raw.get("VenueID", 0)
        self.referee1: str           = raw.get("Referee1") or ""
        self.referee2: str           = raw.get("Referee2") or ""
        self.broadcast_url: str      = raw.get("BroadcastUrl", "")
        self.season_id: int          = raw.get("SeasonID", 0)

        raw_dt: str = raw.get("MatchDateTime", "")
        self.start_time: datetime | None = None
        if raw_dt and not raw_dt.startswith(NULL_DATE):
            try:
                self.start_time = datetime.fromisoformat(raw_dt)
            except ValueError:
                _LOGGER.debug("Kunde inte parsa datum: %s", raw_dt)

    @property
    def is_live(self) -> bool:
        return self.status == MATCH_STATUS_LIVE

    @property
    def is_valid(self) -> bool:
        return (
            self.start_time is not None
            and not self.cancelled
            and not self.time_missing
        )

    @property
    def title(self) -> str:
        home = self.home_team.strip()
        away = self.away_team.strip()
        if self.goals_home is not None and self.goals_away is not None:
            return f"{home} {self.goals_home}–{self.goals_away} {away}"
        return f"{home} vs {away}"

    @property
    def description(self) -> str:
        parts = [self.competition, self.round_name]
        if self.referee1:
            refs = self.referee1
            if self.referee2:
                refs += f", {self.referee2}"
            parts.append(f"Domare: {refs}")
        if self.broadcast_url:
            parts.append(f"Sändning: {self.broadcast_url}")
        if self.cancelled:
            parts.append("⚠️ Inställd")
        if self.postponed:
            parts.append("⚠️ Uppskjuten")
        return "\n".join(p for p in parts if p)


class IbisApiClient:
    def __init__(self, session: aiohttp.ClientSession) -> None:
        self._http = session
        self._auth = IbisAuth(session)

    async def _headers(self) -> dict[str, str]:
        ibis = await self._auth.async_ensure_token()
        return {**HEADERS_JSON, "Authorization": ibis.auth_header}

    async def _get_json(self, url: str) -> Any:
        """GET med auth, fallback utan."""
        headers = await self._headers()
        _LOGGER.debug("GET %s", url)
        async with self._http.get(url, headers=headers) as resp:
            _LOGGER.debug("→ HTTP %s", resp.status)
            if resp.status == 401:
                # Prova utan auth (publika endpoints)
                async with self._http.get(url, headers=HEADERS_JSON) as r2:
                    r2.raise_for_status()
                    return await r2.json()
            resp.raise_for_status()
            return await resp.json()

    # ------------------------------------------------------------------
    # Anläggning
    # ------------------------------------------------------------------
    async def async_get_venue(self, venue_id: int) -> dict[str, Any]:
        url = IBIS_VENUE_URL.format(venue_id=venue_id)
        return await self._get_json(url)

    async def async_get_venue_matches(
        self, venue_id: int, season_id: int
    ) -> list[Match]:
        url = IBIS_VENUE_MATCHES_URL.format(season_id=season_id, venue_id=venue_id)
        raw: list[dict] = await self._get_json(url)
        matches = [Match(m) for m in raw]
        matches.sort(key=lambda m: m.start_time or datetime.max)
        _LOGGER.debug("Hämtade %d matcher för venue %d", len(matches), venue_id)
        return matches

    # ------------------------------------------------------------------
    # Lag
    # ------------------------------------------------------------------
    async def async_get_team(self, team_id: int, season_id: int) -> dict[str, Any]:
        url = IBIS_TEAM_URL.format(season_id=season_id, team_id=team_id)
        return await self._get_json(url)

    async def async_get_team_matches(
        self, team_id: int, season_id: int
    ) -> list[Match]:
        url = IBIS_TEAM_MATCHES_URL.format(season_id=season_id, team_id=team_id)
        raw: list[dict] = await self._get_json(url)
        matches = [Match(m) for m in raw]
        matches.sort(key=lambda m: m.start_time or datetime.max)
        _LOGGER.debug("Hämtade %d matcher för team %d", len(matches), team_id)
        return matches
