from __future__ import annotations

import random
from typing import List, Tuple

import pygame

from .asset_loader import AssetBundle
from . import settings


class PipePair:
    def __init__(self, assets: AssetBundle, x: int) -> None:
        self.assets = assets

        pipe_surface = self.assets.sprites["pipe_green"]
        self.image_top = pygame.transform.flip(pipe_surface, False, True)
        self.image_bottom = pipe_surface

        self.rect_top = self.image_top.get_rect()
        self.rect_bottom = self.image_bottom.get_rect()

        self._set_initial_position(x)

        self.passed: bool = False

    def _set_initial_position(self, x: int) -> None:
        gap_y = random.randint(120, settings.HEIGHT - 120)
        gap_half = settings.PIPE_GAP_START // 2

        self.rect_top.midbottom = (x, gap_y - gap_half)
        self.rect_bottom.midtop = (x, gap_y + gap_half)

    def update(self, dt: float) -> None:
        speed_x = -120  # пикселей в секунду
        dx = int(speed_x * dt)

        self.rect_top.x += dx
        self.rect_bottom.x += dx

    def draw(self, surface: pygame.Surface) -> None:
        surface.blit(self.image_top, self.rect_top)
        surface.blit(self.image_bottom, self.rect_bottom)

