"""Random level generation (pure logic, no pygame)."""

from __future__ import annotations

import random
from typing import List, Tuple

from search import CellState, Grid, Position, bfs_path


def generate_level(
    rows: int,
    cols: int,
    num_walls: int,
    rng: random.Random | None = None,
) -> Tuple[Grid, Position, Position]:
    """Create a random grid and return ``(grid, player_pos, target_pos)``.

    Walls, player and target are placed on distinct cells. Layouts where the
    walls cut the player off from the target are discarded and regenerated,
    so every returned level is solvable.
    """
    if num_walls < 0 or num_walls > rows * cols - 2:
        raise ValueError("num_walls must leave room for the player and the target")

    rng = rng or random.Random()
    cells: List[Position] = [(r, c) for r in range(rows) for c in range(cols)]

    while True:
        picked = rng.sample(cells, num_walls + 2)
        player, target = picked[-2], picked[-1]

        grid: Grid = [[CellState.EMPTY] * cols for _ in range(rows)]
        for r, c in picked[:num_walls]:
            grid[r][c] = CellState.WALL

        if bfs_path(grid, player, target) is not None:
            return grid, player, target
