"""Hand-designed, deterministic and solver-checked levels."""

from __future__ import annotations

from game_core import Arrow, Direction, Level, solve_level


def _arrows(specs: list[tuple[int, int, Direction]]) -> tuple[Arrow, ...]:
    return tuple(
        Arrow(f"a{index + 1:02d}", row, col, direction)
        for index, (row, col, direction) in enumerate(specs)
    )


LEVELS: tuple[Level, ...] = (
    Level(
        "初识方向",
        5,
        5,
        _arrows(
            [
                (0, 2, Direction.UP),
                (1, 2, Direction.UP),
                (2, 0, Direction.LEFT),
                (2, 2, Direction.LEFT),
                (2, 4, Direction.RIGHT),
                (3, 1, Direction.DOWN),
                (4, 1, Direction.DOWN),
                (4, 4, Direction.RIGHT),
            ]
        ),
    ),
    Level(
        "交错路线",
        6,
        6,
        _arrows(
            [
                (0, 1, Direction.UP),
                (0, 4, Direction.UP),
                (1, 1, Direction.UP),
                (1, 3, Direction.RIGHT),
                (1, 5, Direction.RIGHT),
                (2, 0, Direction.LEFT),
                (2, 2, Direction.LEFT),
                (2, 4, Direction.UP),
                (3, 1, Direction.DOWN),
                (3, 3, Direction.RIGHT),
                (3, 5, Direction.RIGHT),
                (4, 2, Direction.LEFT),
                (4, 4, Direction.DOWN),
                (5, 1, Direction.DOWN),
                (5, 4, Direction.DOWN),
            ]
        ),
    ),
    Level(
        "层层解锁",
        7,
        7,
        _arrows(
            [
                (0, 0, Direction.UP),
                (0, 3, Direction.UP),
                (0, 6, Direction.RIGHT),
                (1, 1, Direction.LEFT),
                (1, 3, Direction.UP),
                (1, 5, Direction.RIGHT),
                (2, 0, Direction.LEFT),
                (2, 2, Direction.LEFT),
                (2, 4, Direction.UP),
                (2, 6, Direction.RIGHT),
                (3, 1, Direction.DOWN),
                (3, 3, Direction.RIGHT),
                (3, 5, Direction.UP),
                (4, 0, Direction.LEFT),
                (4, 2, Direction.DOWN),
                (4, 4, Direction.RIGHT),
                (4, 6, Direction.RIGHT),
                (5, 1, Direction.LEFT),
                (5, 3, Direction.DOWN),
                (5, 5, Direction.RIGHT),
                (6, 0, Direction.LEFT),
                (6, 3, Direction.DOWN),
                (6, 6, Direction.DOWN),
            ]
        ),
    ),
)


def validate_levels() -> dict[str, tuple[str, ...]]:
    """Raise immediately if a checked-in level is not solvable."""

    solutions: dict[str, tuple[str, ...]] = {}
    all_directions = set(Direction)
    for level in LEVELS:
        present = {arrow.direction for arrow in level.arrows}
        if present != all_directions:
            raise ValueError(f"{level.name} does not contain all four directions")
        solution = solve_level(level)
        if solution is None:
            raise ValueError(f"{level.name} has no solution")
        solutions[level.name] = solution
    return solutions


SOLUTIONS = validate_levels()

