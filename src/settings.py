
import os
from typing import Final

import pygame


if not pygame.get_init():
    pygame.init()


WIDTH: Final[int] = 288
HEIGHT: Final[int] = 512
WINDOW_SIZE: Final[tuple[int, int]] = (WIDTH, HEIGHT)
FPS: Final[int] = 60

TITLE: Final[str] = "Flappy Oracle"


BASE_DIR: Final[str] = os.path.dirname(os.path.dirname(__file__))
ASSETS_DIR: Final[str] = os.path.join(BASE_DIR, "assets")
SPRITES_DIR: Final[str] = os.path.join(ASSETS_DIR, "sprites")
AUDIO_DIR: Final[str] = os.path.join(ASSETS_DIR, "audio")
FONTS_DIR: Final[str] = os.path.join(ASSETS_DIR, "fonts")
DATA_DIR: Final[str] = os.path.join(BASE_DIR, "data")
SAVE_FILE_PATH: Final[str] = os.path.join(DATA_DIR, "save_data.json")


GRAVITY: Final[float] = 0.25
JUMP_FORCE: Final[float] = -4.5

PIPE_GAP_START: Final[int] = 100
PIPE_DISTANCE_X: Final[int] = 180


COLOR_BACKGROUND: Final[tuple[int, int, int]] = (0, 0, 0)
COLOR_TEXT: Final[tuple[int, int, int]] = (240, 240, 240)


DEFAULT_FONT_PATH: Final[str] = os.path.join(
    FONTS_DIR,
    "Geist-VariableFont_wght.ttf",
)

DEFAULT_FONT_SIZE_SMALL: Final[int] = 16
DEFAULT_FONT_SIZE_MEDIUM: Final[int] = 24
DEFAULT_FONT_SIZE_LARGE: Final[int] = 32

DEFAULT_MUSIC_VOLUME: Final[float] = 0.5
DEFAULT_SFX_VOLUME: Final[float] = 0.8

ORACLE_QUESTION_COST: Final[int] = 5

