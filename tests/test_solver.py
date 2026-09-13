import unittest
from game_core import Arrow, Direction, Level, first_blocker, solve_level
from levels import LEVELS


class SolverTests(unittest.TestCase):
    def test_cycle_is_unsolvable(self):
        level = Level('cycle', 1, 2, (
            Arrow('a', 0, 0, Direction.RIGHT),
            Arrow('b', 0, 1, Direction.LEFT),
        ))
        self.assertIsNone(solve_level(level))

    def test_free_arrow_does_not_hide_remaining_cycle(self):
        level = Level('partial cycle', 2, 2, (
            Arrow('a', 0, 0, Direction.RIGHT),
            Arrow('b', 0, 1, Direction.LEFT),
            Arrow('c', 1, 0, Direction.DOWN),
        ))
        self.assertIsNone(solve_level(level))

    def test_later_levels_have_more_dependency_layers(self):
        depths = []
        for level in LEVELS:
            remaining = list(level.arrows)
            depth = 0
            while remaining:
                free = [a for a in remaining if first_blocker(a, remaining) is None]
                self.assertTrue(free, 'Level must remain solvable')
                remaining = [a for a in remaining if a not in free]
                depth += 1
            depths.append(depth)
        self.assertLess(depths[0], depths[1])
        self.assertLess(depths[1], depths[2])
