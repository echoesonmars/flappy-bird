from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Iterable

import pygame

from .asset_loader import AssetBundle
from . import settings
from .player import Player
from .obstacles import PipePair
from .data_manager import SaveData
from . import ai_core


GAME_START = pygame.USEREVENT + 1
GAME_OVER = pygame.USEREVENT + 2
GAME_RESTART = pygame.USEREVENT + 3
OPEN_SETTINGS = pygame.USEREVENT + 4
CLOSE_SETTINGS = pygame.USEREVENT + 5
OPEN_WARDROBE = pygame.USEREVENT + 6
CLOSE_WARDROBE = pygame.USEREVENT + 7
OPEN_ORACLE = pygame.USEREVENT + 8
CLOSE_ORACLE = pygame.USEREVENT + 9


class Screen(ABC):
    def __init__(self, assets: AssetBundle, save_data: SaveData | None = None) -> None:
        self.assets = assets
        self.save_data = save_data

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
    def __init__(self, assets: AssetBundle, save_data: SaveData | None = None) -> None:
        super().__init__(assets, save_data)
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
            if event.type == pygame.KEYDOWN and event.key == pygame.K_s:
                pygame.event.post(pygame.event.Event(OPEN_SETTINGS))
            if event.type == pygame.KEYDOWN and event.key == pygame.K_k:
                pygame.event.post(pygame.event.Event(OPEN_WARDROBE))
            if event.type == pygame.KEYDOWN and event.key == pygame.K_o:
                pygame.event.post(pygame.event.Event(OPEN_ORACLE))
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

        hint_main = self._small_font.render(
            "SPACE / ЛКМ — начать",
            True,
            settings.COLOR_TEXT,
        )
        hint_main_rect = hint_main.get_rect(center=(settings.WIDTH // 2, 140))
        surface.blit(hint_main, hint_main_rect)

        hint_settings = self._small_font.render(
            "S — настройки, K — скины, O — Оракул",
            True,
            settings.COLOR_TEXT,
        )
        hint_settings_rect = hint_settings.get_rect(center=(settings.WIDTH // 2, 180))
        surface.blit(hint_settings, hint_settings_rect)


class GameScreen(Screen):
    def __init__(self, assets: AssetBundle, save_data: SaveData | None = None) -> None:
        super().__init__(assets, save_data)
        color = "blue"
        if self.save_data is not None:
            color = self.save_data.equipped_skin
        self.player = Player(self.assets, color)
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
            self._trigger_game_over("ground")
            return

        for pipe in self.pipes:
            if self.player.rect.colliderect(pipe.rect_top) or self.player.rect.colliderect(pipe.rect_bottom):
                self._trigger_game_over("pipe")
                return

    def _trigger_game_over(self, reason: str) -> None:
        self.assets.sounds["hit"].play()
        self.assets.sounds["die"].play()
        pygame.event.post(pygame.event.Event(GAME_OVER, {"score": self.score, "reason": reason}))

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
    def __init__(self, assets: AssetBundle, save_data: SaveData | None, score: int, reason: str) -> None:
        super().__init__(assets, save_data)
        self.score = score
        self._font = self.assets.fonts["ui_medium"]
        self.ai_text = ""
        if self.save_data is not None:
            ai_core.request_game_over_message(self.save_data, score, reason, self._on_ai_text)

    def _on_ai_text(self, text: str) -> None:
        self.ai_text = text

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

        if self.ai_text:
            wrapped = self._wrap_text(self.ai_text, 26)
            y = 240
            for line in wrapped:
                line_surf = self._font.render(line, True, settings.COLOR_TEXT)
                line_rect = line_surf.get_rect(center=(settings.WIDTH // 2, y))
                surface.blit(line_surf, line_rect)
                y += 26

        hint = self._font.render("SPACE / ЛКМ — заново", True, settings.COLOR_TEXT)
        hint_rect = hint.get_rect(center=(settings.WIDTH // 2, settings.HEIGHT - 60))
        surface.blit(hint, hint_rect)

    def _wrap_text(self, text: str, max_len: int) -> list[str]:
        words = text.split()
        lines: list[str] = []
        current: list[str] = []
        for w in words:
            test = " ".join(current + [w])
            if len(test) > max_len and current:
                lines.append(" ".join(current))
                current = [w]
            else:
                current.append(w)
        if current:
            lines.append(" ".join(current))
        return lines


class SettingsScreen(Screen):
    def __init__(self, assets: AssetBundle, save_data: SaveData) -> None:
        super().__init__(assets, save_data)
        self._font = self.assets.fonts["ui_medium"]
        self._small_font = self.assets.fonts["ui_small"]
        self._field_index = 0
        self._api_key_buffer = self.save_data.settings_data.get("openai_api_key", "")

    def handle_events(self, events: Iterable[pygame.event.Event]) -> None:
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.event.post(pygame.event.Event(CLOSE_SETTINGS))
                if event.key in (pygame.K_UP, pygame.K_w):
                    self._field_index = (self._field_index - 1) % 3
                if event.key in (pygame.K_DOWN, pygame.K_s):
                    self._field_index = (self._field_index + 1) % 3
                if event.key in (pygame.K_LEFT, pygame.K_a):
                    self._adjust_value(-0.1)
                if event.key in (pygame.K_RIGHT, pygame.K_d):
                    self._adjust_value(0.1)
                if self._field_index == 2:
                    if event.key == pygame.K_BACKSPACE:
                        self._api_key_buffer = self._api_key_buffer[:-1]
                    elif event.key == pygame.K_RETURN:
                        self._apply_changes()
                        pygame.event.post(pygame.event.Event(CLOSE_SETTINGS))
                    else:
                        if event.unicode and not event.unicode.isspace():
                            self._api_key_buffer += event.unicode

    def _adjust_value(self, delta: float) -> None:
        if self._field_index == 0:
            v = float(self.save_data.settings_data.get("music_volume", settings.DEFAULT_MUSIC_VOLUME))
            v = max(0.0, min(1.0, v + delta))
            self.save_data.settings_data["music_volume"] = v
        if self._field_index == 1:
            v = float(self.save_data.settings_data.get("sfx_volume", settings.DEFAULT_SFX_VOLUME))
            v = max(0.0, min(1.0, v + delta))
            self.save_data.settings_data["sfx_volume"] = v

    def _apply_changes(self) -> None:
        self.save_data.settings_data["openai_api_key"] = self._api_key_buffer

    def update(self, dt: float) -> None:
        _ = dt

    def draw(self, surface: pygame.Surface) -> None:
        background = self.assets.sprites["background_day"]
        base = self.assets.sprites["base"]
        surface.blit(background, (0, 0))
        base_y = settings.HEIGHT - base.get_height()
        surface.blit(base, (0, base_y))

        title = self._font.render("Настройки", True, settings.COLOR_TEXT)
        title_rect = title.get_rect(center=(settings.WIDTH // 2, 80))
        surface.blit(title, title_rect)

        music_volume = float(self.save_data.settings_data.get("music_volume", settings.DEFAULT_MUSIC_VOLUME))
        sfx_volume = float(self.save_data.settings_data.get("sfx_volume", settings.DEFAULT_SFX_VOLUME))
        api_key_display = "*" * len(self._api_key_buffer) if self._api_key_buffer else "(пусто)"

        items = [
            f"Музыка: {music_volume:.1f}",
            f"SFX: {sfx_volume:.1f}",
            f"OpenAI Key: {api_key_display}",
        ]

        y = 150
        for index, text in enumerate(items):
            color = settings.COLOR_TEXT
            if index == self._field_index:
                label = self._font.render(text, True, color)
            else:
                label = self._small_font.render(text, True, color)
            rect = label.get_rect(center=(settings.WIDTH // 2, y))
            surface.blit(label, rect)
            y += 40


class WardrobeScreen(Screen):
    def __init__(self, assets: AssetBundle, save_data: SaveData) -> None:
        super().__init__(assets, save_data)
        self._font = self.assets.fonts["ui_medium"]
        self._small_font = self.assets.fonts["ui_small"]
        self._skins = ["blue", "red", "yellow"]
        self._index = 0

    def handle_events(self, events: Iterable[pygame.event.Event]) -> None:
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.event.post(pygame.event.Event(CLOSE_WARDROBE))
                if event.key in (pygame.K_LEFT, pygame.K_a):
                    self._index = (self._index - 1) % len(self._skins)
                if event.key in (pygame.K_RIGHT, pygame.K_d):
                    self._index = (self._index + 1) % len(self._skins)
                if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    self._select_or_unlock()
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self._select_or_unlock()

    def _select_or_unlock(self) -> None:
        skin = self._skins[self._index]
        if skin in self.save_data.unlocked_skins:
            self.save_data.equipped_skin = skin
            pygame.event.post(pygame.event.Event(CLOSE_WARDROBE))
            return
        cost = 20
        if self.save_data.currency >= cost:
            self.save_data.currency -= cost
            self.save_data.unlocked_skins.append(skin)
            self.save_data.equipped_skin = skin
            pygame.event.post(pygame.event.Event(CLOSE_WARDROBE))

    def update(self, dt: float) -> None:
        _ = dt

    def draw(self, surface: pygame.Surface) -> None:
        background = self.assets.sprites["background_day"]
        base = self.assets.sprites["base"]
        surface.blit(background, (0, 0))
        base_y = settings.HEIGHT - base.get_height()
        surface.blit(base, (0, base_y))

        title = self._font.render("Скины", True, settings.COLOR_TEXT)
        title_rect = title.get_rect(center=(settings.WIDTH // 2, 80))
        surface.blit(title, title_rect)

        current_skin = self._skins[self._index]
        frames_keys = [
            f"bird_{current_skin}_midflap",
        ]
        bird_surface = self.assets.sprites[frames_keys[0]]
        bird_rect = bird_surface.get_rect(center=(settings.WIDTH // 2, 180))
        surface.blit(bird_surface, bird_rect)

        unlocked = current_skin in self.save_data.unlocked_skins
        cost = 20
        if unlocked:
            status_text = "Открыто"
        else:
            status_text = f"Цена: {cost} | Валюта: {self.save_data.currency}"

        status = self._small_font.render(status_text, True, settings.COLOR_TEXT)
        status_rect = status.get_rect(center=(settings.WIDTH // 2, 240))
        surface.blit(status, status_rect)

        hint = self._small_font.render("←/→ для выбора, SPACE — подтвердить", True, settings.COLOR_TEXT)
        hint_rect = hint.get_rect(center=(settings.WIDTH // 2, settings.HEIGHT - 50))
        surface.blit(hint, hint_rect)


class OracleScreen(Screen):
    def __init__(self, assets: AssetBundle, save_data: SaveData) -> None:
        super().__init__(assets, save_data)
        self._font = self.assets.fonts["ui_small"]
        self._input_buffer = ""
        self._waiting = False
        self._local_history: list[dict[str, str]] = list(self.save_data.ai_chat_history)

    def handle_events(self, events: Iterable[pygame.event.Event]) -> None:
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.event.post(pygame.event.Event(CLOSE_ORACLE))
                elif event.key == pygame.K_BACKSPACE:
                    self._input_buffer = self._input_buffer[:-1]
                elif event.key == pygame.K_RETURN:
                    self._send_message()
                else:
                    if event.unicode:
                        self._input_buffer += event.unicode

    def _send_message(self) -> None:
        text = self._input_buffer.strip()
        if not text or self._waiting:
            return
        self._input_buffer = ""
        self._local_history.append({"role": "user", "content": text})
        self._waiting = True

        def on_reply(answer: str) -> None:
            self._local_history.append({"role": "assistant", "content": answer})
            self.save_data.ai_chat_history = self._local_history[-20:]
            self._waiting = False

        ai_core.request_oracle_reply(self.save_data, self._local_history[-20:], on_reply)

    def update(self, dt: float) -> None:
        _ = dt

    def draw(self, surface: pygame.Surface) -> None:
        background = self.assets.sprites["background_night"]
        base = self.assets.sprites["base"]
        surface.blit(background, (0, 0))
        base_y = settings.HEIGHT - base.get_height()
        surface.blit(base, (0, base_y))

        padding = 10
        chat_rect = pygame.Rect(
            padding,
            padding,
            settings.WIDTH - 2 * padding,
            settings.HEIGHT - 80,
        )
        pygame.draw.rect(surface, (0, 0, 0, 128), chat_rect)

        y = chat_rect.bottom - 20
        for message in reversed(self._local_history[-10:]):
            prefix = "> " if message["role"] == "user" else "● "
            color = settings.COLOR_TEXT if message["role"] == "assistant" else (180, 220, 255)
            wrapped_lines = self._wrap_text(prefix + message["content"], 32)
            for line in reversed(wrapped_lines):
                text_surf = self._font.render(line, True, color)
                text_rect = text_surf.get_rect(left=chat_rect.left + 8, bottom=y)
                surface.blit(text_surf, text_rect)
                y -= 18
                if y < chat_rect.top + 10:
                    break
            if y < chat_rect.top + 10:
                break

        input_rect = pygame.Rect(
            padding,
            settings.HEIGHT - 60,
            settings.WIDTH - 2 * padding,
            40,
        )
        pygame.draw.rect(surface, (10, 10, 20), input_rect)
        pygame.draw.rect(surface, settings.COLOR_TEXT, input_rect, 1)

        prompt = self._input_buffer or "Задай вопрос Оракулу..."
        if self._waiting:
            prompt = "Оракул размышляет..."
        input_surf = self._font.render(prompt, True, settings.COLOR_TEXT)
        input_rect_inner = input_surf.get_rect(left=input_rect.left + 8, centery=input_rect.centery)
        surface.blit(input_surf, input_rect_inner)

    def _wrap_text(self, text: str, max_len: int) -> list[str]:
        words = text.split()
        lines: list[str] = []
        current: list[str] = []
        for w in words:
            test = " ".join(current + [w])
            if len(test) > max_len and current:
                lines.append(" ".join(current))
                current = [w]
            else:
                current.append(w)
        if current:
            lines.append(" ".join(current))
        return lines

