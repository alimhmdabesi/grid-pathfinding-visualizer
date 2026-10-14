import random
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from level import generate_level  # noqa: E402
from search import (  # noqa: E402
    ALGORITHMS,
    CellState,
    astar_path,
    bfs_path,
    bidi_astar_path,
    dfs_path,
    plan_turns,
)


def make_grid(rows, cols, walls=()):
    grid = [[CellState.EMPTY] * cols for _ in range(rows)]
    for r, c in walls:
        grid[r][c] = CellState.WALL
    return grid


def random_grid(rng, rows=12, cols=16, wall_prob=0.3):
    grid = [
        [CellState.WALL if rng.random() < wall_prob else CellState.EMPTY for _ in range(cols)]
        for _ in range(rows)
    ]
    free = [(r, c) for r in range(rows) for c in range(cols) if grid[r][c] == CellState.EMPTY]
    start, goal = rng.sample(free, 2)
    return grid, start, goal


def assert_valid_path(test, grid, path, start, goal):
    test.assertEqual(path[0], start)
    test.assertEqual(path[-1], goal)
    for (r1, c1), (r2, c2) in zip(path, path[1:]):
        test.assertEqual(abs(r1 - r2) + abs(c1 - c2), 1, "steps must be to adjacent cells")
    for r, c in path:
        test.assertNotEqual(grid[r][c], CellState.WALL)


class PathTests(unittest.TestCase):
    def test_all_algorithms_return_valid_paths(self):
        rng = random.Random(1)
        for _ in range(300):
            grid, start, goal = random_grid(rng)
            reachable = bfs_path(grid, start, goal) is not None
            for name, finder in ALGORITHMS.items():
                path = finder(grid, start, goal)
                if reachable:
                    self.assertIsNotNone(path, name)
                    assert_valid_path(self, grid, path, start, goal)
                else:
                    self.assertIsNone(path, name)

    def test_bfs_astar_and_bidirectional_are_shortest(self):
        rng = random.Random(2)
        for _ in range(300):
            grid, start, goal = random_grid(rng)
            expected = bfs_path(grid, start, goal)
            if expected is None:
                continue
            self.assertEqual(len(astar_path(grid, start, goal)), len(expected))
            self.assertEqual(len(bidi_astar_path(grid, start, goal)), len(expected))

    def test_dfs_path_is_valid_but_not_necessarily_shortest(self):
        grid = make_grid(5, 5)
        path = dfs_path(grid, (0, 0), (4, 4))
        assert_valid_path(self, grid, path, (0, 0), (4, 4))

    def test_start_equals_goal(self):
        grid = make_grid(3, 3)
        for finder in ALGORITHMS.values():
            self.assertEqual(finder(grid, (1, 1), (1, 1)), [(1, 1)])

    def test_unreachable_goal(self):
        grid = make_grid(3, 3, walls=[(0, 1), (1, 1), (2, 1)])
        for finder in ALGORITHMS.values():
            self.assertIsNone(finder(grid, (0, 0), (0, 2)))


class TurnPlanningTests(unittest.TestCase):
    def test_every_algorithm_ends_with_player_on_target(self):
        rng = random.Random(3)
        for _ in range(100):
            grid, player, target = generate_level(12, 16, 35, rng)
            for name in ALGORITHMS:
                turns = plan_turns(name, grid, player, target)
                self.assertTrue(turns, name)
                last_player, last_target = turns[-1]
                self.assertEqual(last_player, last_target, name)

                prev_p, prev_t = player, target
                for p, t in turns:
                    for prev, cur in ((prev_p, p), (prev_t, t)):
                        self.assertLessEqual(abs(prev[0] - cur[0]) + abs(prev[1] - cur[1]), 1)
                        self.assertNotEqual(grid[cur[0]][cur[1]], CellState.WALL)
                    prev_p, prev_t = p, t

    def test_bidirectional_never_swaps_through_each_other(self):
        grid = make_grid(1, 6)
        for length in range(2, 7):
            turns = plan_turns("bidirectional", grid, (0, 0), (0, length - 1))
            ps = [(0, 0)] + [p for p, _ in turns]
            ts = [(0, length - 1)] + [t for _, t in turns]
            for i in range(len(ps) - 1):
                self.assertFalse(ps[i] == ts[i + 1] and ts[i] == ps[i + 1] and ps[i] != ts[i])

    def test_unreachable_returns_no_turns(self):
        grid = make_grid(3, 3, walls=[(0, 1), (1, 1), (2, 1)])
        self.assertEqual(plan_turns("astar", grid, (0, 0), (0, 2)), [])


class LevelTests(unittest.TestCase):
    def test_levels_are_always_solvable_even_when_crowded(self):
        rng = random.Random(4)
        for _ in range(100):
            grid, player, target = generate_level(8, 8, 40, rng)
            self.assertNotEqual(player, target)
            self.assertIsNotNone(bfs_path(grid, player, target))
            self.assertEqual(sum(row.count(CellState.WALL) for row in grid), 40)

    def test_too_many_walls_raises(self):
        with self.assertRaises(ValueError):
            generate_level(2, 2, 3)


if __name__ == "__main__":
    unittest.main()
