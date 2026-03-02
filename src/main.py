from __future__ import annotations

import sys
from typing import Optional

import pygame

from . import settings
from .asset_loader import AssetBundle, load_assets
from .ui import (
    CLOSE_SETTINGS,
    CLOSE_ORACLE,
    CLOSE_WARDROBE,
    GAME_OVER,
    GAME_RESTART,
    GAME_START,
    GameOverScreen,
    GameScreen,
    MainMenuScreen,
    OPEN_SETTINGS,
    OPEN_ORACLE,
    OPEN_WARDROBE,
    SettingsScreen,
    OracleScreen,
    WardrobeScreen,
    Screen,
)
from .data_manager import SaveData, apply_audio_settings, load_save, save_save


class Game:
    def __init__(self) -> None:
        pygame.init()
        pygame.display.set_caption(settings.TITLE)

        self.screen = pygame.display.set_mode(settings.WINDOW_SIZE)
        self.clock = pygame.time.Clock()

        self.assets: AssetBundle = load_assets()
        self.save_data: SaveData = load_save()
        apply_audio_settings(self.save_data, self.assets.sounds)
        self.current_screen: Optional[Screen] = MainMenuScreen(self.assets, self.save_data)
        self._running: bool = True

    def run(self) -> None:
        while self._running:
            dt_ms = self.clock.tick(settings.FPS)
            dt = dt_ms / 1000.0

            events = pygame.event.get()
            for event in events:
                if event.type == pygame.QUIT:
                    self._running = False
                if event.type == GAME_START:
                    self.current_screen = GameScreen(self.assets, self.save_data)
                if event.type == GAME_OVER:
                    data = getattr(event, "dict", {})
                    score = int(getattr(event, "score", data.get("score", 0)))
                    reason = str(getattr(event, "reason", data.get("reason", "")))
                    if score > self.save_data.high_score:
                        self.save_data.high_score = score
                    self.save_data.currency += score
                    save_save(self.save_data)
                    self.current_screen = GameOverScreen(self.assets, self.save_data, score, reason)
                if event.type == GAME_RESTART:
                    self.current_screen = GameScreen(self.assets, self.save_data)
                if event.type == OPEN_SETTINGS:
                    self.current_screen = SettingsScreen(self.assets, self.save_data)
                if event.type == CLOSE_SETTINGS:
                    apply_audio_settings(self.save_data, self.assets.sounds)
                    save_save(self.save_data)
                    self.current_screen = MainMenuScreen(self.assets, self.save_data)
                if event.type == OPEN_WARDROBE:
                    self.current_screen = WardrobeScreen(self.assets, self.save_data)
                if event.type == CLOSE_WARDROBE:
                    save_save(self.save_data)
                    self.current_screen = MainMenuScreen(self.assets, self.save_data)
                if event.type == OPEN_ORACLE:
                    self.current_screen = OracleScreen(self.assets, self.save_data)
                if event.type == CLOSE_ORACLE:
                    save_save(self.save_data)
                    self.current_screen = MainMenuScreen(self.assets, self.save_data)

            if self.current_screen is not None:
                self.current_screen.handle_events(events)
                self.current_screen.update(dt)
                self.current_screen.draw(self.screen)

            pygame.display.flip()

        pygame.quit()
        sys.exit(0)


def main() -> None:
    game = Game()
    game.run()


if __name__ == "__main__":
    main()

