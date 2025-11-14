# World Clock CLI

A command line interface (CLI) for displaying local times in various cities

This tool lets you:

- Display local times for a list of cities
- Search for cities by name (with fuzzy matching).
- Save your preferred home city and requested cities in a config file.

In the examples below, the command is written as `clock`


## Installation

Install into your environment from the project root:

    pip git+https://github.com/kesterallen/timing_tools.git.


## City Database

The `world-clock` and `search` commands both rely on this database.


## Configuration

User configuration is managed via `clock/config.py` and stored at the path defined by `CONFIG_FILE`.

The configuration stores:

- `home_city` (int): ID of your "home" city (displayed first).
- `requested_cities` (list[int]): IDs of other cities to display by default.

Conceptually, the config looks like:

    {
      "home_city": 1234,
      "requested_cities": [1234, 5678, 91011]
    }

When you invoke commands:

- The config is loaded automatically.
- CLI options override config values for that invocation only.


# Commands

## `world-clock` – display city times

    clock world-clock [OPTIONS]

Displays the current local time and time zone for a set of cities.

### Options

- `-h, --home-city INTEGER`  
  Override the home city ID for this run. If omitted, `config.home_city` is used.

- `-r, --requested-cities INTEGER...`  
  One or more city IDs to display. If omitted, `config.requested_cities` is used.

- `-w, --column-width INTEGER`  
  Minimum width of the city column. Default: `20`.

- `-v, --verbose`  
  Show additional metadata columns: country, state, latitude, longitude, and ID.

### Behavior

Internally, `world-clock`:

1. Loads the configuration with `load_config()`.
2. If `--home-city` is not provided, uses `config.home_city`.
3. If `--requested-cities` is not provided, uses `config.requested_cities`.
4. Calls `prepend_home_city(home_city, requested_cities)` so the home city is always first.
5. Loads cities from `data/base_cities.json` via `load_cities`.
6. Builds a Rich table with columns:
   - `City` (with a sun `☼` or moon `☾` icon, depending on whether it is currently day or night).
   - `Local Time` (formatted using the city’s `nowtz_text()`).
   - `Timezone`.
   - In verbose mode, additional columns: `Country`, `State`, `Latitude`, `Longitude`, `ID`.
7. Night-time rows are dimmed; day-time rows use normal styling.

### Examples

Use configuration defaults:

    clock world-clock

Override home city and requested cities:

    clock world-clock --home-city 1001 --requested-cities 1001 --requested-cities 2002

Verbose output with extra metadata:

    clock world-clock -v

Custom column width:

    clock world-clock -w 28


## `search` – find city IDs

    clock search [OPTIONS] QUERY

Search the city database by (partial) name and display possible matches.

### Arguments

- `QUERY`  
  City name or partial name to search for (case-insensitive).

### Options

- `-s, --similarity FLOAT`  
  Similarity threshold between `0.0` and `1.0`. Default is `0.8`. Higher values mean stricter matching.

### Behavior

The `search` command:

1. Lowercases the query.

2. If more than 50 matches are returned, it prints a message and exits with code `1`:

   Too many matches (N). Please use a stricter similarity.

3. Sorts matches by `(country, state, name)` for stable output.
4. Returns `Name`, `State`, `Country`, `Timezone`, `ID`.
5. Prints a header showing the query and then the table.

You will use the `ID` column from this output with the `world-clock` and `config` commands.

### Examples

Basic search:

    clock search "san diego"

Stricter similarity (fewer, closer matches):

    clock search "san" --similarity 0.9

## `config` – manage user configuration

Configuration management commands live under the `config` subcommand:

    clock config [COMMAND] [OPTIONS]

Available subcommands:

- `set-home`
- `add-city`
- `remove-city`
- `reset`
- `show`


### `config show`

    clock config show

Show the current world clock configuration as JSON (pretty-printed):

Example output:

    {
      "home_city": 1234,
      "requested_cities": [1234, 5678, 91011]
    }


### `config set-home`

    clock config set-home CITY_ID

Set the default home city ID.

Behavior:

- Loads the current config with `load_config()`.
- Sets `config.home_city = CITY_ID`.
- Saves the config with `save_config(config)`.

Example output:

    Home city updated → 1234


### `config add-city`

    clock config add-city CITY_ID

Add a city ID to the `requested_cities` list.

Behavior:

- If `CITY_ID` is not already in `config.requested_cities`, it is appended and the config is saved.
- If it is already present, nothing changes and a message is printed.

Example outputs:

    Added city → 5678

or

    City 5678 already in requested list.


### `config remove-city`

    clock config remove-city CITY_ID

Remove a city ID from the `requested_cities` list.

Behavior:

- If `CITY_ID` exists in `config.requested_cities`, it is removed and the config is saved.
- If not present, a message is printed.

Example outputs:

    Removed city → 5678

or

    City 5678 not found in requested list.


### `config reset`

    clock config reset

Reset the world clock configuration to defaults.

Behavior:

- Calls `delete_config()` to remove the config file.
- Prints the path of the removed `CONFIG_FILE`.

Example output:

    Removed configuration → /path/to/config/file.json


## Typical workflow

1. Search for cities and note their IDs:

       clock search "san diego"
       clock search "london"
       clock search "tokyo"

2. Set your home city:

       clock config set-home 1234

3. Add other cities you care about:

       clock config add-city 5678
       clock config add-city 91011

4. View the world clock:

       clock world-clock

5. Inspect your config:

       clock config show

6. Override config for a one-off view:

       clock world-clock --home-city 5678 --requested-cities 5678 7654 4321 -v


## Development notes

- The CLI is built with Typer.
- Output formatting uses Rich.
- Configuration uses a Pydantic model defined in `clock/config.py`.
- City and search helper functions are provided by:
  - `clock.worldclock` (for `load_cities` and `prepend_home_city`)
  - `clock.search` (for `get_city_matches`)
