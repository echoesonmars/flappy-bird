from __future__ import annotations

from typing import List, Tuple

import pygame

from .asset_loader import AssetBundle, get_bird_animation_keys
from . import settings


class Player(pygame.sprite.Sprite):
    """Игрок: анимированная птица/дрон с простой физикой."""

    def __init__(self, assets: AssetBundle, color: str = "blue") -> None:
        super().__init__()

        self.assets = assets

        frame_keys: Tuple[str, str, str] = get_bird_animation_keys(color)
        self.frames: List[pygame.Surface] = [
            self.assets.sprites[key] for key in frame_keys
        ]

        self.frame_index: float = 0.0
        self.animation_speed: float = 8.0  # кадров в секунду

        self.image: pygame.Surface = self.frames[0]
        self.rect: pygame.Rect = self.image.get_rect(
            center=(settings.WIDTH // 4, settings.HEIGHT // 2),
        )

        self.velocity_y: float = 0.0

    def jump(self) -> None:
        self.velocity_y = settings.JUMP_FORCE

    def update(self, dt: float) -> None:
        # Физика
        self.velocity_y += settings.GRAVITY
        self.rect.y += int(self.velocity_y)

        # Анимация
        self.frame_index += self.animation_speed * dt
        if self.frame_index >= len(self.frames):
            self.frame_index = 0.0

        current_frame = self.frames[int(self.frame_index)]

        # Наклон в зависимости от скорости
        angle = -self.velocity_y * 4  # подбираемый коэффициент
        self.image = pygame.transform.rotate(current_frame, angle)
        self.rect = self.image.get_rect(center=self.rect.center)

