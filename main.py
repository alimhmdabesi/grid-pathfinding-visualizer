"""Pathfinding visualizer: watch DFS, BFS, A* and Bidirectional A* chase a target.

Run:
    python main.py                      # asks which algorithm to run
    python main.py --algorithm astar    # skip the prompt
    python main.py --seed 42            # reproducible maps
"""

from __future__ import annotations

import argparse
import asyncio
import random
import sys
from collections import deque
from pathlib import Path
from typing import Deque, Optional, Tuple

import pygame

from level import generate_level
from search import ALGORITHM_LABELS, ALGORITHMS, CellState, Grid, Position, plan_turns

# Screen and grid constants
SCREEN_WIDTH = 640
SCREEN_HEIGHT = 480
TILE_SIZE = 40
ROWS = SCREEN_HEIGHT // TILE_SIZE
COLS = SCREEN_WIDTH // TILE_SIZE
FPS = 15
WALL_NUM = 35
VICTORY_SIZE = 480
VICTORY_DELAY = 0.8  # seconds

ASSETS_DIR = Path(__file__).resolve().parent / "assets"

PLAYER_COLOR = (0, 0, 255)  # Blue
TARGET_COLOR = (255, 0, 0)  # Red
WALL_COLOR = (50, 50, 50)  # Dark gray
GRID_COLOR = (200, 200, 200)  # Light gray
BACKGROUND_COLOR = (240, 240, 240)  # Very light gray
VICTORY_COLOR = (0, 255, 0)  # Green

MENU = list(ALGORITHMS)  # ["dfs", "bfs", "astar", "bidirectional"]


def load_image(filename: str, size: Tuple[int, int], fallback_color: Tuple[int, int, int]) -> pygame.Surface:
    """Load and scale an image from ``assets/``; fall back to a plain colour square."""
    path = ASSETS_DIR / filename
    try:
        image = pygame.image.load(str(path)).convert_alpha()
        return pygame.transform.smoothscale(image, size)
    except (pygame.error, OSError) as e:  # missing file raises FileNotFoundError (an OSError)
        print(f"Unable to load image {path}: {e}")
        surface = pygame.Surface(size)
        surface.fill(fallback_color)
        return surface


def choose_algorithm(cli_choice: Optional[str]) -> str:
    """Return the algorithm key, asking on the console if it was not given."""
    if cli_choice:
        return cli_choice

    print("Which algorithm do you want to run? Press the corresponding number:")
    for number, key in enumerate(MENU, start=1):
        print(f"{number}. {ALGORITHM_LABELS[key]}")
    while True:
        try:
            answer = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            sys.exit(0)
        if answer.isdigit() and 1 <= int(answer) <= len(MENU):
            print("Thanks! Now let's see your algorithm in action!")
            return MENU[int(answer) - 1]
        print(f"Please enter a number between 1 and {len(MENU)}.")


def draw_scene(
    screen: pygame.Surface,
    grid: Grid,
    player_pos: Position,
    target_pos: Position,
    images: Tuple[pygame.Surface, pygame.Surface, pygame.Surface],
) -> None:
    player_image, target_image, wall_image = images
    screen.fill(BACKGROUND_COLOR)

    for row in range(ROWS):
        for col in range(COLS):
            rect = pygame.Rect(col * TILE_SIZE, row * TILE_SIZE, TILE_SIZE, TILE_SIZE)
            pygame.draw.rect(screen, GRID_COLOR, rect, 1)
            if grid[row][col] == CellState.WALL:
                screen.blit(wall_image, rect)

    screen.blit(player_image, (player_pos[1] * TILE_SIZE, player_pos[0] * TILE_SIZE))
    screen.blit(target_image, (target_pos[1] * TILE_SIZE, target_pos[0] * TILE_SIZE))


def new_round(algorithm: str, rng: random.Random):
    """Generate a solvable level and plan the turns for the chosen algorithm."""
    grid, player_pos, target_pos = generate_level(ROWS, COLS, WALL_NUM, rng)
    turns: Deque[Tuple[Position, Position]] = deque(plan_turns(algorithm, grid, player_pos, target_pos))
    return grid, player_pos, target_pos, turns


async def main(algorithm: str, seed: Optional[int] = None) -> None:
    rng = random.Random(seed)

    pygame.init()
    try:
        screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption(f"Pathfinding Visualizer - {ALGORITHM_LABELS[algorithm]}")

        images = (
            load_image("player.png", (TILE_SIZE, TILE_SIZE), PLAYER_COLOR),
            load_image("target.png", (TILE_SIZE, TILE_SIZE), TARGET_COLOR),
            load_image("wall.png", (TILE_SIZE, TILE_SIZE), WALL_COLOR),
        )
        victory_image = load_image("victory.png", (VICTORY_SIZE, VICTORY_SIZE), VICTORY_COLOR)
        victory_pos = ((SCREEN_WIDTH - VICTORY_SIZE) // 2, (SCREEN_HEIGHT - VICTORY_SIZE) // 2)

        grid, player_pos, target_pos, turns = new_round(algorithm, rng)
        steps = 0

        running = True
        while running:
            start_time = pygame.time.get_ticks()

            for event in pygame.event.get():
                if event.type == pygame.QUIT or (
                    event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE
                ):
                    running = False
            if not running:
                break

            draw_scene(screen, grid, player_pos, target_pos, images)
            pygame.display.flip()

            if player_pos == target_pos:
                print(f"NICE JOB! Reached the target in {steps} steps. Maybe you can pass this class after all.")
                screen.blit(victory_image, victory_pos)
                pygame.display.flip()
                await asyncio.sleep(VICTORY_DELAY)

                grid, player_pos, target_pos, turns = new_round(algorithm, rng)
                steps = 0
                continue

            if turns:
                player_pos, target_pos = turns.popleft()
                steps += 1

            # Cap frame rate
            elapsed = pygame.time.get_ticks() - start_time
            await asyncio.sleep(max(0.0, 1.0 / FPS - elapsed / 1000))
    finally:
        pygame.quit()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Visualize grid search algorithms chasing a target.")
    parser.add_argument(
        "-a",
        "--algorithm",
        choices=MENU,
        help="algorithm to run (if omitted you will be asked on the console)",
    )
    parser.add_argument("--seed", type=int, help="random seed for reproducible maps")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    asyncio.run(main(choose_algorithm(args.algorithm), args.seed))
