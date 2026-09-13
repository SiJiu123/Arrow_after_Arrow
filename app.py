"""Pygame interface for the Arrow After Arrow puzzle."""

from __future__ import annotations

import argparse
import math
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

import pygame

from game_core import Arrow, Direction, GameState, MoveResult, RoundStatus
from levels import LEVELS, SOLUTIONS
from theme import PAPER, Theme


class Page(str, Enum):
    START = "start"
    PLAYING = "playing"
    LEVEL_WON = "level_won"
    FAILED = "failed"
    COMPLETE = "complete"


@dataclass(slots=True)
class Animation:
    kind: MoveResult
    arrow: Arrow
    started_at: int
    duration: int
    blocker: Arrow | None = None


@dataclass(frozen=True, slots=True)
class Button:
    rect: pygame.Rect
    label: str
    primary: bool = True

    def contains(self, position: tuple[int, int]) -> bool:
        return self.rect.collidepoint(position)


class ArrowGame:
    def __init__(self, theme: Theme = PAPER) -> None:
        pygame.init()
        pygame.display.set_caption("一箭又一箭")
        self.theme = theme
        self.screen = pygame.display.set_mode(theme.window_size)
        self.clock = pygame.time.Clock()
        self.fonts = self._load_fonts()
        self.page = Page.START
        self.level_index = 0
        self.game = GameState(LEVELS[0])
        self.animations: list[Animation] = []
        self.notice = "观察箭头前方，选择没有阻挡的一支"
        self.running = True
        self.mouse_position = (0, 0)

    def _load_fonts(self) -> dict[str, pygame.font.Font]:
        candidates = (
            Path("C:/Windows/Fonts/msyh.ttc"),
            Path("C:/Windows/Fonts/msyh.ttf"),
            Path("C:/Windows/Fonts/simhei.ttf"),
        )
        font_path = next((path for path in candidates if path.exists()), None)

        def build(size: int, bold: bool = False) -> pygame.font.Font:
            # Direct file loading also works on systems with malformed font
            # registry entries, where pygame.font.SysFont may fail.
            font = pygame.font.Font(str(font_path) if font_path else None, size)
            font.set_bold(bold)
            return font

        return {
            "title": build(58, bold=True),
            "hero": build(32, bold=True),
            "heading": build(25, bold=True),
            "body": build(18),
            "small": build(15),
            "number": build(29, bold=True),
        }

    def run(self) -> None:
        while self.running:
            now = pygame.time.get_ticks()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.MOUSEMOTION:
                    self.mouse_position = event.pos
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    self._handle_click(event.pos, now)

            self._finish_animations(now)
            self.draw(now)
            pygame.display.flip()
            self.clock.tick(60)
        pygame.quit()

    def _handle_click(self, position: tuple[int, int], now: int) -> None:
        if self.page is Page.START:
            if self._start_button().contains(position):
                self._start_level(0)
            return

        if self.page is Page.PLAYING:
            if self._restart_button().contains(position):
                self._restart_level()
                return
            if self._home_button().contains(position):
                self.page = Page.START
                self.animations.clear()
                return
            cell = self._cell_at(position)
            if cell is None:
                return
            arrow = self.game.arrow_at(*cell)
            collision_running = arrow is not None and any(
                animation.kind is MoveResult.BLOCKED
                and animation.arrow.id == arrow.id
                for animation in self.animations
            )
            if arrow is not None:
                if collision_running:
                    if self.game.blocker_for(arrow.id) is not None:
                        return
                    # The blocker may have flown away during this feedback.
                    self.animations = [
                        animation for animation in self.animations
                        if animation.arrow.id != arrow.id
                    ]
                self._try_arrow(arrow, now)
            return

        if self.page is Page.LEVEL_WON:
            if self._dialog_primary_button().contains(position):
                self._start_level(self.level_index + 1)
            elif self._dialog_secondary_button().contains(position):
                self.page = Page.START
            return

        if self.page is Page.FAILED:
            if self._dialog_primary_button().contains(position):
                self._restart_level()
            elif self._dialog_secondary_button().contains(position):
                self.page = Page.START
            return

        if self.page is Page.COMPLETE:
            if self._dialog_primary_button().contains(position):
                self._start_level(0)
            elif self._dialog_secondary_button().contains(position):
                self.page = Page.START

    def _try_arrow(self, arrow: Arrow, now: int) -> None:
        move = self.game.click(arrow.id)
        if move.result is MoveResult.REMOVED:
            self.animations.append(Animation(MoveResult.REMOVED, arrow, now, 500))
            self.notice = "路径畅通，箭头飞出棋盘"
        elif move.result is MoveResult.BLOCKED:
            self.animations.append(
                Animation(MoveResult.BLOCKED, arrow, now, 430, blocker=move.blocker)
            )
            self.notice = f"前方有阻挡，剩余 {move.mistakes_remaining} 次机会"

    def _finish_animations(self, now: int) -> None:
        if self.page is not Page.PLAYING:
            return
        self.animations = [
            animation
            for animation in self.animations
            if now - animation.started_at < animation.duration
        ]
        if self.animations:
            return
        if self.game.status is RoundStatus.WON:
            self.page = (
                Page.COMPLETE
                if self.level_index == len(LEVELS) - 1
                else Page.LEVEL_WON
            )
        elif self.game.status is RoundStatus.LOST:
            self.page = Page.FAILED

    def _start_level(self, index: int) -> None:
        self.level_index = index
        self.game = GameState(LEVELS[index])
        self.page = Page.PLAYING
        self.animations.clear()
        self.notice = "观察箭头前方，选择没有阻挡的一支"

    def _restart_level(self) -> None:
        self.game.reset()
        self.page = Page.PLAYING
        self.animations.clear()
        self.notice = "本关已重新开始"

    def _board_geometry(self) -> tuple[pygame.Rect, int]:
        level = self.game.level
        cell = min(
            self.theme.board_max_size // level.rows,
            self.theme.board_max_size // level.cols,
        )
        width, height = level.cols * cell, level.rows * cell
        rect = pygame.Rect(
            (self.theme.window_size[0] - width) // 2,
            148 + (self.theme.board_max_size - height) // 2,
            width,
            height,
        )
        return rect, cell

    def _cell_at(self, position: tuple[int, int]) -> tuple[int, int] | None:
        board, cell = self._board_geometry()
        if not board.collidepoint(position):
            return None
        col = (position[0] - board.left) // cell
        row = (position[1] - board.top) // cell
        return int(row), int(col)

    def _start_button(self) -> Button:
        return Button(pygame.Rect(402, 574, 196, 54), "开始游戏")

    def _restart_button(self) -> Button:
        return Button(pygame.Rect(354, 698, 142, 42), "重新开始", False)

    def _home_button(self) -> Button:
        return Button(pygame.Rect(510, 698, 136, 42), "返回首页", False)

    def _dialog_primary_button(self) -> Button:
        label = {
            Page.LEVEL_WON: "进入下一关",
            Page.FAILED: "重新挑战",
            Page.COMPLETE: "再玩一次",
        }.get(self.page, "继续")
        return Button(pygame.Rect(383, 474, 234, 50), label)

    def _dialog_secondary_button(self) -> Button:
        return Button(pygame.Rect(410, 540, 180, 40), "返回首页", False)

    def draw(self, now: int | None = None) -> None:
        now = pygame.time.get_ticks() if now is None else now
        self.screen.fill(self.theme.background)
        if self.page is Page.START:
            self._draw_start()
            return
        self._draw_game(now)
        if self.page is not Page.PLAYING:
            self._draw_result_dialog()

    def _draw_start(self) -> None:
        self._draw_text("一箭又一箭", self.fonts["title"], self.theme.ink, (500, 154))
        self._draw_text(
            "看清方向，按正确顺序让所有箭头离开棋盘",
            self.fonts["body"],
            self.theme.muted,
            (500, 217),
        )

        emblem_center = (500, 363)
        pygame.draw.circle(self.screen, self.theme.surface, emblem_center, 106)
        pygame.draw.circle(self.screen, self.theme.grid, emblem_center, 106, 2)
        directions = (
            (Direction.UP, (500, 317)),
            (Direction.RIGHT, (546, 363)),
            (Direction.DOWN, (500, 409)),
            (Direction.LEFT, (454, 363)),
        )
        for direction, center in directions:
            self._draw_arrow(center, direction, 64, self.theme.ink, 5)

        self._draw_text(
            "前方没有其他箭头时，点击即可飞出",
            self.fonts["small"],
            self.theme.muted,
            (500, 507),
        )
        self._draw_button(self._start_button())
        self._draw_text(
            "3 个固定关卡  ·  每关 3 次失误机会",
            self.fonts["small"],
            self.theme.muted,
            (500, 672),
        )

    def _draw_game(self, now: int) -> None:
        level = self.game.level
        self._draw_text(
            f"第 {self.level_index + 1} 关  {level.name}",
            self.fonts["heading"],
            self.theme.ink,
            (84, 48),
            anchor="midleft",
        )
        self._draw_stat("剩余箭头", str(len(self.game.arrows)), 600)
        self._draw_stat("失误机会", str(self.game.mistakes_remaining), 788)

        pygame.draw.line(self.screen, self.theme.grid, (72, 94), (928, 94), 1)
        self._draw_board(now)
        notice_color = (
            self.theme.danger
            if any(
                animation.kind is MoveResult.BLOCKED
                for animation in self.animations
            )
            else self.theme.muted
        )
        self._draw_text(
            self.notice, self.fonts["small"], notice_color, (500, 674)
        )
        self._draw_button(self._restart_button())
        self._draw_button(self._home_button())

    def _draw_stat(self, label: str, value: str, x: int) -> None:
        self._draw_text(label, self.fonts["small"], self.theme.muted, (x, 38))
        color = self.theme.danger if label == "失误机会" and value == "0" else self.theme.ink
        self._draw_text(value, self.fonts["number"], color, (x, 67))

    def _draw_board(self, now: int) -> None:
        board, cell = self._board_geometry()
        pygame.draw.rect(
            self.screen,
            self.theme.surface,
            board.inflate(22, 22),
            border_radius=self.theme.corner_radius,
        )
        pygame.draw.rect(
            self.screen,
            self.theme.grid,
            board.inflate(22, 22),
            2,
            border_radius=self.theme.corner_radius,
        )

        hover_cell = self._cell_at(self.mouse_position)
        if self.page is Page.PLAYING and hover_cell:
            row, col = hover_cell
            hover_rect = pygame.Rect(
                board.left + col * cell,
                board.top + row * cell,
                cell,
                cell,
            )
            pygame.draw.rect(self.screen, self.theme.grid_soft, hover_rect)

        for row in range(self.game.level.rows + 1):
            y = board.top + row * cell
            pygame.draw.line(self.screen, self.theme.grid_soft, (board.left, y), (board.right, y), 1)
        for col in range(self.game.level.cols + 1):
            x = board.left + col * cell
            pygame.draw.line(self.screen, self.theme.grid_soft, (x, board.top), (x, board.bottom), 1)
        pygame.draw.rect(self.screen, self.theme.grid, board, 2)

        for animation in self.animations:
            if animation.kind is not MoveResult.BLOCKED or animation.blocker is None:
                continue
            blocker = animation.blocker
            if blocker.id not in self.game.arrows:
                continue
            blocker_rect = pygame.Rect(
                board.left + blocker.col * cell + 5,
                board.top + blocker.row * cell + 5,
                cell - 10,
                cell - 10,
            )
            pygame.draw.rect(
                self.screen,
                self.theme.danger_soft,
                blocker_rect,
                3,
                border_radius=10,
            )

        for arrow in self.game.arrows.values():
            offset = (0.0, 0.0)
            color = self.theme.ink
            collision = next(
                (
                    animation
                    for animation in self.animations
                    if animation.kind is MoveResult.BLOCKED
                    and animation.arrow.id == arrow.id
                ),
                None,
            )
            if collision is not None:
                offset, color = self._collision_style(now, collision)
            center = self._arrow_center(arrow, board, cell, offset)
            self._draw_arrow(center, arrow.direction, cell * 0.52, color, max(4, cell // 15))

        for animation in self.animations:
            if animation.kind is not MoveResult.REMOVED:
                continue
            progress = min(1.0, (now - animation.started_at) / animation.duration)
            offset = self._flight_offset(animation.arrow, board, cell, progress)
            center = self._arrow_center(animation.arrow, board, cell, offset)
            self._draw_arrow(
                center,
                animation.arrow.direction,
                cell * 0.52,
                self.theme.success,
                max(4, cell // 15),
            )

    def _collision_style(
        self, now: int, animation: Animation
    ) -> tuple[tuple[float, float], str]:
        progress = min(1.0, (now - animation.started_at) / animation.duration)
        dr, dc = animation.arrow.direction.delta
        forward = math.sin(math.pi * progress) * 11
        shake = math.sin(progress * math.pi * 8) * 3 * (1 - progress)
        return ((dc * forward + dr * shake, dr * forward + dc * shake), self.theme.danger)

    def _flight_offset(
        self, arrow: Arrow, board: pygame.Rect, cell: int, progress: float
    ) -> tuple[float, float]:
        eased = progress * progress * (3 - 2 * progress)
        distances = {
            Direction.UP: (0, -(arrow.row + 1.7) * cell),
            Direction.DOWN: (0, (self.game.level.rows - arrow.row + 0.7) * cell),
            Direction.LEFT: (-(arrow.col + 1.7) * cell, 0),
            Direction.RIGHT: ((self.game.level.cols - arrow.col + 0.7) * cell, 0),
        }
        dx, dy = distances[arrow.direction]
        return dx * eased, dy * eased

    @staticmethod
    def _arrow_center(
        arrow: Arrow,
        board: pygame.Rect,
        cell: int,
        offset: tuple[float, float] = (0, 0),
    ) -> tuple[int, int]:
        return (
            round(board.left + (arrow.col + 0.5) * cell + offset[0]),
            round(board.top + (arrow.row + 0.5) * cell + offset[1]),
        )

    def _draw_arrow(
        self,
        center: tuple[int, int],
        direction: Direction,
        length: float,
        color: str,
        width: int,
    ) -> None:
        dr, dc = direction.delta
        vx, vy = dc, dr
        half = length * 0.46
        start = (center[0] - vx * half, center[1] - vy * half)
        tip = (center[0] + vx * half, center[1] + vy * half)
        shaft_end = (center[0] + vx * length * 0.16, center[1] + vy * length * 0.16)
        pygame.draw.line(self.screen, color, start, shaft_end, width)
        perpendicular = (-vy, vx)
        head_depth = length * 0.30
        head_width = length * 0.24
        base = (tip[0] - vx * head_depth, tip[1] - vy * head_depth)
        points = [
            tip,
            (base[0] + perpendicular[0] * head_width, base[1] + perpendicular[1] * head_width),
            (base[0] - perpendicular[0] * head_width, base[1] - perpendicular[1] * head_width),
        ]
        pygame.draw.polygon(self.screen, color, points)

    def _draw_button(self, button: Button) -> None:
        hovered = button.contains(self.mouse_position)
        if button.primary:
            fill = self.theme.success_dark if hovered else self.theme.success
            text_color = self.theme.white
            border = 0
        else:
            fill = self.theme.grid_soft if hovered else self.theme.surface
            text_color = self.theme.ink
            border = 1
        pygame.draw.rect(
            self.screen,
            fill,
            button.rect,
            border_radius=button.rect.height // 2,
        )
        if border:
            pygame.draw.rect(
                self.screen,
                self.theme.grid,
                button.rect,
                border,
                border_radius=button.rect.height // 2,
            )
        self._draw_text(
            button.label,
            self.fonts["body"],
            text_color,
            button.rect.center,
        )

    def _draw_result_dialog(self) -> None:
        veil = pygame.Surface(self.theme.window_size, pygame.SRCALPHA)
        veil.fill(self.theme.overlay)
        self.screen.blit(veil, (0, 0))
        panel = pygame.Rect(312, 232, 376, 378)
        pygame.draw.rect(
            self.screen,
            self.theme.surface,
            panel,
            border_radius=24,
        )

        content = {
            Page.LEVEL_WON: ("本关完成", "顺序正确，下一关会更有挑战", self.theme.success),
            Page.FAILED: ("挑战失败", "失误机会已用完，再观察一次路线", self.theme.danger),
            Page.COMPLETE: ("全部通关", "三关箭头已经全部飞出棋盘", self.theme.success),
        }
        title, subtitle, accent = content[self.page]
        pygame.draw.circle(self.screen, accent, (500, 302), 34)
        if self.page is Page.FAILED:
            self._draw_text("!", self.fonts["hero"], self.theme.white, (500, 301))
        else:
            pygame.draw.line(
                self.screen,
                self.theme.white,
                (485, 302),
                (496, 313),
                5,
            )
            pygame.draw.line(
                self.screen,
                self.theme.white,
                (496, 313),
                (516, 289),
                5,
            )
        self._draw_text(title, self.fonts["hero"], self.theme.ink, (500, 371))
        self._draw_text(subtitle, self.fonts["small"], self.theme.muted, (500, 414))
        self._draw_button(self._dialog_primary_button())
        self._draw_button(self._dialog_secondary_button())

    def _draw_text(
        self,
        text: str,
        font: pygame.font.Font,
        color: str,
        position: tuple[int, int],
        anchor: str = "center",
    ) -> pygame.Rect:
        surface = font.render(text, True, color)
        rect = surface.get_rect()
        setattr(rect, anchor, position)
        self.screen.blit(surface, rect)
        return rect

    def save_sample_screens(self, output_dir: Path) -> list[Path]:
        """Render reproducible README/blog screenshots without manual cropping."""

        output_dir.mkdir(parents=True, exist_ok=True)
        paths: list[Path] = []

        self.page = Page.START
        self.draw(0)
        start_path = output_dir / "start-screen.png"
        pygame.image.save(self.screen, start_path)
        paths.append(start_path)

        self._start_level(1)
        self.draw(0)
        game_path = output_dir / "game-screen.png"
        pygame.image.save(self.screen, game_path)
        paths.append(game_path)

        self._start_level(len(LEVELS) - 1)
        now = 0
        for arrow_id in SOLUTIONS[self.game.level.name]:
            board, cell = self._board_geometry()
            self._handle_click(self._arrow_center(self.game.arrows[arrow_id], board, cell), now)
            now += 20
        self._finish_animations(now + 501)
        self.draw(now + 501)
        complete_path = output_dir / "complete-screen.png"
        pygame.image.save(self.screen, complete_path)
        paths.append(complete_path)

        self._start_level(0)
        blocked = next(a for a in self.game.arrows.values()
                       if self.game.blocker_for(a.id) is not None)
        for now in (0, 500, 1000):
            board, cell = self._board_geometry()
            self._handle_click(self._arrow_center(blocked, board, cell), now)
            self._finish_animations(now + 431)
        self.draw(1500)
        failed_path = output_dir / "failed-screen.png"
        pygame.image.save(self.screen, failed_path)
        paths.append(failed_path)
        return paths


def main() -> None:
    parser = argparse.ArgumentParser(description="一箭又一箭小游戏")
    parser.add_argument(
        "--screenshots",
        type=Path,
        help="将开始、游戏、通关和失败示例界面保存到指定文件夹后退出",
    )
    args = parser.parse_args()
    app = ArrowGame()
    if args.screenshots:
        for path in app.save_sample_screens(args.screenshots):
            print(path)
        pygame.quit()
        return
    app.run()


if __name__ == "__main__":
    main()
