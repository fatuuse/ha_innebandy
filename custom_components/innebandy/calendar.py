"""Kalenderentitet för Innebandy – hall eller lag."""
from __future__ import annotations
import logging
from datetime import datetime, timedelta, timezone

from homeassistant.components.calendar import CalendarEntity, CalendarEvent
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    CONF_MONITOR_TYPE,
    CONF_TEAM_NAME,
    CONF_VENUE_NAME,
    DEFAULT_MATCH_DURATION,
    DOMAIN,
    MONITOR_TYPE_TEAM,
)
from .coordinator import InnebandyCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: InnebandyCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([InnebandyCalendar(coordinator, entry)])


class InnebandyCalendar(CoordinatorEntity[InnebandyCoordinator], CalendarEntity):
    _attr_has_entity_name = True

    def __init__(self, coordinator: InnebandyCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._entry = entry
        monitor_type = entry.data.get(CONF_MONITOR_TYPE, "venue")
        if monitor_type == MONITOR_TYPE_TEAM:
            display_name = entry.data.get(CONF_TEAM_NAME, "Lag")
            uid_key = entry.data.get("team_id", "")
        else:
            display_name = entry.data.get(CONF_VENUE_NAME, "Hall")
            uid_key = entry.data.get("venue_id", "")

        self._attr_name = display_name
        self._attr_unique_id = f"{DOMAIN}_calendar_{monitor_type}_{uid_key}"

    @property
    def event(self) -> CalendarEvent | None:
        live = self.coordinator.live_match
        if live and live.start_time:
            return self._to_event(live)
        nxt = self.coordinator.next_match
        return self._to_event(nxt) if nxt else None

    async def async_get_events(
        self, hass: HomeAssistant, start_date: datetime, end_date: datetime
    ) -> list[CalendarEvent]:
        events = []
        for m in (self.coordinator.data or []):
            if not m.is_valid or m.start_time is None:
                continue
            end = m.start_time + timedelta(seconds=DEFAULT_MATCH_DURATION)
            if end < start_date or m.start_time > end_date:
                continue
            events.append(self._to_event(m))
        return events

    @staticmethod
    def _to_event(m) -> CalendarEvent:
        start = m.start_time
        end = start + timedelta(seconds=DEFAULT_MATCH_DURATION)
        if start.tzinfo is None:
            start = start.replace(tzinfo=timezone.utc)
            end   = end.replace(tzinfo=timezone.utc)
        return CalendarEvent(
            start=start,
            end=end,
            summary=m.title,
            description=m.description,
            location=m.venue,
        )

    @property
    def extra_state_attributes(self) -> dict:
        live = self.coordinator.live_match
        nxt  = self.coordinator.next_match
        attrs: dict = {}
        if live:
            attrs["live_match"] = live.title
            attrs["live_score"] = (
                f"{live.goals_home}–{live.goals_away}"
                if live.goals_home is not None else "–"
            )
        if nxt:
            attrs["next_match"]       = nxt.title
            attrs["next_match_time"]  = nxt.start_time.isoformat() if nxt.start_time else None
            attrs["next_competition"] = nxt.competition
            attrs["next_venue"]       = nxt.venue
        attrs["upcoming_count"] = len(self.coordinator.upcoming_matches)
        return attrs
