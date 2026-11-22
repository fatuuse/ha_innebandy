# Innebandy för Home Assistant

Visar matcher för en innebandyhall eller ett lag från stats.innebandy.se som kalender i Home Assistant.

## Installation (HACS)
1. HACS → Integrationer → ⋮ → Anpassade arkiv → lägg till repot som *Integration*.
2. Installera **Innebandy** och starta om Home Assistant.
3. Inställningar → Enheter & tjänster → Lägg till integration → **Innebandy**.
4. Välj hall eller lag och ange ID från webbadressen på stats.innebandy.se, t.ex. hall `1254` (Ingarö Sporthall) eller lag `123976`.

## Vad den gör
- Kalenderentitet per hall eller lag med alla matcher för aktuell säsong.
- Attribut: pågående match, nästa match, antal kommande matcher.
- Uppdatering var 15:e minut, var 30:e sekund under pågående match.

## Begränsningar
- Lag-matchendpoint är inte verifierad mot live-data ännu.
- Tabell-, spelare- och målhändelse-sensorer ingår inte.
- Säsong är satt till 44 (2026/2027).
- Ej testad i en live Home Assistant-instans ännu.
