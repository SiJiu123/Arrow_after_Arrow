import os
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

from app import Animation, ArrowGame, Page
from game_core import Arrow, Direction, GameState, Level, MoveResult
from levels import LEVELS


class InterfaceFlowTests(unittest.TestCase):
    def setUp(self):
        self.app = ArrowGame()

    def tearDown(self):
        pygame.quit()

    def test_start_button_opens_first_level(self):
        self.app._handle_click(self.app._start_button().rect.center, 0)

        self.assertEqual(self.app.page, Page.PLAYING)
        self.assertEqual(self.app.level_index, 0)
        self.assertEqual(len(self.app.game.arrows), len(LEVELS[0].arrows))

    def test_last_removal_reaches_complete_page_after_animation(self):
        arrow = Arrow("only", 0, 0, Direction.UP)
        self.app.level_index = len(LEVELS) - 1
        self.app.game = GameState(Level("UI", 1, 1, (arrow,)))
        self.app.page = Page.PLAYING

        self.app._try_arrow(arrow, 100)
        self.app._finish_animation(601)

        self.assertEqual(self.app.page, Page.COMPLETE)

    def test_restart_button_restores_removed_arrow(self):
        self.app._start_level(0)
        solution_arrow = next(
            arrow
            for arrow in self.app.game.arrows.values()
            if self.app.game.blocker_for(arrow.id) is None
        )
        self.app.game.click(solution_arrow.id)

        self.app._handle_click(self.app._restart_button().rect.center, 0)

        self.assertEqual(len(self.app.game.arrows), len(LEVELS[0].arrows))
        self.assertEqual(self.app.game.mistakes_remaining, LEVELS[0].mistakes)


if __name__ == "__main__":
    unittest.main()

