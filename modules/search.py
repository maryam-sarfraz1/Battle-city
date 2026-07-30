# modules/search.py — Module B: Search Algorithms

import heapq
from collections import deque
from constants import *


# ------------------------------------------------------------------ #
#  BFS — Used by Basic Tank                                           #
# ------------------------------------------------------------------ #

def bfs(grid, start, goal):
    """
    Breadth-First Search: shortest-hop path ignoring terrain cost.
    Treats BRICK as passable (tank can shoot through).
    Returns list of (x,y) tiles from start (exclusive) to goal (inclusive),
    or [] if no path.
    """
    sx, sy = start
    gx, gy = goal

    if (sx, sy) == (gx, gy):
        return []

    visited = [[False] * GRID_SIZE for _ in range(GRID_SIZE)]
    parent  = {}
    queue   = deque([(sx, sy)])
    visited[sy][sx] = True

    while queue:
        x, y = queue.popleft()
        if x == gx and y == gy:
            return _reconstruct(parent, start, goal)
        for dx, dy in [(-1,0),(1,0),(0,-1),(0,1)]:
            nx, ny = x+dx, y+dy
            if 0 <= nx < GRID_SIZE and 0 <= ny < GRID_SIZE:
                if not visited[ny][nx]:
                    cell = grid[ny][nx]
                    # BFS cannot pass through STEEL or WATER
                    if cell not in (STEEL, WATER):
                        visited[ny][nx] = True
                        parent[(nx, ny)] = (x, y)
                        queue.append((nx, ny))
    return []


# ------------------------------------------------------------------ #
#  Greedy Best-First Search — Used by Fast Tank                       #
# ------------------------------------------------------------------ #

def greedy_next_step(grid, pos, goal):
    """
    Single-step greedy: pick the passable neighbour closest to goal
    (Manhattan distance). Returns (nx, ny) or None.
    """
    x, y = pos
    gx, gy = goal
    best = None
    best_h = float('inf')

    for dx, dy in [(-1,0),(1,0),(0,-1),(0,1)]:
        nx, ny = x+dx, y+dy
        if 0 <= nx < GRID_SIZE and 0 <= ny < GRID_SIZE:
            cell = grid[ny][nx]
            if cell in (STEEL, WATER):
                continue
            h = abs(nx - gx) + abs(ny - gy)
            if h < best_h:
                best_h = h
                best = (nx, ny)

    return best


# ------------------------------------------------------------------ #
#  A* Search — Used by Armor Tank                                     #
# ------------------------------------------------------------------ #

def astar(grid, start, goal):
    """
    A* with terrain-aware costs:
      EMPTY/FOREST = 1, BRICK = 3, STEEL = inf, WATER = inf
    Returns path list like bfs(), or [].
    """
    sx, sy = start
    gx, gy = goal

    if (sx, sy) == (gx, gy):
        return []

    def h(x, y):
        return abs(x - gx) + abs(y - gy)

    open_set = []
    heapq.heappush(open_set, (h(sx, sy), 0, sx, sy))
    g_cost = {(sx, sy): 0}
    parent = {}

    while open_set:
        f, g, x, y = heapq.heappop(open_set)

        if x == gx and y == gy:
            return _reconstruct(parent, start, goal)

        if g > g_cost.get((x, y), float('inf')):
            continue

        for dx, dy in [(-1,0),(1,0),(0,-1),(0,1)]:
            nx, ny = x+dx, y+dy
            if 0 <= nx < GRID_SIZE and 0 <= ny < GRID_SIZE:
                cell = grid[ny][nx]
                cost = ASTAR_COST.get(cell, float('inf'))
                if cost == float('inf'):
                    continue
                ng = g + cost
                if ng < g_cost.get((nx, ny), float('inf')):
                    g_cost[(nx, ny)] = ng
                    parent[(nx, ny)] = (x, y)
                    heapq.heappush(open_set, (ng + h(nx, ny), ng, nx, ny))
    return []


def bfs_to_nearest(grid, start, target_types):
    """BFS to find the nearest tile of any type in target_types. Returns path."""
    sx, sy = start
    visited = [[False] * GRID_SIZE for _ in range(GRID_SIZE)]
    parent  = {}
    queue   = deque([(sx, sy)])
    visited[sy][sx] = True

    while queue:
        x, y = queue.popleft()
        if grid[y][x] in target_types and (x, y) != (sx, sy):
            return _reconstruct(parent, start, (x, y))
        for dx, dy in [(-1,0),(1,0),(0,-1),(0,1)]:
            nx, ny = x+dx, y+dy
            if 0 <= nx < GRID_SIZE and 0 <= ny < GRID_SIZE:
                if not visited[ny][nx]:
                    cell = grid[ny][nx]
                    if cell not in (STEEL, WATER):
                        visited[ny][nx] = True
                        parent[(nx, ny)] = (x, y)
                        queue.append((nx, ny))
    return []


# ------------------------------------------------------------------ #
#  Shared helpers                                                      #
# ------------------------------------------------------------------ #

def _reconstruct(parent, start, goal):
    path = []
    cur = goal
    while cur != start:
        path.append(cur)
        cur = parent.get(cur)
        if cur is None:
            return []
    path.reverse()
    return path
