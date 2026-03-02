from __future__ import annotations

import json
import os
from dataclasses import dataclass, asdict, field
from typing import Any, Dict

from . import settings


@dataclass
class SaveData:
    high_score: int = 0
    currency: int = 0
    unlocked_skins: list[str] = field(default_factory=lambda: ["blue"])
    equipped_skin: str = "blue"
    ai_chat_history: list[Dict[str, str]] = field(default_factory=list)
    settings_data: Dict[str, Any] = field(
        default_factory=lambda: {
            "music_volume": settings.DEFAULT_MUSIC_VOLUME,
            "sfx_volume": settings.DEFAULT_SFX_VOLUME,
            "openai_api_key": "",
        },
    )


def _ensure_data_dir() -> None:
    os.makedirs(settings.DATA_DIR, exist_ok=True)


def load_save() -> SaveData:
    _ensure_data_dir()
    if not os.path.exists(settings.SAVE_FILE_PATH):
        return SaveData()
    try:
        with open(settings.SAVE_FILE_PATH, "r", encoding="utf-8") as f:
            raw = json.load(f)
    except (OSError, json.JSONDecodeError):
        return SaveData()

    data = SaveData()
    data.high_score = int(raw.get("high_score", data.high_score))
    data.currency = int(raw.get("currency", data.currency))
    data.unlocked_skins = list(raw.get("unlocked_skins", data.unlocked_skins))
    data.equipped_skin = str(raw.get("equipped_skin", data.equipped_skin))
    data.ai_chat_history = list(raw.get("ai_chat_history", data.ai_chat_history))

    settings_raw = raw.get("settings", {})
    if not isinstance(settings_raw, dict):
        settings_raw = {}
    merged_settings = dict(data.settings_data)
    merged_settings.update(settings_raw)
    data.settings_data = merged_settings

    return data


def save_save(data: SaveData) -> None:
    _ensure_data_dir()
    payload = {
        "high_score": data.high_score,
        "currency": data.currency,
        "unlocked_skins": data.unlocked_skins,
        "equipped_skin": data.equipped_skin,
        "ai_chat_history": data.ai_chat_history,
        "settings": data.settings_data,
    }
    with open(settings.SAVE_FILE_PATH, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)


def apply_audio_settings(save_data: SaveData, sounds: dict[str, Any]) -> None:
    music_volume = float(save_data.settings_data.get("music_volume", settings.DEFAULT_MUSIC_VOLUME))
    sfx_volume = float(save_data.settings_data.get("sfx_volume", settings.DEFAULT_SFX_VOLUME))
    for key, sound in sounds.items():
        if hasattr(sound, "set_volume"):
            sound.set_volume(sfx_volume)

