import os
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

from app import ArrowGame, Page
from game_core import Arrow, Direction, GameState, Level, MoveResult, RoundStatus
from levels import LEVELS, SOLUTIONS


class InterfaceFlowTests(unittest.TestCase):
    def setUp(self):
        self.app = ArrowGame()

    def tearDown(self):
        pygame.quit()

    def click_arrow(self, arrow, now):
        board, cell = self.app._board_geometry()
        self.app._handle_click(self.app._arrow_center(arrow, board, cell), now)

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
        self.app._finish_animations(601)

        self.assertEqual(self.app.page, Page.COMPLETE)

    def test_another_arrow_can_be_clicked_while_first_is_flying(self):
        first = Arrow("first", 0, 0, Direction.UP)
        second = Arrow("second", 1, 1, Direction.RIGHT)
        self.app.game = GameState(Level("FAST", 2, 2, (first, second)))
        self.app.page = Page.PLAYING

        self.click_arrow(first, 100)
        self.click_arrow(second, 150)

        self.assertEqual(len(self.app.animations), 2)

        self.assertNotIn("first", self.app.game.arrows)
        self.assertNotIn("second", self.app.game.arrows)

    def test_full_campaign_via_mouse_coordinates_and_next_buttons(self):
        self.app._handle_click(self.app._start_button().rect.center, 0)
        now = 100
        for index, level in enumerate(LEVELS):
            self.assertEqual(self.app.level_index, index)
            for arrow_id in SOLUTIONS[level.name]:
                self.click_arrow(self.app.game.arrows[arrow_id], now)
                self.app.draw(now)
                now += 20
            self.app._finish_animations(now + 501)
            expected = Page.COMPLETE if index == len(LEVELS) - 1 else Page.LEVEL_WON
            self.assertEqual(self.app.page, expected)
            self.assertEqual(self.app.game.mistakes_remaining, 3)
            if expected is Page.LEVEL_WON:
                self.app._handle_click(self.app._dialog_primary_button().rect.center, now + 502)
            now += 600

    def test_failure_dialog_retry_and_animation_restart(self):
        self.app._start_level(0)
        blocked = next(a for a in self.app.game.arrows.values()
                       if self.app.game.blocker_for(a.id) is not None)
        for now in (100, 600, 1100):
            self.click_arrow(blocked, now)
            self.app.draw(now + 200)
            self.app._finish_animations(now + 431)
        self.assertEqual(self.app.page, Page.FAILED)
        self.app._handle_click(self.app._dialog_primary_button().rect.center, 1600)
        self.assertEqual(self.app.page, Page.PLAYING)
        self.assertEqual(self.app.game.mistakes_remaining, 3)
        free = next(a for a in self.app.game.arrows.values()
                    if self.app.game.blocker_for(a.id) is None)
        self.click_arrow(free, 1700)
        self.assertTrue(self.app.animations)
        self.app._handle_click(self.app._restart_button().rect.center, 1710)
        self.app._finish_animations(2300)
        self.assertFalse(self.app.animations)
        self.assertEqual(len(self.app.game.arrows), len(LEVELS[0].arrows))
        self.assertEqual(self.app.page, Page.PLAYING)

    def test_collision_locks_only_that_arrow(self):
        blocked = Arrow("blocked", 1, 0, Direction.RIGHT)
        free = Arrow("free", 1, 2, Direction.UP)
        self.app.game = GameState(Level("LOCK", 3, 3, (blocked, free)))
        self.app.page = Page.PLAYING
        board, cell = self.app._board_geometry()
        blocked_center = self.app._arrow_center(blocked, board, cell)
        free_center = self.app._arrow_center(free, board, cell)

        self.app._handle_click(blocked_center, 100)
        self.app._handle_click(blocked_center, 150)

        self.assertEqual(self.app.game.mistakes_remaining, 2)
        self.assertEqual(len(self.app.animations), 1)

        self.app._handle_click(free_center, 200)

        self.assertNotIn("free", self.app.game.arrows)
        self.assertEqual(len(self.app.animations), 2)

        # Retry immediately after the blocker leaves, before the 430ms shake ends.
        self.click_arrow(blocked, 210)
        self.assertNotIn('blocked', self.app.game.arrows)
        self.assertEqual(self.app.game.mistakes_remaining, 2)
        self.assertTrue(all(a.kind is MoveResult.REMOVED for a in self.app.animations))

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

    def test_home_button_from_result_page_is_not_overwritten_next_frame(self):
        cases = (
            (Page.LEVEL_WON, RoundStatus.WON),
            (Page.COMPLETE, RoundStatus.WON),
            (Page.FAILED, RoundStatus.LOST),
        )
        for result_page, round_status in cases:
            with self.subTest(result_page=result_page):
                self.app.page = result_page
                self.app.game.status = round_status

                self.app._handle_click(
                    self.app._dialog_secondary_button().rect.center, 100
                )
                self.app._finish_animations(101)

                self.assertEqual(self.app.page, Page.START)


if __name__ == "__main__":
    unittest.main()
