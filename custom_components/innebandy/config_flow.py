"""Config Flow för Innebandy – hall eller lag."""
from __future__ import annotations
import logging
from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import SelectSelector, SelectSelectorConfig, SelectSelectorMode

from .api import IbisApiClient
from .const import (
    CONF_MONITOR_TYPE,
    CONF_SEASON_ID,
    CONF_TEAM_ID,
    CONF_TEAM_NAME,
    CONF_VENUE_ID,
    CONF_VENUE_NAME,
    CURRENT_SEASON_ID,
    DOMAIN,
    MONITOR_TYPE_TEAM,
    MONITOR_TYPE_VENUE,
)

_LOGGER = logging.getLogger(__name__)


class InnebandyConfigFlow(ConfigFlow, domain=DOMAIN):
    """Config Flow: välj typ → ange ID → bekräfta."""

    VERSION = 1

    def __init__(self) -> None:
        self._monitor_type: str         = MONITOR_TYPE_VENUE
        self._venue_data: dict | None   = None
        self._venue_id: int | None      = None
        self._team_data: dict | None    = None
        self._team_id: int | None       = None

    # ── Steg 1: Välj typ ──────────────────────────────────────────
    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if user_input is not None:
            self._monitor_type = user_input[CONF_MONITOR_TYPE]
            if self._monitor_type == MONITOR_TYPE_TEAM:
                return await self.async_step_team()
            return await self.async_step_venue()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_MONITOR_TYPE, default=MONITOR_TYPE_VENUE): SelectSelector(
                    SelectSelectorConfig(
                        options=[
                            {"value": MONITOR_TYPE_VENUE, "label": "🏟️ Hall (alla matcher i hallen)"},
                            {"value": MONITOR_TYPE_TEAM,  "label": "👕 Lag (ett lags matcher)"},
                        ],
                        mode=SelectSelectorMode.LIST,
                    )
                ),
            }),
        )

    # ── Steg 2a: Ange hall-ID ─────────────────────────────────────
    async def async_step_venue(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            venue_id = user_input[CONF_VENUE_ID]
            await self.async_set_unique_id(f"venue_{venue_id}")
            self._abort_if_unique_id_configured()
            try:
                client = IbisApiClient(async_get_clientsession(self.hass))
                self._venue_data = await client.async_get_venue(venue_id)
                self._venue_id = venue_id
                return await self.async_step_confirm()
            except Exception:
                errors[CONF_VENUE_ID] = "cannot_connect"

        return self.async_show_form(
            step_id="venue",
            data_schema=vol.Schema({vol.Required(CONF_VENUE_ID): vol.Coerce(int)}),
            errors=errors,
            description_placeholders={
                "example": "1254",
                "url": "stats.innebandy.se/sasong/44/anlaggning/1254",
            },
        )

    # ── Steg 2b: Ange lag-ID ──────────────────────────────────────
    async def async_step_team(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            team_id = user_input[CONF_TEAM_ID]
            season_id = user_input.get(CONF_SEASON_ID, CURRENT_SEASON_ID)
            await self.async_set_unique_id(f"team_{team_id}_{season_id}")
            self._abort_if_unique_id_configured()
            try:
                client = IbisApiClient(async_get_clientsession(self.hass))
                self._team_data = await client.async_get_team(team_id, season_id)
                self._team_id = team_id
                return await self.async_step_confirm()
            except Exception:
                errors[CONF_TEAM_ID] = "cannot_connect"

        return self.async_show_form(
            step_id="team",
            data_schema=vol.Schema({
                vol.Required(CONF_TEAM_ID): vol.Coerce(int),
                vol.Optional(CONF_SEASON_ID, default=CURRENT_SEASON_ID): vol.Coerce(int),
            }),
            errors=errors,
            description_placeholders={
                "example": "123976",
                "url": "stats.innebandy.se/sasong/44/lag/123976",
            },
        )

    # ── Steg 3: Bekräfta ──────────────────────────────────────────
    async def async_step_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if user_input is not None:
            if self._monitor_type == MONITOR_TYPE_TEAM:
                return self._create_team_entry()
            return self._create_venue_entry()

        if self._monitor_type == MONITOR_TYPE_TEAM:
            assert self._team_data is not None
            td = self._team_data
            name = (
                td.get("TeamName") or td.get("Name") or f"Lag {self._team_id}"
            ).strip()
            placeholders = {
                "name":    name,
                "team_id": str(self._team_id),
                "extra":   td.get("CompetitionName", ""),
            }
        else:
            assert self._venue_data is not None
            vd = self._venue_data
            name = vd.get("Name", "").strip()
            placeholders = {
                "name":    name,
                "team_id": "",
                "extra":   f"{vd.get('Address','')}, {vd.get('City','')}",
            }

        return self.async_show_form(
            step_id="confirm",
            data_schema=vol.Schema({}),
            description_placeholders=placeholders,
        )

    def _create_venue_entry(self) -> ConfigFlowResult:
        assert self._venue_data is not None
        vd = self._venue_data
        name = vd.get("Name", "").strip()
        city = vd.get("City", "")
        return self.async_create_entry(
            title=f"🏟️ {name} ({city})" if city else f"🏟️ {name}",
            data={
                CONF_MONITOR_TYPE: MONITOR_TYPE_VENUE,
                CONF_VENUE_ID:     self._venue_id,
                CONF_VENUE_NAME:   name,
                CONF_SEASON_ID:    CURRENT_SEASON_ID,
            },
        )

    def _create_team_entry(self) -> ConfigFlowResult:
        assert self._team_data is not None
        td = self._team_data
        name = (td.get("TeamName") or td.get("Name") or f"Lag {self._team_id}").strip()
        return self.async_create_entry(
            title=f"👕 {name}",
            data={
                CONF_MONITOR_TYPE: MONITOR_TYPE_TEAM,
                CONF_TEAM_ID:      self._team_id,
                CONF_TEAM_NAME:    name,
                CONF_SEASON_ID:    CURRENT_SEASON_ID,
            },
        )
