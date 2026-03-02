from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Tuple

import pygame

from . import settings


pygame.init()


SpriteDict = Dict[str, pygame.Surface]
SoundDict = Dict[str, pygame.mixer.Sound]
FontDict = Dict[str, pygame.font.Font]


@dataclass
class AssetBundle:
    sprites: SpriteDict
    sounds: SoundDict
    fonts: FontDict


def load_sprites() -> SpriteDict:
    sprites: SpriteDict = {}

    # Фон
    sprites["background_day"] = pygame.image.load(
        f"{settings.SPRITES_DIR}/background-day.png",
    ).convert()
    sprites["background_night"] = pygame.image.load(
        f"{settings.SPRITES_DIR}/background-night.png",
    ).convert()

    # Земля
    sprites["base"] = pygame.image.load(
        f"{settings.SPRITES_DIR}/base.png",
    ).convert_alpha()

    # Цифры 0–9
    for digit in range(10):
        sprites[f"digit_{digit}"] = pygame.image.load(
            f"{settings.SPRITES_DIR}/{digit}.png",
        ).convert_alpha()

    # Птицы — кадры анимации по цветам
    bird_colors = ("blue", "red", "yellow")
    flaps = ("downflap", "midflap", "upflap")
    for color in bird_colors:
        for flap in flaps:
            key = f"bird_{color}_{flap}"
            filename = f"{color}bird-{flap}.png"
            sprites[key] = pygame.image.load(
                f"{settings.SPRITES_DIR}/{filename}",
            ).convert_alpha()

    # Трубы
    sprites["pipe_green"] = pygame.image.load(
        f"{settings.SPRITES_DIR}/pipe-green.png",
    ).convert_alpha()
    sprites["pipe_red"] = pygame.image.load(
        f"{settings.SPRITES_DIR}/pipe-red.png",
    ).convert_alpha()

    # UI
    sprites["gameover"] = pygame.image.load(
        f"{settings.SPRITES_DIR}/gameover.png",
    ).convert_alpha()
    sprites["message"] = pygame.image.load(
        f"{settings.SPRITES_DIR}/message.png",
    ).convert_alpha()

    return sprites


def load_sounds() -> SoundDict:
    pygame.mixer.init()

    sounds: SoundDict = {}

    # Смерть / удар
    sounds["die"] = pygame.mixer.Sound(f"{settings.AUDIO_DIR}/die.wav")
    sounds["hit"] = pygame.mixer.Sound(f"{settings.AUDIO_DIR}/hit.wav")

    # Очки
    sounds["point"] = pygame.mixer.Sound(f"{settings.AUDIO_DIR}/point.wav")

    # UI / переходы
    sounds["swoosh"] = pygame.mixer.Sound(f"{settings.AUDIO_DIR}/swoosh.wav")

    # Прыжок
    sounds["wing"] = pygame.mixer.Sound(f"{settings.AUDIO_DIR}/wing.wav")

    return sounds


def load_fonts() -> FontDict:
    fonts: FontDict = {}

    fonts["ui_small"] = pygame.font.Font(
        settings.DEFAULT_FONT_PATH,
        settings.DEFAULT_FONT_SIZE_SMALL,
    )
    fonts["ui_medium"] = pygame.font.Font(
        settings.DEFAULT_FONT_PATH,
        settings.DEFAULT_FONT_SIZE_MEDIUM,
    )
    fonts["ui_large"] = pygame.font.Font(
        settings.DEFAULT_FONT_PATH,
        settings.DEFAULT_FONT_SIZE_LARGE,
    )

    return fonts


def load_assets() -> AssetBundle:
    return AssetBundle(
        sprites=load_sprites(),
        sounds=load_sounds(),
        fonts=load_fonts(),
    )


def get_bird_animation_keys(color: str) -> Tuple[str, str, str]:
    """
    Удобный helper: по цвету возвращает ключи кадров анимации.

    Пример:
    >>> get_bird_animation_keys("blue")
    ("bird_blue_downflap", "bird_blue_midflap", "bird_blue_upflap")
    """
    return (
        f"bird_{color}_downflap",
        f"bird_{color}_midflap",
        f"bird_{color}_upflap",
    )

