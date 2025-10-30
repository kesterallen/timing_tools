"""
Word Clock: print times of different cities to the terminal
"""

from argparse import ArgumentParser
import datetime

import pytz
import suntime
from termcolor import colored


SHORT_LIST_NAMES = ["Berkeley", "Copenhagen"]


class City:
    """A city with time zone and lat/lng information."""

    def __init__(self, name: str, tz: str, lat: float, lng: float) -> None:
        self.name = name
        self.tz = tz
        self.lat = lat
        self.lng = lng

    def str_fmt(self, fmt: str) -> str:
        """City name / time with formatting"""
        return f"{self.name:{fmt}} {self.nowtz_text():{fmt}}"

    def latlng_fmt(self, fmt: str) -> str:
        """City lat / lng with formatting"""
        return f"{self.lat:{fmt}} {self.lng:{fmt}}"

    def nowtz(self) -> datetime.datetime:
        """The current datetime object in a city's time zone."""
        return datetime.datetime.now(pytz.timezone(self.tz))

    def nowtz_text(self, fmt="%H:%M %a %Z") -> str:
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
        Determine if currently nighttime in a city. The sunset/sunrise/now
        variables are just times (no date info) so that you're not comparing
        things from different days
        """
        sunrise, sunset = self._get_suntimes()
        now = self.nowtz().time()
        return now < sunrise or now > sunset


def all_cities() -> list[City]:
    """Cities sorted by longitude"""
    cities = [
        City("Berkeley", "America/Los_Angeles", 37.8706606, -122.4657867),
        City("Honolulu", "Pacific/Honolulu", 21.3251912, -158.1307034),
        City("Mexico City", "America/Mexico_City", 19.3907336, -99.1436127),
        City("Milwaukee", "America/Chicago", 43.0576793, -88.1322139),
        City("Raleigh", "America/New_York", 35.8391044, -78.9745184),
        City("Azores", "Atlantic/Azores", 38.676345, -27.2990279),
        City("Copenhagen", "Europe/Copenhagen", 55.6708258, 12.2642021),
        City("Bucharest", "Europe/Bucharest", 44.4268, 26.1025),
        City("Tel Aviv", "Asia/Tel_Aviv", 32.0853, 34.7818),
        City("Moscow", "Europe/Moscow", 55.582026, 37.3855235),
        City("Bangalore", "Asia/Kolkata", 12.9539974, 77.6309395),
        City("Shanghai", "Asia/Shanghai", 31.2243489, 121.4767528),
        City("Tokyo", "Asia/Tokyo", 35.5092405, 139.7698121),
        City("Sydney", "Australia/Sydney", 33.8482439, 150.9319747),
        City("Auckland", "Pacific/Auckland", -36.8777976, 174.7566242),
    ]
    return sorted(cities, key=lambda c: c.lng)


def rotate_cities_list(cities: list[City], home: str) -> list[City]:
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


def filter_cities(
    cities: list[City], show_all: bool, requested_cities: list[str], home: str
) -> list[City]:
    """
    Filter the list of cities to either be a) just the short list, b) just the
    specified cities, or c) everything if requested.
    """
    filtered_cities = []
    # Sort by longitude and filter:
    for city in cities:
        # If just the short list of cities is being printed, skip others.
        # If a list of cities has been requested, skip cities not in that list.
        # The show_all argument overrules both of those options.
        if not show_all:
            if requested_cities and city.name not in requested_cities:
                continue
            if not requested_cities and city.name not in SHORT_LIST_NAMES:
                continue

        filtered_cities.append(city)

    filtered_cities = rotate_cities_list(filtered_cities, home)
    return filtered_cities


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
        "--home",
        type=str,
        nargs="?",
        default="Berkeley",
        help="The name of your home city (will be displayed first).",
    )
    parser.add_argument(
        "-c",
        "--cities",
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
    return parser.parse_args()


def main():
    """Display the list"""
    args = parse_args()
    cities = filter_cities(all_cities(), args.show_all, args.cities, args.home)
    for city in cities:
        msg = city.str_fmt(args.column_width)
        if args.lat_lng:
            msg += city.latlng_fmt("-7.2f")
        if city.is_night:
            msg = colored(msg, "dark_grey")
        print(msg)


if __name__ == "__main__":
    main()
