"""Grid search algorithms: DFS, BFS, A* and Bidirectional A*.

Everything in this module is pure logic (no pygame), so it can be tested
without a display. A grid is a list of rows; each cell is a ``CellState``.
Movement is 4-directional with a uniform step cost of 1.

Every ``*_path`` function returns the list of cells from ``start`` to
``goal`` (both included), or ``None`` if the goal cannot be reached.
"""

from __future__ import annotations

import heapq
from collections import deque
from enum import Enum
from itertools import count
from typing import Callable, Dict, Iterator, List, Optional, Set, Tuple

Position = Tuple[int, int]


class CellState(Enum):
    EMPTY = 0
    WALL = 1


Grid = List[List[CellState]]
Path = List[Position]

# Order matters for DFS (the last direction is explored first).
DIRECTIONS = ((1, 0), (-1, 0), (0, 1), (0, -1))
INFINITY = float("inf")


def neighbors(grid: Grid, node: Position) -> Iterator[Position]:
    """Yield the walkable 4-neighbours of ``node`` that are inside the grid."""
    rows, cols = len(grid), len(grid[0])
    row, col = node
    for d_row, d_col in DIRECTIONS:
        n_row, n_col = row + d_row, col + d_col
        if 0 <= n_row < rows and 0 <= n_col < cols and grid[n_row][n_col] != CellState.WALL:
            yield (n_row, n_col)


def heuristic(a: Position, b: Position) -> int:
    """Manhattan distance: admissible and consistent for 4-directional unit-cost grids."""
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def _reconstruct(parent: Dict[Position, Optional[Position]], node: Position) -> Path:
    path = [node]
    while parent[node] is not None:
        node = parent[node]  # type: ignore[assignment]
        path.append(node)
    path.reverse()
    return path


# --------------------------------------------------------------------------- #
# Depth-first search
# --------------------------------------------------------------------------- #
def dfs_path(grid: Grid, start: Position, goal: Position) -> Optional[Path]:
    """Iterative DFS with an explicit stack. Finds *a* path, not the shortest."""
    parent: Dict[Position, Optional[Position]] = {}
    stack: List[Tuple[Position, Optional[Position]]] = [(start, None)]
    while stack:
        node, came_from = stack.pop()
        if node in parent:
            continue
        parent[node] = came_from
        if node == goal:
            return _reconstruct(parent, node)
        for nxt in neighbors(grid, node):
            if nxt not in parent:
                stack.append((nxt, node))
    return None


# --------------------------------------------------------------------------- #
# Breadth-first search
# --------------------------------------------------------------------------- #
def bfs_path(grid: Grid, start: Position, goal: Position) -> Optional[Path]:
    """BFS with a queue. Returns a shortest path (all steps cost 1)."""
    parent: Dict[Position, Optional[Position]] = {start: None}
    queue = deque([start])
    while queue:
        node = queue.popleft()
        if node == goal:
            return _reconstruct(parent, node)
        for nxt in neighbors(grid, node):
            if nxt not in parent:
                parent[nxt] = node
                queue.append(nxt)
    return None


# --------------------------------------------------------------------------- #
# A*
# --------------------------------------------------------------------------- #
def astar_path(grid: Grid, start: Position, goal: Position) -> Optional[Path]:
    """A* with the Manhattan heuristic. Returns a shortest path."""
    tie = count()  # keeps heap comparisons away from tuples of positions
    open_heap: List[Tuple[int, int, Position]] = [(heuristic(start, goal), next(tie), start)]
    g_cost: Dict[Position, int] = {start: 0}
    parent: Dict[Position, Optional[Position]] = {start: None}
    closed: Set[Position] = set()

    while open_heap:
        _, _, node = heapq.heappop(open_heap)
        if node in closed:
            continue
        if node == goal:
            return _reconstruct(parent, node)
        closed.add(node)
        for nxt in neighbors(grid, node):
            new_g = g_cost[node] + 1
            if new_g < g_cost.get(nxt, INFINITY):
                g_cost[nxt] = new_g
                parent[nxt] = node
                heapq.heappush(open_heap, (new_g + heuristic(nxt, goal), next(tie), nxt))
    return None


# --------------------------------------------------------------------------- #
# Bidirectional A*
# --------------------------------------------------------------------------- #
def bidi_astar_path(grid: Grid, start: Position, goal: Position) -> Optional[Path]:
    """Bidirectional A*: two A* searches (start->goal and goal->start) run in turn.

    ``best`` is the cheapest complete path found so far (where the two search
    frontiers touch). With a consistent heuristic the search can stop as soon
    as the smallest f-value of either frontier is >= ``best``, and the path is
    then guaranteed to be shortest.
    """
    if start == goal:
        return [start]

    tie = count()
    g_fwd: Dict[Position, int] = {start: 0}
    g_bwd: Dict[Position, int] = {goal: 0}
    parent_fwd: Dict[Position, Optional[Position]] = {start: None}
    parent_bwd: Dict[Position, Optional[Position]] = {goal: None}
    open_fwd: List[Tuple[int, int, Position]] = [(heuristic(start, goal), next(tie), start)]
    open_bwd: List[Tuple[int, int, Position]] = [(heuristic(goal, start), next(tie), goal)]
    closed_fwd: Set[Position] = set()
    closed_bwd: Set[Position] = set()

    best: float = INFINITY
    meeting: Optional[Position] = None

    def drop_stale(heap: List[Tuple[int, int, Position]], closed: Set[Position]) -> None:
        while heap and heap[0][2] in closed:
            heapq.heappop(heap)

    def expand(
        heap: List[Tuple[int, int, Position]],
        closed: Set[Position],
        g_own: Dict[Position, int],
        g_other: Dict[Position, int],
        parent: Dict[Position, Optional[Position]],
        target: Position,
    ) -> None:
        nonlocal best, meeting
        _, _, node = heapq.heappop(heap)
        closed.add(node)
        for nxt in neighbors(grid, node):
            new_g = g_own[node] + 1
            if new_g < g_own.get(nxt, INFINITY):
                g_own[nxt] = new_g
                parent[nxt] = node
                heapq.heappush(heap, (new_g + heuristic(nxt, target), next(tie), nxt))
            if nxt in g_other:
                total = g_own[nxt] + g_other[nxt]
                if total < best:
                    best, meeting = total, nxt

    while True:
        drop_stale(open_fwd, closed_fwd)
        drop_stale(open_bwd, closed_bwd)
        if not open_fwd or not open_bwd:
            break
        if best <= max(open_fwd[0][0], open_bwd[0][0]):
            break
        if open_fwd[0][0] <= open_bwd[0][0]:
            expand(open_fwd, closed_fwd, g_fwd, g_bwd, parent_fwd, goal)
        else:
            expand(open_bwd, closed_bwd, g_bwd, g_fwd, parent_bwd, start)

    if meeting is None:
        return None
    first_half = _reconstruct(parent_fwd, meeting)  # start .. meeting
    second_half = _reconstruct(parent_bwd, meeting)  # goal .. meeting
    second_half.reverse()  # meeting .. goal
    return first_half + second_half[1:]


# --------------------------------------------------------------------------- #
# Turn planning (what the game animates)
# --------------------------------------------------------------------------- #
ALGORITHMS: Dict[str, Callable[[Grid, Position, Position], Optional[Path]]] = {
    "dfs": dfs_path,
    "bfs": bfs_path,
    "astar": astar_path,
    "bidirectional": bidi_astar_path,
}

ALGORITHM_LABELS: Dict[str, str] = {
    "dfs": "DFS",
    "bfs": "BFS",
    "astar": "A*",
    "bidirectional": "Bidirectional A*",
}


def plan_turns(
    algorithm: str, grid: Grid, player: Position, target: Position
) -> List[Tuple[Position, Position]]:
    """Return the ``(player_pos, target_pos)`` after every turn until they meet.

    The path is computed once and then followed, so the result does not
    depend on how a search breaks ties from different starting cells (which
    could otherwise make DFS oscillate between two cells forever).

    * ``dfs``, ``bfs``, ``astar``: only the player moves toward the target.
    * ``bidirectional``: the player walks forward along the path while the
      target walks backward along it, so they meet in the middle.

    Returns an empty list if the target is unreachable (or already reached).
    """
    path = ALGORITHMS[algorithm](grid, player, target)
    if path is None:
        return []

    if algorithm != "bidirectional":
        return [(cell, target) for cell in path[1:]]

    turns: List[Tuple[Position, Position]] = []
    lo, hi = 0, len(path) - 1
    while lo < hi:
        lo += 1
        if lo < hi:  # if the player just stepped onto the target, it stays put
            hi -= 1
        turns.append((path[lo], path[hi]))
    return turns
