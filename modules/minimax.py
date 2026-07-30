# modules/minimax.py — Module C: Adversarial Search (Boss Tank)

from constants import *


# ------------------------------------------------------------------ #
#  Minimax + Alpha-Beta for Boss Tank                                 #
# ------------------------------------------------------------------ #

class MinimaxAgent:
    """
    Minimax with Alpha-Beta Pruning for the Boss Tank.
    MAX player = Boss Tank (maximises heuristic)
    MIN player = Human player (minimises Boss heuristic)
    """

    def __init__(self):
        self.nodes_without_pruning = 0
        self.nodes_with_pruning    = 0

    def choose_action(self, boss, player, grid, depth):
        """Return best action for boss. Also records node counts."""
        self.nodes_with_pruning    = 0
        self.nodes_without_pruning = 0

        # Count nodes without pruning first (for reporting)
        self._minimax_no_prune(boss, player, grid, depth, True)

        # Now run with alpha-beta
        best_val  = float('-inf')
        best_action = None
        alpha, beta = float('-inf'), float('inf')

        for action in self._get_boss_actions(boss, grid):
            new_boss, new_grid = self._apply_boss_action(boss, player, grid, action)
            val = self._minimax(new_boss, player, new_grid, depth - 1,
                                False, alpha, beta)
            if val > best_val:
                best_val    = val
                best_action = action
            alpha = max(alpha, val)

        return best_action

    # ---------------------------------------------------------------- #

    def _minimax(self, boss, player, grid, depth, is_max, alpha, beta):
        self.nodes_with_pruning += 1

        if depth == 0 or boss is None or player is None:
            return self._evaluate(boss, player, grid)

        if is_max:
            value = float('-inf')
            for action in self._get_boss_actions(boss, grid):
                new_boss, new_grid = self._apply_boss_action(boss, player, grid, action)
                value = max(value, self._minimax(new_boss, player, new_grid,
                                                 depth - 1, False, alpha, beta))
                alpha = max(alpha, value)
                if alpha >= beta:
                    break  # Beta cutoff
            return value
        else:
            value = float('inf')
            for action in self._get_player_actions(player, grid):
                new_player = self._apply_player_action(player, grid, action)
                value = min(value, self._minimax(boss, new_player, grid,
                                                 depth - 1, True, alpha, beta))
                beta = min(beta, value)
                if alpha >= beta:
                    break  # Alpha cutoff
            return value

    def _minimax_no_prune(self, boss, player, grid, depth, is_max):
        """Same as minimax but no pruning — for node counting comparison."""
        self.nodes_without_pruning += 1

        if depth == 0 or boss is None or player is None:
            return self._evaluate(boss, player, grid)

        if is_max:
            value = float('-inf')
            for action in self._get_boss_actions(boss, grid):
                new_boss, new_grid = self._apply_boss_action(boss, player, grid, action)
                value = max(value, self._minimax_no_prune(new_boss, player, new_grid,
                                                          depth - 1, False))
            return value
        else:
            value = float('inf')
            for action in self._get_player_actions(player, grid):
                new_player = self._apply_player_action(player, grid, action)
                value = min(value, self._minimax_no_prune(boss, new_player, grid,
                                                          depth - 1, True))
            return value

    # ---------------------------------------------------------------- #
    #  Heuristic                                                        #
    # ---------------------------------------------------------------- #

    def _evaluate(self, boss, player, grid):
        """
        Evaluation heuristic (from spec):
          +60  player within 3 tiles
          +50  player in line-of-sight
          +30  boss adjacent to steel
          +20  per player HP missing
          -40  per boss HP missing
          -20  player in forest tile
        """
        if boss is None:
            return float('-inf')
        if player is None:
            return float('inf')

        score = 0
        bx, by = boss['x'], boss['y']
        px, py = player['x'], player['y']

        dist = abs(bx - px) + abs(by - py)

        # Proximity bonus
        if dist <= 3:
            score += 60
        else:
            score += max(0, 30 - dist * 2)

        # Line of sight
        if self._has_los(bx, by, px, py, grid):
            score += 50

        # Boss adjacent to steel wall
        for dx, dy in [(-1,0),(1,0),(0,-1),(0,1)]:
            nx, ny = bx+dx, by+dy
            if 0 <= nx < GRID_SIZE and 0 <= ny < GRID_SIZE:
                if grid[ny][nx] == STEEL:
                    score += 30
                    break

        # Player weakened
        score += (3 - player.get('hp', 1)) * 20

        # Boss HP penalty
        score -= (10 - boss.get('hp', 10)) * 40

        # Player in forest
        if 0 <= px < GRID_SIZE and 0 <= py < GRID_SIZE:
            if grid[py][px] == FOREST:
                score -= 20

        return score

    def _has_los(self, bx, by, px, py, grid):
        """Check if boss has line-of-sight to player (same row or column, no walls)."""
        if bx == px:
            mn, mx = min(by, py), max(by, py)
            for y in range(mn+1, mx):
                if grid[y][bx] in (BRICK, STEEL, WATER):
                    return False
            return True
        if by == py:
            mn, mx = min(bx, px), max(bx, px)
            for x in range(mn+1, mx):
                if grid[by][x] in (BRICK, STEEL, WATER):
                    return False
            return True
        return False

    # ---------------------------------------------------------------- #
    #  Action generation & simulation                                   #
    # ---------------------------------------------------------------- #

    def _get_boss_actions(self, boss, grid):
        actions = ['SHOOT']
        bx, by  = boss['x'], boss['y']
        for d, (dx, dy) in DIR_VEC.items():
            nx, ny = bx+dx, by+dy
            if 0 <= nx < GRID_SIZE and 0 <= ny < GRID_SIZE:
                cell = grid[ny][nx]
                if cell not in (STEEL, WATER):
                    actions.append(('MOVE', d))
        return actions

    def _get_player_actions(self, player, grid):
        actions = ['SHOOT', 'STAY']
        px, py  = player['x'], player['y']
        for d, (dx, dy) in DIR_VEC.items():
            nx, ny = px+dx, py+dy
            if 0 <= nx < GRID_SIZE and 0 <= ny < GRID_SIZE:
                cell = grid[ny][nx]
                if cell not in (STEEL, WATER, BRICK):
                    actions.append(('MOVE', d))
        return actions

    def _apply_boss_action(self, boss, player, grid, action):
        """Simulate boss action. Returns (new_boss_state, new_grid)."""
        import copy
        new_boss  = dict(boss)
        new_grid  = grid  # shallow — we don't actually mutate for simulation

        if action == 'SHOOT':
            pass  # shooting doesn't change position
        elif isinstance(action, tuple) and action[0] == 'MOVE':
            d = action[1]
            dx, dy = DIR_VEC[d]
            nx, ny = new_boss['x'] + dx, new_boss['y'] + dy
            if (0 <= nx < GRID_SIZE and 0 <= ny < GRID_SIZE and
                    grid[ny][nx] not in (STEEL, WATER, BRICK)):
                new_boss['x'] = nx
                new_boss['y'] = ny
            new_boss['dir'] = d

        return new_boss, new_grid

    def _apply_player_action(self, player, grid, action):
        new_player = dict(player)
        if isinstance(action, tuple) and action[0] == 'MOVE':
            d = action[1]
            dx, dy = DIR_VEC[d]
            nx, ny = new_player['x'] + dx, new_player['y'] + dy
            if (0 <= nx < GRID_SIZE and 0 <= ny < GRID_SIZE and
                    grid[ny][nx] not in (STEEL, WATER, BRICK)):
                new_player['x'] = nx
                new_player['y'] = ny
        return new_player
