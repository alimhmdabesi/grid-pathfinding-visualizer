# Grid Pathfinding Visualizer


A small [pygame](https://www.pygame.org/) app that shows four classic search algorithms chasing a target across a random grid with walls: **DFS**, **BFS**, **A\*** and **Bidirectional A\***.


## Features

- Four algorithms on a 16 x 12 grid with 35 random walls
- Every generated map is guaranteed to be solvable (unreachable layouts are re-rolled)
- Choose the algorithm from the command line or from a console menu
- Reproducible maps with `--seed`
- New map automatically after each win, with a step counter printed in the console
- Search logic is separate from the pygame code and covered by unit tests

## Algorithms

| Algorithm | Data structure | Shortest path? | Notes |
|---|---|---|---|
| DFS | stack | No | Finds *a* path; often long and winding |
| BFS | queue | Yes | Explores level by level |
| A\* | priority queue | Yes | `f(n) = g(n) + h(n)` with the Manhattan heuristic |
| Bidirectional A\* | two priority queues | Yes | One search from the player, one from the target; stops when `best <= min f` of either frontier |

Movement is 4-directional and every step costs 1, so the Manhattan heuristic is admissible and consistent.

In **Bidirectional A\*** mode the target also moves: the player walks forward along the found path while the target walks backward along it, so they meet in the middle. In the other three modes the target stays still.

## Getting started

Requires Python 3.8+ (tested logic on 3.12).

```bash
git clone https://github.com/alimhmdabesi/grid-pathfinding-visualizer.git
cd grid-pathfinding-visualizer
python -m venv .venv
# Windows: .venv\Scripts\activate      macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
python main.py
```

Options:

```bash
python main.py                       # asks which algorithm to run (1-4)
python main.py --algorithm astar     # dfs | bfs | astar | bidirectional
python main.py --seed 42             # reproducible maps
```

Press `Esc` or close the window to quit.

## Tests

The search and level-generation code does not need pygame:

```bash
python -m unittest discover -s tests -v
```

## Project structure

```
.
├── main.py          # pygame window, game loop, CLI
├── search.py        # DFS, BFS, A*, Bidirectional A*, turn planning
├── level.py         # random solvable level generation
├── assets/          # player, target, wall and victory images
└── tests/           # unit tests
```

## Configuration

Grid size, number of walls and speed are constants at the top of `main.py` (`SCREEN_WIDTH`, `SCREEN_HEIGHT`, `TILE_SIZE`, `WALL_NUM`, `FPS`).

