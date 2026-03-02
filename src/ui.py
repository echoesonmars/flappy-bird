from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Iterable

import pygame

from .asset_loader import AssetBundle
from . import settings
from .player import Player
from .obstacles import PipePair


GAME_START = pygame.USEREVENT + 1
GAME_OVER = pygame.USEREVENT + 2
GAME_RESTART = pygame.USEREVENT + 3


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
    def __init__(self, assets: AssetBundle) -> None:
        super().__init__(assets)
        self._title_font = self.assets.fonts["ui_large"]
        self._small_font = self.assets.fonts["ui_small"]

    def handle_events(self, events: Iterable[pygame.event.Event]) -> None:
        for event in events:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                pygame.event.post(pygame.event.Event(pygame.QUIT))
            if event.type == pygame.KEYDOWN and event.key in (
                pygame.K_SPACE,
                pygame.K_RETURN,
            ):
                pygame.event.post(pygame.event.Event(GAME_START))
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                pygame.event.post(pygame.event.Event(GAME_START))

    def update(self, dt: float) -> None:
        _ = dt

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


class GameScreen(Screen):
    def __init__(self, assets: AssetBundle) -> None:
        super().__init__(assets)
        self.player = Player(self.assets, "blue")
        self.pipes: list[PipePair] = []
        self.score = 0
        self.background_x = 0.0
        self.base_x = 0.0
        self._pipe_spawn_x = settings.WIDTH + 80
        self._spawn_initial_pipes()

    def _spawn_initial_pipes(self) -> None:
        self.pipes.clear()
        x = self._pipe_spawn_x
        for _ in range(3):
            self.pipes.append(PipePair(self.assets, x))
            x += settings.PIPE_DISTANCE_X

    def handle_events(self, events: Iterable[pygame.event.Event]) -> None:
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.event.post(pygame.event.Event(pygame.QUIT))
                if event.key == pygame.K_SPACE:
                    self.player.jump()
                    self.assets.sounds["wing"].play()
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self.player.jump()
                self.assets.sounds["wing"].play()

    def update(self, dt: float) -> None:
        self.player.update(dt)
        for pipe in self.pipes:
            pipe.update(dt)

        self._cleanup_pipes()
        self._maybe_spawn_pipe()
        self._check_collisions()
        self._update_score()
        self._update_scroll(dt)

    def _cleanup_pipes(self) -> None:
        self.pipes = [p for p in self.pipes if p.rect_top.right > -50]

    def _maybe_spawn_pipe(self) -> None:
        if not self.pipes:
            self.pipes.append(PipePair(self.assets, self._pipe_spawn_x))
            return
        last_pipe = self.pipes[-1]
        if last_pipe.rect_top.x < settings.WIDTH - settings.PIPE_DISTANCE_X:
            self.pipes.append(PipePair(self.assets, self._pipe_spawn_x))

    def _check_collisions(self) -> None:
        background = self.assets.sprites.get("background_day")
        base = self.assets.sprites.get("base")
        if background is None or base is None:
            ground_y = settings.HEIGHT - 80
        else:
            ground_y = settings.HEIGHT - base.get_height()

        if self.player.rect.bottom >= ground_y or self.player.rect.top <= 0:
            self._trigger_game_over()
            return

        for pipe in self.pipes:
            if self.player.rect.colliderect(pipe.rect_top) or self.player.rect.colliderect(pipe.rect_bottom):
                self._trigger_game_over()
                return

    def _trigger_game_over(self) -> None:
        self.assets.sounds["hit"].play()
        self.assets.sounds["die"].play()
        pygame.event.post(pygame.event.Event(GAME_OVER, {"score": self.score}))

    def _update_score(self) -> None:
        for pipe in self.pipes:
            if not pipe.passed and pipe.rect_top.right < self.player.rect.left:
                pipe.passed = True
                self.score += 1
                self.assets.sounds["point"].play()

    def _update_scroll(self, dt: float) -> None:
        bg_speed = -30
        base_speed = -120
        self.background_x += bg_speed * dt
        self.base_x += base_speed * dt
        bg_width = self.assets.sprites["background_day"].get_width()
        base_width = self.assets.sprites["base"].get_width()
        if self.background_x <= -bg_width:
            self.background_x += bg_width
        if self.base_x <= -base_width:
            self.base_x += base_width

    def draw(self, surface: pygame.Surface) -> None:
        background = self.assets.sprites["background_day"]
        base = self.assets.sprites["base"]

        bg_w = background.get_width()
        for i in range(2):
            surface.blit(background, (self.background_x + i * bg_w, 0))

        for pipe in self.pipes:
            pipe.draw(surface)

        self.player.draw(surface)

        base_w = base.get_width()
        base_y = settings.HEIGHT - base.get_height()
        for i in range(2):
            surface.blit(base, (self.base_x + i * base_w, base_y))

        self._draw_score(surface)

    def _draw_score(self, surface: pygame.Surface) -> None:
        text = str(self.score)
        total_width = sum(self.assets.sprites[f"digit_{int(ch)}"].get_width() for ch in text)
        x = (settings.WIDTH - total_width) // 2
        y = 40
        for ch in text:
            sprite = self.assets.sprites[f"digit_{int(ch)}"]
            surface.blit(sprite, (x, y))
            x += sprite.get_width()


class GameOverScreen(Screen):
    def __init__(self, assets: AssetBundle, score: int) -> None:
        super().__init__(assets)
        self.score = score
        self._font = self.assets.fonts["ui_medium"]

    def handle_events(self, events: Iterable[pygame.event.Event]) -> None:
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.event.post(pygame.event.Event(pygame.QUIT))
                if event.key in (pygame.K_SPACE, pygame.K_RETURN):
                    pygame.event.post(pygame.event.Event(GAME_RESTART))
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                pygame.event.post(pygame.event.Event(GAME_RESTART))

    def update(self, dt: float) -> None:
        _ = dt

    def draw(self, surface: pygame.Surface) -> None:
        background = self.assets.sprites["background_day"]
        base = self.assets.sprites["base"]
        gameover_sprite = self.assets.sprites["gameover"]

        surface.blit(background, (0, 0))
        base_y = settings.HEIGHT - base.get_height()
        surface.blit(base, (0, base_y))

        go_rect = gameover_sprite.get_rect(center=(settings.WIDTH // 2, 140))
        surface.blit(gameover_sprite, go_rect)

        text = f"Счёт: {self.score}"
        label = self._font.render(text, True, settings.COLOR_TEXT)
        label_rect = label.get_rect(center=(settings.WIDTH // 2, 210))
        surface.blit(label, label_rect)

        hint = self._font.render("SPACE / ЛКМ — заново", True, settings.COLOR_TEXT)
        hint_rect = hint.get_rect(center=(settings.WIDTH // 2, 260))
        surface.blit(hint, hint_rect)

