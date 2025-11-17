"""Word Clock: print times of different cities to the terminal"""

import datetime
import json
from pathlib import Path
from typing import Any

import pytz
import suntime
from pydantic import BaseModel, ConfigDict, PrivateAttr

DEFAULT_TIME_FORMAT = "%H:%M %a %Z"


class City(BaseModel):
    """A city with time zone and lat/lng information."""

    id: int
    name: str
    tz: str
    lat: float
    lng: float
    country: str
    state: str

    model_config = ConfigDict(frozen=True)

    _tz: pytz.BaseTzInfo = PrivateAttr()
    _sun: suntime.Sun = PrivateAttr()

    def model_post_init(self, _context: Any) -> None:
        """Post-initialization to set up time zone and sun calculator."""
        self._tz = pytz.timezone(self.tz)
        self._sun = suntime.Sun(self.lat, self.lng)

    def nowtz(self) -> datetime.datetime:
        """The current datetime object in the city's time zone."""
        return datetime.datetime.now(self._tz)

    def nowtz_text(self, fmt: str = DEFAULT_TIME_FORMAT) -> str:
        """The current time formatted text in the city's time zone."""
        return self.nowtz().strftime(fmt)

    def _get_suntimes(self) -> tuple[datetime.time, datetime.time]:
        """Return today's local sunrise and sunset times (no date info)."""
        sunrise_utc = self._sun.get_sunrise_time()
        sunset_utc = self._sun.get_sunset_time()
        sunrise_local = sunrise_utc.astimezone(self._tz).time()
        sunset_local = sunset_utc.astimezone(self._tz).time()
        return sunrise_local, sunset_local

    @property
    def is_night(self) -> bool:
        """Return True if it's currently night in the city.

        Uses sunrise and sunset times. If sunrise/sunset cannot be
        computed (e.g. polar day/night), fall back to a crude heuristic:
        assume polar night in Northern Hemisphere winters.
        """
        now = self.nowtz()
        current_time = now.time()

        try:
            sunrise, sunset = self._get_suntimes()
            # Night if we're before sunrise or after sunset
            return current_time < sunrise or current_time > sunset
        except suntime.SunTimeException:
            # Very rough: between late autumn and early spring in the
            # Northern Hemisphere, assume polar night if we're north of equator.
            month = now.month
            winter_northern = month < 4 or month > 10  # between solstices
            return winter_northern and self.lat > 0


def load_cities(path: str | Path) -> dict[str, City]:
    """Yield City objects from a JSON file."""
    path = Path(path)
    data = json.loads(path.read_text())

    cities = {
        city.get("id"): City(
            name=city["name"],
            tz=city["timezone"],
            lat=city["lat"],
            lng=city["lng"],
            country=city["country"],
            state=city.get("state"),
            id=city.get("id"),
        )
        for city in data
    }
    return cities


def prepend_home_city(home: int, cities: list[int]) -> list[int]:
    """Prepend the home city to the list of cities, removing duplicates."""
    if home in cities:
        cities = [c for c in cities if c != home]
    return [home] + cities
