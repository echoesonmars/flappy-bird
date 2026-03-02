from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Iterable

import pygame

from .asset_loader import AssetBundle
from . import settings


class Screen(ABC):
    """Базовый интерфейс для всех экранов (меню, игра, настройки и т.д.)."""

    def __init__(self, assets: AssetBundle) -> None:
        self.assets = assets

    @abstractmethod
    def handle_events(self, events: Iterable[pygame.event.Event]) -> None:
        ...

    @abstractmethod
    def update(self, dt: float) -> None:
        ...

    @abstractmethod
    def draw(self, surface: pygame.Surface) -> None:
        ...


class MainMenuScreen(Screen):
    """Главное меню: фон, логотип, кнопки."""

    def __init__(self, assets: AssetBundle) -> None:
        super().__init__(assets)
        self._title_font = self.assets.fonts["ui_large"]
        self._small_font = self.assets.fonts["ui_small"]

    def handle_events(self, events: Iterable[pygame.event.Event]) -> None:
        # Логика кнопок появится позже; пока просто заглушка
        for event in events:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                pygame.event.post(pygame.event.Event(pygame.QUIT))

    def update(self, dt: float) -> None:
        _ = dt  # пока не используется, но пригодится для анимаций

    def draw(self, surface: pygame.Surface) -> None:
        background = self.assets.sprites.get("background_day")
        base = self.assets.sprites.get("base")

        if background is not None:
            surface.blit(background, (0, 0))

        if base is not None:
            surface.blit(base, (0, settings.HEIGHT - base.get_height()))

        title = self._title_font.render(
            settings.TITLE,
            True,
            settings.COLOR_TEXT,
        )
        title_rect = title.get_rect(center=(settings.WIDTH // 2, 80))
        surface.blit(title, title_rect)

        hint = self._small_font.render(
            "SPACE / ЛКМ — начать",
            True,
            settings.COLOR_TEXT,
        )
        hint_rect = hint.get_rect(center=(settings.WIDTH // 2, 140))
        surface.blit(hint, hint_rect)

