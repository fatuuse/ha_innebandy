"""Konstanter för Innebandy-integrationen."""

DOMAIN   = "innebandy"
VERSION  = "0.0.2"

# ------------------------------------------------------------------
# Konfigurationsnycklar
# ------------------------------------------------------------------
CONF_MONITOR_TYPE = "monitor_type"
CONF_VENUE_ID     = "venue_id"
CONF_VENUE_NAME   = "venue_name"
CONF_TEAM_ID      = "team_id"
CONF_TEAM_NAME    = "team_name"
CONF_SEASON_ID    = "season_id"

MONITOR_TYPE_VENUE = "venue"
MONITOR_TYPE_TEAM  = "team"

# ------------------------------------------------------------------
# HTTP-headers
# ------------------------------------------------------------------
USER_AGENT = (
    f"HomeAssistant-Innebandy/{VERSION} "
    "(+https://github.com/fatuuse/ha_innebandy)"
)

HEADERS_JSON = {
    "User-Agent": USER_AGENT,
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "sv-SE,sv;q=0.8,en-US;q=0.5,en;q=0.3",
    "Content-Type": "application/json",
}

HEADERS_FORM = {
    "User-Agent": USER_AGENT,
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "sv-SE,sv;q=0.8,en-US;q=0.5,en;q=0.3",
    "Content-Type": "application/x-www-form-urlencoded",
}

# ------------------------------------------------------------------
# API-endpoints
# ------------------------------------------------------------------
IBIS_API_BASE = "https://api.innebandy.se/v2/api"

CURRENT_SEASON_ID = 44

# Auth
IBIS_STARTKIT_URL  = f"{IBIS_API_BASE}/auth/startkit"
IBIS_HANDSHAKE_URL = f"{IBIS_API_BASE}/auth/handshake"
TOKEN_EXPIRY_BUFFER = 120  # sek innan token-utgång då den förnyas

# Anläggning (bekräftad)
IBIS_VENUE_URL = f"{IBIS_API_BASE}/public/venues/{{venue_id}}"
IBIS_VENUE_MATCHES_URL = (
    f"{IBIS_API_BASE}/public/seasons/{{season_id}}/venues/{{venue_id}}/matches"
)

# Lag (bekräftad info, matches-endpoint ej bekräftad – samma mönster)
IBIS_TEAM_URL = (
    f"{IBIS_API_BASE}/public/seasons/{{season_id}}/teams/{{team_id}}"
)
IBIS_TEAM_MATCHES_URL = (
    f"{IBIS_API_BASE}/public/seasons/{{season_id}}/teams/{{team_id}}/matches"
)

# Övrigt
IBIS_SEARCH_URL = f"{IBIS_API_BASE}/public/search"

# ------------------------------------------------------------------
# Matchstatus
# ------------------------------------------------------------------
MATCH_STATUS_SCHEDULED = 1
MATCH_STATUS_LIVE      = 3
MATCH_STATUS_FINISHED  = 4

# ------------------------------------------------------------------
# Intervall (sek)
# ------------------------------------------------------------------
SCAN_INTERVAL_DEFAULT = 15 * 60
SCAN_INTERVAL_LIVE    = 30

DEFAULT_MATCH_DURATION = 90 * 60   # 90 min

NULL_DATE = "0001-01-01"
