import unittest

from game_core import (
    Arrow,
    Direction,
    GameState,
    Level,
    MoveResult,
    RoundStatus,
    first_blocker,
    solve_level,
)
from levels import LEVELS


class PathDetectionTests(unittest.TestCase):
    def test_t01_unblocked_arrow_is_removed(self):
        level = Level("T01", 3, 3, (Arrow("right", 1, 1, Direction.RIGHT),))
        state = GameState(level)

        move = state.click("right")

        self.assertEqual(move.result, MoveResult.REMOVED)
        self.assertNotIn("right", state.arrows)

    def test_t02_blocked_arrow_stays_and_costs_one_mistake(self):
        arrows = (
            Arrow("clicked", 1, 0, Direction.RIGHT),
            Arrow("blocker", 1, 2, Direction.UP),
        )
        state = GameState(Level("T02", 3, 3, arrows))

        move = state.click("clicked")

        self.assertEqual(move.result, MoveResult.BLOCKED)
        self.assertEqual(move.blocker.id, "blocker")
        self.assertIn("clicked", state.arrows)
        self.assertEqual(state.mistakes_remaining, 2)

    def test_nearest_blocker_is_reported(self):
        clicked = Arrow("clicked", 2, 0, Direction.RIGHT)
        nearest = Arrow("near", 2, 2, Direction.UP)
        farther = Arrow("far", 2, 4, Direction.DOWN)

        self.assertEqual(first_blocker(clicked, (clicked, farther, nearest)), nearest)

    def test_all_four_directions(self):
        cases = (
            (Arrow("u", 2, 1, Direction.UP), Arrow("bu", 0, 1, Direction.LEFT)),
            (Arrow("d", 0, 1, Direction.DOWN), Arrow("bd", 2, 1, Direction.LEFT)),
            (Arrow("l", 1, 2, Direction.LEFT), Arrow("bl", 1, 0, Direction.UP)),
            (Arrow("r", 1, 0, Direction.RIGHT), Arrow("br", 1, 2, Direction.UP)),
        )
        for clicked, blocker in cases:
            with self.subTest(direction=clicked.direction):
                self.assertEqual(first_blocker(clicked, (clicked, blocker)), blocker)


class GameFlowTests(unittest.TestCase):
    def test_t03_edge_arrow_can_leave_without_index_error(self):
        cases = (
            Arrow("u", 0, 1, Direction.UP),
            Arrow("d", 2, 1, Direction.DOWN),
            Arrow("l", 1, 0, Direction.LEFT),
            Arrow("r", 1, 2, Direction.RIGHT),
        )
        for arrow in cases:
            with self.subTest(direction=arrow.direction):
                state = GameState(Level("T03", 3, 3, (arrow,)))
                self.assertEqual(state.click(arrow.id).result, MoveResult.REMOVED)

    def test_t04_clearing_all_arrows_wins(self):
        state = GameState(
            Level("T04", 2, 2, (Arrow("only", 0, 0, Direction.UP),))
        )
        state.click("only")
        self.assertEqual(state.status, RoundStatus.WON)

    def test_t05_three_blocked_clicks_lose(self):
        arrows = (
            Arrow("clicked", 1, 0, Direction.RIGHT),
            Arrow("blocker", 1, 2, Direction.UP),
        )
        state = GameState(Level("T05", 3, 3, arrows, mistakes=3))
        for _ in range(3):
            state.click("clicked")
        self.assertEqual(state.status, RoundStatus.LOST)
        self.assertEqual(state.mistakes_remaining, 0)

    def test_t06_restart_restores_layout_and_mistakes(self):
        level = Level(
            "T06",
            3,
            3,
            (
                Arrow("clicked", 1, 0, Direction.RIGHT),
                Arrow("blocker", 1, 2, Direction.UP),
            ),
        )
        state = GameState(level)
        state.click("clicked")
        state.click("blocker")

        state.reset()

        self.assertEqual(set(state.arrows), {"clicked", "blocker"})
        self.assertEqual(state.mistakes_remaining, 3)
        self.assertEqual(state.status, RoundStatus.PLAYING)

    def test_all_handmade_levels_have_a_valid_solution(self):
        for level in LEVELS:
            with self.subTest(level=level.name):
                solution = solve_level(level)
                self.assertIsNotNone(solution)
                state = GameState(level)
                for arrow_id in solution:
                    self.assertEqual(state.click(arrow_id).result, MoveResult.REMOVED)
                self.assertEqual(state.status, RoundStatus.WON)


if __name__ == "__main__":
    unittest.main()

