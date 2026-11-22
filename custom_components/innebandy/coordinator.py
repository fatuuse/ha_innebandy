"""DataUpdateCoordinator för Innebandy."""
from __future__ import annotations
import logging
from datetime import datetime, timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import IbisApiClient, Match
from .const import (
    CONF_MONITOR_TYPE,
    CONF_SEASON_ID,
    CONF_TEAM_ID,
    CONF_VENUE_ID,
    CURRENT_SEASON_ID,
    DOMAIN,
    MATCH_STATUS_FINISHED,
    MONITOR_TYPE_TEAM,
    MONITOR_TYPE_VENUE,
    SCAN_INTERVAL_DEFAULT,
    SCAN_INTERVAL_LIVE,
)

_LOGGER = logging.getLogger(__name__)


class InnebandyCoordinator(DataUpdateCoordinator[list[Match]]):

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self._monitor_type: str = entry.data.get(CONF_MONITOR_TYPE, MONITOR_TYPE_VENUE)
        self._venue_id: int     = entry.data.get(CONF_VENUE_ID, 0)
        self._team_id: int      = entry.data.get(CONF_TEAM_ID, 0)
        self._season_id: int    = entry.data.get(CONF_SEASON_ID, CURRENT_SEASON_ID)
        self._client            = IbisApiClient(async_get_clientsession(hass))

        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{self._monitor_type}_{self._venue_id or self._team_id}",
            update_interval=timedelta(seconds=SCAN_INTERVAL_DEFAULT),
        )

    async def _async_update_data(self) -> list[Match]:
        try:
            if self._monitor_type == MONITOR_TYPE_TEAM:
                matches = await self._client.async_get_team_matches(
                    self._team_id, self._season_id
                )
            else:
                matches = await self._client.async_get_venue_matches(
                    self._venue_id, self._season_id
                )
        except Exception as err:
            raise UpdateFailed(f"Fel vid hämtning: {err}") from err

        is_live = any(m.is_live for m in matches)
        new_interval = timedelta(
            seconds=SCAN_INTERVAL_LIVE if is_live else SCAN_INTERVAL_DEFAULT
        )
        if new_interval != self.update_interval:
            self.update_interval = new_interval
            _LOGGER.debug("Intervall → %s sek", new_interval.total_seconds())

        return matches

    @property
    def upcoming_matches(self) -> list[Match]:
        now = datetime.now()
        return [
            m for m in (self.data or [])
            if m.is_valid
            and not m.has_result
            and m.status != MATCH_STATUS_FINISHED
            and m.start_time is not None
            and m.start_time >= now
        ]

    @property
    def past_matches(self) -> list[Match]:
        return [m for m in (self.data or []) if m.has_result or m.status == MATCH_STATUS_FINISHED]

    @property
    def live_match(self) -> Match | None:
        return next((m for m in (self.data or []) if m.is_live), None)

    @property
    def next_match(self) -> Match | None:
        upcoming = self.upcoming_matches
        return upcoming[0] if upcoming else None
