"""
Word Clock: print times of different cities to the terminal
"""

from argparse import ArgumentParser
from collections import namedtuple
import datetime
import tzlocal

import pytz
import suntime
from termcolor import colored

City = namedtuple("City", "name tz lat lng")

BASE_NAME = "Berkeley"
BASE_TZ = tzlocal.get_localzone_name()  # "America/Los_Angeles"
BASE_LAT = 37.8706606
BASE_LNG = -122.4657867
BASE_CITY = City(BASE_NAME, BASE_TZ, BASE_LAT, BASE_LNG)

SHORT_LIST_NAMES = [BASE_NAME, "Copenhagen"]


def parse_args():
    """Parse user arguments"""
    parser = ArgumentParser(
        prog="World Clock",
        description="Display city times and time zones",
    )
    parser.add_argument(
        "-a",
        "--print-all",
        action="store_true",
        default=False,
        help="Display times for all cities this program knows",
    )
    parser.add_argument(
        "-c",
        "--cities",
        nargs="*",
        help="A list of cities to display (optional). Defaults to Berkeley and Copenhagen.",
    )
    return parser.parse_args()


def nowtz(city: City) -> datetime.datetime:
    """The current time object in a city's time zone."""
    current_time = datetime.datetime.now(pytz.timezone(city.tz))
    return current_time


def nowtz_text(city: City, fmt="%H:%M %a %Z") -> str:
    """The current time text in a specified city's time zone."""
    current_time = nowtz(city)
    return current_time.strftime(fmt)


def _decimal_hours(dt: datetime.datetime) -> float:
    """Float hours:minutes from a datetime object"""
    return dt.hour + dt.minute / 60


def _get_sunrise(city: City, sunrise: bool = True):
    """Determine sunrise or sunset time for a city"""
    sun = suntime.Sun(city.lat, city.lng)
    sr_time = sun.get_sunrise_time() if sunrise else sun.get_sunset_time()
    tz = pytz.timezone(city.tz)
    return _decimal_hours(sr_time.astimezone(tz))


def _is_night(city: City):
    """Determine if it night for a city"""
    sunrise = _get_sunrise(city)
    sunset = _get_sunrise(city, False)
    now = nowtz(city)
    nowfloat = _decimal_hours(now)
    is_night = nowfloat < sunrise or nowfloat > sunset
    return is_night


def cities(print_all: bool, requested_cities: list) -> list[City]:
    """Cities sorted by longitude"""
    all_cities = [
        BASE_CITY,
        City("Honolulu", "Pacific/Honolulu", 21.3251912, -158.1307034),
        City("Mexico City", "America/Mexico_City", 19.3907336, -99.1436127),
        City("Milwaukee", "America/Chicago", 43.0576793, -88.1322139),
        City("Raleigh", "America/New_York", 35.8391044, -78.9745184),
        City("Azores", "Atlantic/Azores", 38.676345, -27.2990279),
        City("Copenhagen", "Europe/Copenhagen", 55.6708258, 12.2642021),
        City("Tel Aviv", "Asia/Tel_Aviv", 32.0853, 34.7818),
        City("Moscow", "Europe/Moscow", 55.582026, 37.3855235),
        City("Bangalore", "Asia/Kolkata", 12.9539974, 77.6309395),
        City("Shanghai", "Asia/Shanghai", 31.2243489, 121.4767528),
        City("Tokyo", "Asia/Tokyo", 35.5092405, 139.7698121),
        City("Sydney", "Australia/Sydney", 33.8482439, 150.9319747),
        City("Auckland", "Pacific/Auckland", -36.8777976, 174.7566242),
    ]
    unique_cities = {}
    for city in all_cities:
        # If just the short list of cities is being printed, skip others.
        # If a list of cities has been requested, skip cities not in that list.
        # The print_all argument overrules everything.
        if not print_all:
            if requested_cities and city.name not in requested_cities:
                continue
            if not requested_cities and city.name not in SHORT_LIST_NAMES:
                continue

        # Group cities in same time zone
        now_hm = nowtz(city).strftime("%H:%M")
        if now_hm in unique_cities:
            name = f"{city.name} / {unique_cities[now_hm].name}"
            unique_cities[now_hm] = City(name, city.tz, city.lat, city.lng)
        else:
            unique_cities[now_hm] = city
    cities_sorted = sorted(unique_cities.values(), key=lambda c: c.lng)
    return cities_sorted


def main():
    """Display the list"""
    args = parse_args()
    for city in cities(args.print_all, args.cities):
        msg = f"{city.name:20} {nowtz_text(city)}"
        if _is_night(city):
            msg = colored(msg, "dark_grey")
        print(msg)


if __name__ == "__main__":
    main()
