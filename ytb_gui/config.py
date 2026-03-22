"""Persistent configuration using platformdirs + JSON."""
from __future__ import annotations

import json
from pathlib import Path

from platformdirs import user_config_dir

APP_NAME = "ytb-summarizer"


def _config_dir() -> Path:
    return Path(user_config_dir(APP_NAME))


def config_file() -> Path:
    return _config_dir() / "config.json"


def templates_dir() -> Path:
    return _config_dir() / "templates"


def history_db() -> Path:
    return _config_dir() / "history.db"


def summaries_dir() -> Path:
    home = Path.home()
    return home / "summaries"


def load() -> dict:
    path = config_file()
    if path.exists():
        try:
            with open(path, encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return _defaults()


def save(data: dict) -> None:
    path = config_file()
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def _defaults() -> dict:
    return {
        "provider": "anthropic",
        "model": "claude-sonnet-4-6",
        "api_keys": {},          # {provider: api_key}
        "base_url": "",          # for custom provider
        "template": "default",
        "output_dir": str(summaries_dir()),
        "transcript_lang": "en",
        "summary_lang": "zh",
    }
