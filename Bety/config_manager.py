"""
config_manager.py
-----------------
Manages local configuration for Bety, explicitly focusing on Whisper settings.
The config is saved to a local JSON file that is ignored by Git to protect user preferences.
"""

from __future__ import annotations

import json
from pathlib import Path

# The local config file (added to .gitignore)
CONFIG_FILE = Path(__file__).parent / "config.json"

# Reasonable base defaults
DEFAULTS: dict[str, str] = {
    "WHISPER_LANGUAGE": "Auto",  # Auto, English, Spanish
    "WHISPER_MODEL_SIZE": "base", # tiny, base, small
}


def load_config() -> dict[str, str]:
    """Load settings from config.json, backfilling any missing defaults.

    Returns:
        dict[str, str]: The complete configuration dictionary.
    """
    config = dict(DEFAULTS)
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, encoding="utf-8") as f:
                user_config = json.load(f)
                # Merge user config into defaults
                for key, val in user_config.items():
                    if key in config:
                        config[key] = val
        except Exception as exc:  # noqa: BLE001
            print(f"[config_manager] Warning: Could not parse {CONFIG_FILE.name}: {exc}")
    
    # Optional: Automatically cleanup old legacy keys if found
    save_config(config)

    return config


def save_config(config: dict[str, str]) -> None:
    """Save the configuration dictionary to config.json.

    Args:
        config (dict[str, str]): The dictionary containing valid keys.
    """
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4)
    except Exception as exc:  # noqa: BLE001
        print(f"[config_manager] Error saving to {CONFIG_FILE.name}: {exc}")
