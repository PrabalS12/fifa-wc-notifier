"""Map national-team names to flag image URLs (flagcdn.com) — reliable on any renderer.

Emoji flags don't render on Linux/Chromium, so the image card uses real flag PNGs.
"""

from __future__ import annotations

# ESPN display name -> ISO 3166-1 code used by flagcdn (home nations use gb-xxx).
_ISO = {
    "Mexico": "mx", "South Africa": "za", "South Korea": "kr", "Czechia": "cz",
    "Canada": "ca", "Bosnia-Herzegovina": "ba", "Switzerland": "ch", "Qatar": "qa",
    "United States": "us", "USA": "us", "Paraguay": "py", "Türkiye": "tr", "Turkey": "tr",
    "Australia": "au", "Brazil": "br", "Morocco": "ma", "Haiti": "ht", "Scotland": "gb-sct",
    "Germany": "de", "Curaçao": "cw", "Netherlands": "nl", "Japan": "jp", "Ivory Coast": "ci",
    "Ecuador": "ec", "Sweden": "se", "Tunisia": "tn", "Argentina": "ar", "France": "fr",
    "England": "gb-eng", "Wales": "gb-wls", "Spain": "es", "Portugal": "pt", "Belgium": "be",
    "Croatia": "hr", "Uruguay": "uy", "Colombia": "co", "Senegal": "sn", "Nigeria": "ng",
    "Egypt": "eg", "Ghana": "gh", "Cameroon": "cm", "Norway": "no", "Italy": "it",
    "Denmark": "dk", "Poland": "pl", "Serbia": "rs", "Iran": "ir", "Saudi Arabia": "sa",
    "Peru": "pe", "Chile": "cl", "Costa Rica": "cr", "Panama": "pa", "Jamaica": "jm",
    "Honduras": "hn", "Algeria": "dz", "Austria": "at", "Ukraine": "ua", "Greece": "gr",
    "New Zealand": "nz", "Venezuela": "ve", "Bolivia": "bo", "Cape Verde": "cv",
    "Jordan": "jo", "Uzbekistan": "uz", "South Sudan": "ss",
}


def flag_url(team: str, width: int = 80) -> str:
    """Return a flagcdn PNG URL for the team, or '' if unknown."""
    iso = _ISO.get(team)
    return f"https://flagcdn.com/w{width}/{iso}.png" if iso else ""
