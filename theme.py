"""Visual tokens for the default paper-and-ink theme."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Theme:
    background: str = "#F3EEDF"
    surface: str = "#FBF8EF"
    ink: str = "#292824"
    muted: str = "#777064"
    grid: str = "#C9C1AF"
    grid_soft: str = "#E5DECF"
    success: str = "#66866A"
    success_dark: str = "#4D6D52"
    danger: str = "#B55445"
    danger_soft: str = "#EAC9C0"
    white: str = "#FFFFFF"
    overlay: tuple[int, int, int, int] = (41, 40, 36, 145)

    window_size: tuple[int, int] = (1000, 760)
    board_max_size: int = 490
    corner_radius: int = 16


PAPER = Theme()
