from __future__ import annotations

import sys
from typing import Optional

import pygame

from . import settings
from .asset_loader import AssetBundle, load_assets
from .ui import MainMenuScreen, Screen


class Game:
    """Главный объект игры: окно, цикл и текущий экран."""

    def __init__(self) -> None:
        pygame.init()
        pygame.display.set_caption(settings.TITLE)

        self.screen = pygame.display.set_mode(settings.WINDOW_SIZE)
        self.clock = pygame.time.Clock()

        self.assets: AssetBundle = load_assets()

        # Пока только главное меню; позже сюда добавится машина состояний
        self.current_screen: Screen = MainMenuScreen(self.assets)
        self._running: bool = True

    def run(self) -> None:
        while self._running:
            dt_ms = self.clock.tick(settings.FPS)
            dt = dt_ms / 1000.0

            events = pygame.event.get()
            for event in events:
                if event.type == pygame.QUIT:
                    self._running = False

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

