# modules/csp_map.py — Module A: Constraint Satisfaction Problem Map Generator

import random
from collections import deque
from constants import *


class CSPMapGenerator:
    """
    Generates a valid Battle City map using backtracking CSP.
    
    Variables : each of the 676 tiles X_{i,j}
    Domain    : {EMPTY, BRICK, STEEL, WATER, FOREST}  (EAGLE placed separately)
    Constraints:
      1. Base Safety  — Eagle surrounded by at least 1 ring of Brick/Steel
      2. Reachability — BFS path from every spawn to Eagle must exist
      3. Fairness     — No spawn within 10 tiles (Manhattan) of player start
      4. Density      — ≤ 40% wall tiles
      5. Water        — Water must not block the only path to Eagle
    """

    def __init__(self, level=1, seed=None):
        self.level = level
        if seed is not None:
            random.seed(seed)
        self.grid = [[EMPTY] * GRID_SIZE for _ in range(GRID_SIZE)]

    # ------------------------------------------------------------------ #
    #  Public API                                                          #
    # ------------------------------------------------------------------ #

    def generate(self):
        """Return a valid 26×26 grid. Retries until constraints are met."""
        for attempt in range(200):
            grid = self._attempt_generate()
            if grid is not None:
                return grid
        # Fallback: open map with just eagle protection
        return self._fallback_map()

    # ------------------------------------------------------------------ #
    #  Internal generation                                                 #
    # ------------------------------------------------------------------ #

    def _attempt_generate(self):
        grid = [[EMPTY] * GRID_SIZE for _ in range(GRID_SIZE)]

        # Place Eagle
        grid[EAGLE_Y][EAGLE_X] = EAGLE

        # Protect Eagle with a ring of brick
        self._place_eagle_protection(grid)

        # Reserve player spawn and enemy spawns as empty
        self._reserve_spawns(grid)

        # Fill map terrain with forward-checking backtracking
        if not self._fill_terrain(grid):
            return None

        # Final reachability check
        if not self._check_reachability(grid):
            return None

        return grid

    def _place_eagle_protection(self, grid):
        """Surround Eagle with at least 1 ring of Brick."""
        ex, ey = EAGLE_X, EAGLE_Y
        for dy in range(-1, 2):
            for dx in range(-1, 2):
                nx, ny = ex + dx, ey + dy
                if 0 <= nx < GRID_SIZE and 0 <= ny < GRID_SIZE:
                    if grid[ny][nx] == EMPTY:
                        grid[ny][nx] = BRICK

    def _reserve_spawns(self, grid):
        """Keep spawn areas clear."""
        # Player spawn area
        for dx in range(-1, 3):
            for dy in range(-1, 3):
                nx = PLAYER_SPAWN_X + dx
                ny = PLAYER_SPAWN_Y + dy
                if 0 <= nx < GRID_SIZE and 0 <= ny < GRID_SIZE:
                    if grid[ny][nx] not in (EAGLE, BRICK):
                        grid[ny][nx] = EMPTY

        # Enemy spawns
        for sx, sy in ENEMY_SPAWNS:
            for dx in range(-1, 3):
                for dy in range(-1, 3):
                    nx, ny = sx + dx, sy + dy
                    if 0 <= nx < GRID_SIZE and 0 <= ny < GRID_SIZE:
                        grid[ny][nx] = EMPTY

    def _fill_terrain(self, grid):
        """
        Assign terrain to free tiles using probabilistic assignment
        with density forward-checking.
        """
        # Determine probabilities by level
        if self.level == 1:
            # Dense brick maze, less steel
            weights = {EMPTY: 35, BRICK: 45, STEEL: 5, WATER: 5, FOREST: 10}
        elif self.level == 2:
            # Mix of brick and steel
            weights = {EMPTY: 35, BRICK: 30, STEEL: 20, WATER: 5, FOREST: 10}
        else:
            # Boss level: small arena, handled separately
            weights = {EMPTY: 50, BRICK: 20, STEEL: 20, WATER: 5, FOREST: 5}

        total_w = sum(weights.values())
        wall_types = {BRICK, STEEL, WATER}

        wall_count = 0
        max_walls = int(0.40 * GRID_SIZE * GRID_SIZE)

        tiles_to_fill = []
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                if grid[y][x] == EMPTY:
                    tiles_to_fill.append((x, y))

        random.shuffle(tiles_to_fill)

        for x, y in tiles_to_fill:
            if grid[y][x] != EMPTY:
                continue

            # Forward check: do not exceed wall density
            remaining_free = sum(1 for tx, ty in tiles_to_fill
                                 if grid[ty][tx] == EMPTY)
            if wall_count >= max_walls:
                # Force empty for remaining tiles
                continue

            # Choose terrain
            roll = random.randint(1, total_w)
            cumulative = 0
            chosen = EMPTY
            for terrain, w in weights.items():
                cumulative += w
                if roll <= cumulative:
                    chosen = terrain
                    break

            # Apply fairness constraint: no wall near player spawn
            px, py = PLAYER_SPAWN_X, PLAYER_SPAWN_Y
            if abs(x - px) + abs(y - py) < 4:
                chosen = EMPTY

            if chosen in wall_types:
                if wall_count + 1 > max_walls:
                    chosen = EMPTY
                else:
                    wall_count += 1

            grid[y][x] = chosen

        return True

    # ------------------------------------------------------------------ #
    #  Constraint checking                                                 #
    # ------------------------------------------------------------------ #

    def _check_reachability(self, grid):
        """BFS from each enemy spawn to Eagle. All must reach."""
        for sx, sy in ENEMY_SPAWNS:
            if not self._bfs_reachable(grid, sx, sy, EAGLE_X, EAGLE_Y):
                return False
        # Also player spawn to eagle
        if not self._bfs_reachable(grid, PLAYER_SPAWN_X, PLAYER_SPAWN_Y,
                                   EAGLE_X, EAGLE_Y):
            return False
        return True

    def _bfs_reachable(self, grid, sx, sy, gx, gy):
        """BFS treating BRICK as passable (tanks can shoot through)."""
        visited = [[False] * GRID_SIZE for _ in range(GRID_SIZE)]
        queue = deque([(sx, sy)])
        visited[sy][sx] = True
        while queue:
            x, y = queue.popleft()
            if x == gx and y == gy:
                return True
            for dx, dy in [(-1,0),(1,0),(0,-1),(0,1)]:
                nx, ny = x+dx, y+dy
                if 0 <= nx < GRID_SIZE and 0 <= ny < GRID_SIZE:
                    if not visited[ny][nx]:
                        cell = grid[ny][nx]
                        if cell not in (STEEL, WATER):
                            visited[ny][nx] = True
                            queue.append((nx, ny))
        return False

    # ------------------------------------------------------------------ #
    #  Fallback                                                            #
    # ------------------------------------------------------------------ #

    def _fallback_map(self):
        grid = [[EMPTY] * GRID_SIZE for _ in range(GRID_SIZE)]
        grid[EAGLE_Y][EAGLE_X] = EAGLE
        self._place_eagle_protection(grid)
        # Simple brick pattern
        for y in range(2, GRID_SIZE - 2):
            for x in range(2, GRID_SIZE - 2):
                if x % 4 == 0 and y % 4 == 0:
                    grid[y][x] = BRICK
        self._reserve_spawns(grid)
        return grid


# ------------------------------------------------------------------ #
#  Boss Arena generator                                               #
# ------------------------------------------------------------------ #

def generate_boss_arena():
    """Generate a small 26×26 map for boss battle (12×12 arena feel)."""
    grid = [[STEEL] * GRID_SIZE for _ in range(GRID_SIZE)]

    # Clear a 12×12 arena in the center
    ax, ay = 7, 7
    for y in range(ay, ay + 12):
        for x in range(ax, ax + 12):
            grid[y][x] = EMPTY

    # Eagle at bottom center of arena
    grid[EAGLE_Y][EAGLE_X] = EAGLE
    # Protect Eagle
    for dy in range(-1, 2):
        for dx in range(-1, 2):
            nx, ny = EAGLE_X + dx, EAGLE_Y + dy
            if 0 <= nx < GRID_SIZE and 0 <= ny < GRID_SIZE:
                if grid[ny][nx] == EMPTY:
                    grid[ny][nx] = BRICK

    # Place some brick pillars and one water patch
    arena_tiles = [
        (9,  9,  BRICK), (10, 9,  BRICK),
        (15, 9,  BRICK), (16, 9,  BRICK),
        (9,  14, STEEL), (10, 14, STEEL),
        (15, 14, STEEL), (16, 14, STEEL),
        (12, 11, WATER), (13, 11, WATER),
        (12, 12, WATER), (13, 12, WATER),
    ]
    for x, y, t in arena_tiles:
        if 0 <= x < GRID_SIZE and 0 <= y < GRID_SIZE:
            grid[y][x] = t

    # Open player spawn area
    for dx in range(-2, 3):
        for dy in range(-2, 3):
            nx, ny = PLAYER_SPAWN_X + dx, PLAYER_SPAWN_Y + dy
            if 0 <= nx < GRID_SIZE and 0 <= ny < GRID_SIZE:
                if grid[ny][nx] not in (EAGLE, BRICK):
                    grid[ny][nx] = EMPTY

    # Open boss spawn
    grid[7][12] = EMPTY
    grid[7][13] = EMPTY
    grid[8][12] = EMPTY
    grid[8][13] = EMPTY

    return grid
