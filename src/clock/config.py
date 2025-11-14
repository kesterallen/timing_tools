import json
from pathlib import Path

from platformdirs import user_config_dir
from pydantic import BaseModel

CONFIG_DIR = Path(user_config_dir("clock"))
CONFIG_FILE = CONFIG_DIR / "config.json"


class ClockConfig(BaseModel):
    """Configuration for the clock application."""

    home_city: int = 50388
    requested_cities: list[int] = [50388]


def load_config() -> ClockConfig:
    """Load the clock configuration from file or return default."""
    if CONFIG_FILE.exists():
        data = json.loads(CONFIG_FILE.read_text())
        return ClockConfig(**data)
    else:
        return ClockConfig()


def save_config(config: ClockConfig) -> None:
    """Save the clock configuration to file."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(config.model_dump_json(indent=2))


def delete_config() -> None:
    """Delete the user configuration file if it exists."""
    if CONFIG_FILE.exists():
        CONFIG_FILE.unlink()
        print(f"Deleted config file: {CONFIG_FILE}")
    else:
        print("No config file found.")
