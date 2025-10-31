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
        self.tz = tz
        self.lat = lat if isinstance(lat, float) else float(lat)
        self.lng = lng if isinstance(lng, float) else float(lng)

    def nowtz(self) -> datetime.datetime:
        """The current datetime object in a city's time zone."""
        return datetime.datetime.now(pytz.timezone(self.tz))

    def nowtz_text(self, fmt: str = DEFAULT_TIME_FORMAT) -> str:
        """The current time formatted text in a specified city's time zone."""
        return self.nowtz().strftime(fmt)

    def _get_suntimes(self) -> tuple[datetime.time, datetime.time]:
        """Determine sunrise or sunset time for a city"""
        sun = suntime.Sun(self.lat, self.lng)
        sunrise = sun.get_sunrise_time()
        sunset = sun.get_sunset_time()
        tz = pytz.timezone(self.tz)
        return sunrise.astimezone(tz).time(), sunset.astimezone(tz).time()

    @property
    def is_night(self) -> bool:
        """
        Determine if a city is in nighttime now. The sunset/sunrise/now
        variables are just times (no date info) so that you're not comparing
        things from different days
        """
        sunrise, sunset = self._get_suntimes()
        now = self.nowtz().time()
        return now < sunrise or now > sunset


class CityPrinter:
    @staticmethod
    def print(city: City, fmt: str, do_lat_lng: bool = False):
        """Generate the city info in a string for printing"""
        msg = CityPrinter._name_time(city, fmt)
        if do_lat_lng:
            msg += CityPrinter._latlng_fmt(city)
        if city.is_night:
            msg = colored(msg, "dark_grey")
        return msg

    @staticmethod
    def _name_time(city: City, fmt):
        """City name / time with formatting"""
        return f"{city.name:{fmt}s} {city.nowtz_text():{fmt}s}"

    @staticmethod
    def _latlng_fmt(city: City, fmt: str = "-7.2f") -> str:
        """City lat / lng with formatting"""
        return f"{city.lat:{fmt}} {city.lng:{fmt}}"


def all_cities(filename: str | Path) -> list[City]:
    """Cities sorted by longitude"""
    with open(filename) as file:
        cities = [City(*row) for row in csv.reader(file)]

    return sorted(cities, key=lambda c: c.lng)


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
    If possible, rotate the list so that home is first. If home is specified
    but not in the list of cities, do no rotation.
    """
    try:
        i = [c.name for c in cities].index(home)
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
    cities = all_cities(args.city_file)
    cities = filter_cities(cities, args.show_all, args.requested_cities)
    cities = rotate_list(cities, args.home_base)

    for city in cities:
        print(CityPrinter.print(city, args.column_width, args.lat_lng))


if __name__ == "__main__":
    main()
