"""Command lint interface for clock toosl."""

import json
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table

from clock.config import CONFIG_FILE, delete_config, load_config, save_config

from .search import get_city_matches
from .worldclock import load_cities, prepend_home_city

app = typer.Typer(help="Clock functions")
console = Console()

app = typer.Typer(help="Display city times and time zones")

config_app = typer.Typer(help="Manage world clock user configuration")
app.add_typer(config_app, name="config")

# TODO: Move this to a config or something
default_city_file = Path(__file__).parent / "data/base_cities.json"


@config_app.command("set-home")
def set_home(home_city: Annotated[int, typer.Argument(help="City ID to set as home city")]):
    """Set the default home city."""
    config = load_config()
    config.home_city = home_city
    save_config(config)
    typer.echo(f"Home city updated → {home_city}")


@config_app.command("add-city")
def add_city(city_id: Annotated[int, typer.Argument(help="City ID to add to requested list")]):
    """Add a city ID to the default requested cities."""
    config = load_config()

    if city_id not in config.requested_cities:
        config.requested_cities.append(city_id)
        save_config(config)
        typer.echo(f"Added city → {city_id}")
    else:
        typer.echo(f"City {city_id} already in requested list.")


@config_app.command("remove-city")
def remove_city(city_id: Annotated[int, typer.Argument(help="City ID to remove from defaults")]):
    """Remove a city from the default requested cities."""
    config = load_config()

    if city_id in config.requested_cities:
        config.requested_cities = [cid for cid in config.requested_cities if cid != city_id]
        save_config(config)
        typer.echo(f"Removed city → {city_id}")
    else:
        typer.echo(f"City {city_id} not found in requested list.")


@config_app.command("reset")
def reset():
    """Set default configuration for the world clock CLI."""
    delete_config()
    typer.echo(f"Removed configuration → {CONFIG_FILE}")


@config_app.command("show")
def show_config():
    """Show the current world clock configuration."""
    config = load_config()
    typer.echo(config.model_dump_json(indent=2))


@app.command("world-clock")
def world_clock(
    home_city: Annotated[
        int | None,
        typer.Option("--home-city", "-h", help="The ID of your home city (first displayed)"),
    ] = None,
    requested_cities: Annotated[
        list[int] | None,
        typer.Option(
            "--requested-cities",
            "-r",
            help="List of city IDs to display",
        ),
    ] = None,
    column_width: Annotated[
        int,
        typer.Option("--column-width", "-w", help="Column print width (minimum city column width)."),
    ] = 20,
    verbose: Annotated[bool, typer.Option("--verbose", "-v", help="Increase verbosity level")] = False,
):
    """Entry point for the World Clock CLI."""
    config = load_config()

    # Merge config with CLI flags (CLI wins)
    if home_city is None:
        home_city = config.home_city

    if requested_cities is None:
        requested_cities = config.requested_cities

    requested_cities = prepend_home_city(home_city, requested_cities)
    cities = load_cities(default_city_file)
    cities = [cities[id_] for id_ in requested_cities if id_ in cities]

    table = Table(
        title="🌍 World Clock",
        header_style="bold magenta",
        show_lines=False,
    )

    table.add_column("City", style="bold cyan", min_width=column_width)
    table.add_column("Local Time", style="green")
    table.add_column("Timezone", style="white")

    if verbose:
        table.add_column("Country", style="bold cyan", min_width=column_width)
        table.add_column("State", style="bold cyan", min_width=column_width)
        table.add_column("Latitude", justify="right")
        table.add_column("Longitude", justify="right")
        table.add_column("ID", justify="right")

    for city in cities:
        is_night = city.is_night
        emoji = "☾" if is_night else "☼"
        row_style = "dim" if is_night else None

        base_cells: list[str] = [
            f"{emoji} {city.name}",
            city.nowtz_text(),  # uses DEFAULT_TIME_FORMAT
            str(city.tz),
        ]

        if verbose:
            base_cells.extend(
                [
                    city.country,
                    city.state,
                    f"{city.lat:.4f}",
                    f"{city.lng:.4f}",
                    str(city.id),
                ]
            )

        table.add_row(*base_cells, style=row_style)

    console.print(table)


@app.command("search")
def search_cities(
    query: Annotated[str, typer.Argument(help="City name or partial name to search for")],
    similarity: Annotated[
        float,
        typer.Option("--similarity", "-s", help="Similarity threshold between 0 and 1"),
    ] = 0.8,
):
    """Search for cities by name and display possible matches."""
    data = json.loads(default_city_file.read_text())
    q = query.lower()
    matches = get_city_matches(data, q, threshold=similarity)
    if len(matches) > 50:
        console.print(f"[red]Too many matches ({len(matches)}). Please use a stricter similarity.[/red]")
        raise typer.Exit(code=1)

    # Build Rich table
    table = Table(show_lines=False, header_style="bold cyan")
    table.add_column("Name", style="bold white")
    table.add_column("State")
    table.add_column("Country")
    table.add_column("Timezone")
    table.add_column("ID", justify="right")

    # Sort for stable output
    matches.sort(key=lambda e: (e.get("country", ""), e.get("state", ""), e.get("name", "")))

    for e in matches:
        table.add_row(
            e.get("name", ""),
            e.get("state", "") or "",
            e.get("country", "") or "",
            e.get("timezone", "") or "",
            str(e.get("id", "")),
        )

    console.print(f"\n[bold]Matches for:[/] '{query}'\n")
    console.print(table)


if __name__ == "__main__":
    app()
