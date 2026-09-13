"""Pure game rules for Arrow After Arrow.

This module deliberately contains no Pygame code.  It can therefore be tested
without opening a window, and the interface can be restyled independently.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from functools import lru_cache
from typing import Iterable


class Direction(str, Enum):
    UP = "up"
    DOWN = "down"
    LEFT = "left"
    RIGHT = "right"

    @property
    def delta(self) -> tuple[int, int]:
        return {
            Direction.UP: (-1, 0),
            Direction.DOWN: (1, 0),
            Direction.LEFT: (0, -1),
            Direction.RIGHT: (0, 1),
        }[self]


class MoveResult(str, Enum):
    REMOVED = "removed"
    BLOCKED = "blocked"
    IGNORED = "ignored"


class RoundStatus(str, Enum):
    PLAYING = "playing"
    WON = "won"
    LOST = "lost"


@dataclass(frozen=True, slots=True)
class Arrow:
    """One single-cell arrow on the board."""

    id: str
    row: int
    col: int
    direction: Direction


@dataclass(frozen=True, slots=True)
class Level:
    name: str
    rows: int
    cols: int
    arrows: tuple[Arrow, ...]
    mistakes: int = 3

    def __post_init__(self) -> None:
        occupied: set[tuple[int, int]] = set()
        ids: set[str] = set()
        for arrow in self.arrows:
            if not (0 <= arrow.row < self.rows and 0 <= arrow.col < self.cols):
                raise ValueError(f"Arrow {arrow.id!r} is outside the board")
            if (arrow.row, arrow.col) in occupied:
                raise ValueError(f"Duplicate cell: {(arrow.row, arrow.col)}")
            if arrow.id in ids:
                raise ValueError(f"Duplicate arrow id: {arrow.id}")
            occupied.add((arrow.row, arrow.col))
            ids.add(arrow.id)


@dataclass(frozen=True, slots=True)
class Move:
    result: MoveResult
    arrow: Arrow | None = None
    blocker: Arrow | None = None
    mistakes_remaining: int = 0
    status: RoundStatus = RoundStatus.PLAYING


def first_blocker(arrow: Arrow, arrows: Iterable[Arrow]) -> Arrow | None:
    """Return the nearest arrow in front of *arrow*, or ``None``.

    Only arrows in the same row/column and strictly ahead count as blockers.
    """

    dr, dc = arrow.direction.delta
    candidates: list[tuple[int, Arrow]] = []
    for other in arrows:
        if other.id == arrow.id:
            continue
        row_gap = other.row - arrow.row
        col_gap = other.col - arrow.col
        same_ray = (
            (dr == 0 and row_gap == 0 and col_gap * dc > 0)
            or (dc == 0 and col_gap == 0 and row_gap * dr > 0)
        )
        if same_ray:
            distance = abs(row_gap) + abs(col_gap)
            candidates.append((distance, other))
    return min(candidates, key=lambda item: item[0])[1] if candidates else None


class GameState:
    """Mutable state for one attempt at one level."""

    def __init__(self, level: Level):
        self.level = level
        self.reset()

    def reset(self) -> None:
        self.arrows: dict[str, Arrow] = {
            arrow.id: arrow for arrow in self.level.arrows
        }
        self.mistakes_remaining = self.level.mistakes
        self.status = RoundStatus.PLAYING

    def arrow_at(self, row: int, col: int) -> Arrow | None:
        return next(
            (
                arrow
                for arrow in self.arrows.values()
                if arrow.row == row and arrow.col == col
            ),
            None,
        )

    def blocker_for(self, arrow_id: str) -> Arrow | None:
        arrow = self.arrows.get(arrow_id)
        if arrow is None:
            return None
        return first_blocker(arrow, self.arrows.values())

    def click(self, arrow_id: str) -> Move:
        if self.status is not RoundStatus.PLAYING or arrow_id not in self.arrows:
            return Move(
                MoveResult.IGNORED,
                mistakes_remaining=self.mistakes_remaining,
                status=self.status,
            )

        arrow = self.arrows[arrow_id]
        blocker = first_blocker(arrow, self.arrows.values())
        if blocker is not None:
            self.mistakes_remaining -= 1
            if self.mistakes_remaining <= 0:
                self.status = RoundStatus.LOST
            return Move(
                MoveResult.BLOCKED,
                arrow,
                blocker,
                self.mistakes_remaining,
                self.status,
            )

        del self.arrows[arrow_id]
        if not self.arrows:
            self.status = RoundStatus.WON
        return Move(
            MoveResult.REMOVED,
            arrow,
            mistakes_remaining=self.mistakes_remaining,
            status=self.status,
        )


def solve_level(level: Level) -> tuple[str, ...] | None:
    """Find one mistake-free solution, used to validate hand-made levels."""

    by_id = {arrow.id: arrow for arrow in level.arrows}
    initial = frozenset(by_id)

    @lru_cache(maxsize=None)
    def search(remaining: frozenset[str]) -> tuple[str, ...] | None:
        if not remaining:
            return ()
        current = tuple(by_id[arrow_id] for arrow_id in sorted(remaining))
        for arrow_id in sorted(remaining):
            if first_blocker(by_id[arrow_id], current) is None:
                tail = search(remaining - {arrow_id})
                if tail is not None:
                    return (arrow_id, *tail)
        return None

    return search(initial)

