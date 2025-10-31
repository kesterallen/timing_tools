"""
Word Clock: print times of different cities to the terminal
"""

from argparse import ArgumentParser
import csv
import datetime
from pathlib import Path

import pytz
import suntime
from termcolor import colored


DEFAULT_TIME_FORMAT = "%H:%M %a %Z"
SHORT_LIST_NAMES = ["Berkeley", "Copenhagen"]


class City:
    """A city with time zone and lat/lng information."""

    def __init__(self, name: str, tz: str, lat: float | str, lng: float | str) -> None:
        self.name = name
        self.tz = pytz.timezone(tz)
        self.lat = lat if isinstance(lat, float) else float(lat)
        self.lng = lng if isinstance(lng, float) else float(lng)

    def nowtz(self) -> datetime.datetime:
        """The current datetime object in a city's time zone."""
        return datetime.datetime.now(self.tz)

    def nowtz_text(self, fmt: str = DEFAULT_TIME_FORMAT) -> str:
        """The current time formatted text in a specified city's time zone."""
        return self.nowtz().strftime(fmt)

    def _get_suntimes(self) -> tuple[datetime.time, datetime.time]:
        """
        Determine sunrise or sunset time for a city

        The sunset/sunrise variables are datetime.times (no date info)
        because suntime seems to return the most recent sunrise or sunset (e.g.
        sunset will be yesterday).
        """
        sun = suntime.Sun(self.lat, self.lng)
        sunrise = sun.get_sunrise_time()
        sunset = sun.get_sunset_time()
        return sunrise.astimezone(self.tz).time(), sunset.astimezone(self.tz).time()

    @property
    def is_night(self) -> bool:
        """
        Determine if it is day or night in a city now.
        """
        sunrise, sunset = self._get_suntimes()
        now = self.nowtz().time()
        return now < sunrise or now > sunset

    def printstr(self, fmt: str, do_lat_lng: bool) -> str:
        """Generate the city info in a string for printing"""
        msg = self._name_time(fmt)
        if do_lat_lng:
            msg += self._latlng_fmt()
        if self.is_night:
            msg = colored(msg, "dark_grey")
        return msg

    def _name_time(self, fmt) -> str:
        """City name / time with formatting"""
        return f"{self.name:{fmt}s} {self.nowtz_text():{fmt}s}"

    def _latlng_fmt(self, fmt: str = "-7.2f") -> str:
        """City lat / lng with formatting"""
        return f"{self.lat:{fmt}} {self.lng:{fmt}}"


def load_cities(filename: str | Path, home_base: str) -> list[City]:
    """Cities sorted by longitude"""
    with open(filename) as file:
        cities = [City(*row) for row in csv.reader(file)]

    cities = sorted(cities, key=lambda c: c.lng)
    cities = rotate_list(cities, home_base)
    return cities


def filter_cities(
    cities: list[City], show_all: bool, requested_cities: list[str]
) -> list[City]:
    """
    Filter the list of cities to either be a) just the short list, b) just the
    specified cities, or c) everything if requested.
    """
    if show_all:
        filtered_cities = cities
    elif requested_cities:
        filtered_cities = [c for c in cities if c.name in requested_cities]
    else:
        filtered_cities = [c for c in cities if c.name in SHORT_LIST_NAMES]

    return filtered_cities


def rotate_list(cities: list[City], home: str) -> list[City]:
    """
    If possible, rotate the list so that the city named home (city.name == home)
    is first. If home is specified but not in the list of cities, return the list unchanged.
    """
    try:
        i = [i for i, c in enumerate(cities) if c.name.lower() == home.lower()][0]
        cities = cities[i:] + cities[:i]
    except ValueError:
        pass  # catch value error from .index if home is not in the list of names
    return cities


def parse_args():
    """Parse user arguments"""
    parser = ArgumentParser(
        prog="World Clock",
        description="Display city times and time zones",
    )
    parser.add_argument(
        "-a",
        "--show-all",
        action="store_true",
        default=False,
        help="Display times for all cities this program knows",
    )
    parser.add_argument(
        "-l",
        "--lat-lng",
        action="store_true",
        default=False,
        help="Display lat/lng coordinates for cities",
    )
    parser.add_argument(
        "-b",
        "--home-base",
        type=str,
        nargs="?",
        default="Berkeley",
        help="The name of your home city (will be displayed first).",
    )
    parser.add_argument(
        "-c",
        "--requested-cities",
        nargs="*",
        help="A list of cities to display (optional). Defaults to Berkeley and Copenhagen.",
    )
    parser.add_argument(
        "-w",
        "--column-width",
        type=int,
        nargs="?",
        default=20,
        help="Column print width.",
    )
    parser.add_argument(
        "-f",
        "--city-file",
        type=str,
        nargs="?",
        default=Path(__file__).parent / "worldclock_cities.csv",
        help="The path to a file with a CSV of Name/Timezone/Lat/Lng cities.",
    )
    return parser.parse_args()


def main():
    """Display the list"""
    args = parse_args()
    cities = load_cities(args.city_file, args.home_base)
    cities = filter_cities(cities, args.show_all, args.requested_cities)

    for city in cities:
        print(city.printstr(args.column_width, args.lat_lng))


if __name__ == "__main__":
    main()
