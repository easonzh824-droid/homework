from __future__ import annotations

import json
import random
from pathlib import Path
import tkinter as tk


GRID_SIZE = 24
TILE_COUNT = 20
BOARD_SIZE = GRID_SIZE * TILE_COUNT
INITIAL_DELAY = 140
MIN_DELAY = 70
BEST_SCORE_PATH = Path(__file__).with_name("snake_best_score.json")

BACKGROUND = "#f6efe5"
BOARD_BACKGROUND = "#f9f2e8"
GRID_COLOR = "#e7d9c7"
TEXT_COLOR = "#2c2218"
MUTED_COLOR = "#7a6652"
SNAKE_COLOR = "#2f7d32"
HEAD_COLOR = "#14532d"
FOOD_COLOR = "#ef4444"
PANEL_COLOR = "#fffaf2"
BUTTON_COLOR = "#2c2218"
BUTTON_TEXT = "#fff9ef"


class SnakeGame:
    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.title("貪吃蛇")
        self.root.configure(bg=BACKGROUND)
        self.root.resizable(False, False)

        self.best_score = self.load_best_score()
        self.after_id: str | None = None

        self.snake: list[tuple[int, int]] = []
        self.food = (0, 0)
        self.direction = (1, 0)
        self.queued_direction = (1, 0)
        self.score = 0
        self.started = False
        self.running = False
        self.game_over = False

        self.build_ui()
        self.bind_keys()
        self.reset_game()

    def build_ui(self) -> None:
        shell = tk.Frame(self.root, bg=BACKGROUND, padx=20, pady=20)
        shell.pack()

        title = tk.Label(
            shell,
            text="貪吃蛇",
            font=("Microsoft JhengHei", 24, "bold"),
            bg=BACKGROUND,
            fg=TEXT_COLOR,
        )
        title.pack(anchor="w")

        subtitle = tk.Label(
            shell,
            text="方向鍵或 WASD 控制移動，Space 暫停。",
            font=("Microsoft JhengHei", 11),
            bg=BACKGROUND,
            fg=MUTED_COLOR,
        )
        subtitle.pack(anchor="w", pady=(4, 16))

        hud = tk.Frame(shell, bg=BACKGROUND)
        hud.pack(fill="x", pady=(0, 16))

        score_panel = tk.Frame(hud, bg=PANEL_COLOR, bd=1, relief="solid", padx=16, pady=10)
        score_panel.pack(side="left", padx=(0, 12))
        tk.Label(
            score_panel,
            text="分數",
            font=("Microsoft JhengHei", 10),
            bg=PANEL_COLOR,
            fg=MUTED_COLOR,
        ).pack(anchor="w")
        self.score_var = tk.StringVar(value="0")
        tk.Label(
            score_panel,
            textvariable=self.score_var,
            font=("Consolas", 18, "bold"),
            bg=PANEL_COLOR,
            fg=TEXT_COLOR,
        ).pack(anchor="w")

        best_panel = tk.Frame(hud, bg=PANEL_COLOR, bd=1, relief="solid", padx=16, pady=10)
        best_panel.pack(side="left", padx=(0, 12))
        tk.Label(
            best_panel,
            text="最高分",
            font=("Microsoft JhengHei", 10),
            bg=PANEL_COLOR,
            fg=MUTED_COLOR,
        ).pack(anchor="w")
        self.best_score_var = tk.StringVar(value=str(self.best_score))
        tk.Label(
            best_panel,
            textvariable=self.best_score_var,
            font=("Consolas", 18, "bold"),
            bg=PANEL_COLOR,
            fg=TEXT_COLOR,
        ).pack(anchor="w")

        restart_button = tk.Button(
            hud,
            text="重新開始",
            font=("Microsoft JhengHei", 11, "bold"),
            bg=BUTTON_COLOR,
            fg=BUTTON_TEXT,
            activebackground="#4a3723",
            activeforeground=BUTTON_TEXT,
            padx=16,
            pady=10,
            relief="flat",
            command=self.restart_game,
        )
        restart_button.pack(side="left")

        board_frame = tk.Frame(shell, bg=PANEL_COLOR, bd=1, relief="solid", padx=12, pady=12)
        board_frame.pack()

        self.canvas = tk.Canvas(
            board_frame,
            width=BOARD_SIZE,
            height=BOARD_SIZE,
            bg=BOARD_BACKGROUND,
            highlightthickness=0,
        )
        self.canvas.pack()

        self.message_var = tk.StringVar()
        message = tk.Label(
            shell,
            textvariable=self.message_var,
            font=("Microsoft JhengHei", 11),
            bg=BACKGROUND,
            fg=MUTED_COLOR,
        )
        message.pack(anchor="w", pady=(12, 0))

    def bind_keys(self) -> None:
        for key in ("<Up>", "<w>", "<W>"):
            self.root.bind(key, lambda event: self.set_direction((0, -1)))
        for key in ("<Down>", "<s>", "<S>"):
            self.root.bind(key, lambda event: self.set_direction((0, 1)))
        for key in ("<Left>", "<a>", "<A>"):
            self.root.bind(key, lambda event: self.set_direction((-1, 0)))
        for key in ("<Right>", "<d>", "<D>"):
            self.root.bind(key, lambda event: self.set_direction((1, 0)))
        self.root.bind("<space>", lambda event: self.toggle_pause())

    def load_best_score(self) -> int:
        if not BEST_SCORE_PATH.exists():
            return 0

        try:
            data = json.loads(BEST_SCORE_PATH.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return 0

        return int(data.get("best_score", 0))

    def save_best_score(self) -> None:
        payload = {"best_score": self.best_score}
        BEST_SCORE_PATH.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def reset_game(self) -> None:
        self.cancel_scheduled_tick()
        self.snake = [(10, 12), (9, 12), (8, 12)]
        self.direction = (1, 0)
        self.queued_direction = self.direction
        self.food = self.spawn_food()
        self.score = 0
        self.started = False
        self.running = False
        self.game_over = False
        self.score_var.set("0")
        self.message_var.set("按方向鍵開始遊戲。")
        self.draw()

    def restart_game(self) -> None:
        self.reset_game()

    def spawn_food(self) -> tuple[int, int]:
        available = [
            (x, y)
            for x in range(TILE_COUNT)
            for y in range(TILE_COUNT)
            if (x, y) not in self.snake
        ]
        return random.choice(available)

    def set_direction(self, new_direction: tuple[int, int]) -> None:
        if new_direction == (-self.direction[0], -self.direction[1]):
            return

        self.queued_direction = new_direction
        if not self.started:
            self.start_game()

    def start_game(self) -> None:
        if self.game_over:
            self.reset_game()

        if self.running:
            return

        self.started = True
        self.running = True
        self.message_var.set("")
        self.schedule_tick()

    def toggle_pause(self) -> None:
        if not self.started or self.game_over:
            return

        self.running = not self.running
        if self.running:
            self.message_var.set("")
            self.schedule_tick()
            return

        self.cancel_scheduled_tick()
        self.message_var.set("已暫停，按 Space 繼續。")

    def schedule_tick(self) -> None:
        self.cancel_scheduled_tick()
        delay = max(MIN_DELAY, INITIAL_DELAY - (self.score // 5) * 8)
        self.after_id = self.root.after(delay, self.game_tick)

    def cancel_scheduled_tick(self) -> None:
        if self.after_id is not None:
            self.root.after_cancel(self.after_id)
            self.after_id = None

    def game_tick(self) -> None:
        if not self.running:
            return

        self.after_id = None
        self.direction = self.queued_direction

        head_x, head_y = self.snake[0]
        next_head = (head_x + self.direction[0], head_y + self.direction[1])

        hit_wall = (
            next_head[0] < 0
            or next_head[0] >= TILE_COUNT
            or next_head[1] < 0
            or next_head[1] >= TILE_COUNT
        )
        hit_self = next_head in self.snake
        if hit_wall or hit_self:
            self.finish_game()
            return

        self.snake.insert(0, next_head)

        if next_head == self.food:
            self.score += 1
            self.score_var.set(str(self.score))
            if self.score > self.best_score:
                self.best_score = self.score
                self.best_score_var.set(str(self.best_score))
                self.save_best_score()
            self.food = self.spawn_food()
        else:
            self.snake.pop()

        self.draw()
        self.schedule_tick()

    def finish_game(self) -> None:
        self.running = False
        self.game_over = True
        self.cancel_scheduled_tick()
        self.message_var.set(f"遊戲結束，本局得分 {self.score}。按重新開始再玩一次。")
        self.draw()

    def draw(self) -> None:
        self.canvas.delete("all")
        self.draw_grid()
        self.draw_food()
        self.draw_snake()
        if not self.started and not self.game_over:
            self.draw_overlay("按方向鍵開始")
        elif self.game_over:
            self.draw_overlay("遊戲結束")

    def draw_grid(self) -> None:
        for index in range(1, TILE_COUNT):
            offset = index * GRID_SIZE
            self.canvas.create_line(offset, 0, offset, BOARD_SIZE, fill=GRID_COLOR)
            self.canvas.create_line(0, offset, BOARD_SIZE, offset, fill=GRID_COLOR)

    def draw_food(self) -> None:
        x0 = self.food[0] * GRID_SIZE + 6
        y0 = self.food[1] * GRID_SIZE + 6
        x1 = x0 + GRID_SIZE - 12
        y1 = y0 + GRID_SIZE - 12
        self.canvas.create_oval(x0, y0, x1, y1, fill=FOOD_COLOR, outline="")
        self.canvas.create_oval(x0 + 4, y0 + 4, x0 + 8, y0 + 8, fill="#ffd5d5", outline="")

    def draw_snake(self) -> None:
        for index, (x, y) in enumerate(self.snake):
            padding = 2 if index == 0 else 3
            color = HEAD_COLOR if index == 0 else SNAKE_COLOR
            x0 = x * GRID_SIZE + padding
            y0 = y * GRID_SIZE + padding
            x1 = x0 + GRID_SIZE - padding * 2
            y1 = y0 + GRID_SIZE - padding * 2
            self.canvas.create_rectangle(x0, y0, x1, y1, fill=color, outline="")

    def draw_overlay(self, title: str) -> None:
        self.canvas.create_rectangle(
            0,
            0,
            BOARD_SIZE,
            BOARD_SIZE,
            fill="#000000",
            stipple="gray50",
            outline="",
        )
        self.canvas.create_text(
            BOARD_SIZE / 2,
            BOARD_SIZE / 2 - 10,
            text=title,
            fill="#fff8ee",
            font=("Microsoft JhengHei", 22, "bold"),
        )

    def run(self) -> None:
        self.root.mainloop()


if __name__ == "__main__":
    SnakeGame().run()
