# tanks.py — All tank types: Player, Basic, Fast, Armor, Boss

import random
from constants import *
from modules.search import bfs, greedy_next_step, astar, bfs_to_nearest
from modules.minimax import MinimaxAgent


# ------------------------------------------------------------------ #
#  Bullet                                                             #
# ------------------------------------------------------------------ #

class Bullet:
    def __init__(self, x, y, direction, owner):
        self.x = float(x)
        self.y = float(y)
        self.dir = direction
        self.owner = owner   # 'player' or 'enemy' or 'boss'
        self.alive = True

    def update(self, grid):
        dx, dy = DIR_VEC[self.dir]
        # Move BULLET_SPEED tiles per tick (in sub-steps to detect collisions)
        for _ in range(BULLET_SPEED):
            if not self.alive:
                break
            nx = int(self.x) + dx
            ny = int(self.y) + dy
            if not (0 <= nx < GRID_SIZE and 0 <= ny < GRID_SIZE):
                self.alive = False
                break
            cell = grid[ny][nx]
            if cell == BRICK:
                grid[ny][nx] = EMPTY
                self.alive = False
                break
            elif cell == STEEL:
                self.alive = False
                break
            elif cell == WATER:
                self.alive = False
                break
            elif cell == EAGLE:
                self.alive = False
                return 'eagle'
            else:
                self.x = nx
                self.y = ny
        return None

    @property
    def tile(self):
        return int(self.x), int(self.y)


# ------------------------------------------------------------------ #
#  Player Tank                                                        #
# ------------------------------------------------------------------ #

class PlayerTank:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.dir = UP
        self.hp = 1
        self.lives = PLAYER_LIVES
        self.alive = True
        self.bullet = None
        self.shoot_cooldown = 0
        self.invincible = 0  # ticks of spawn invincibility
        self.SHOOT_CD = 12

    def handle_input(self, keys, grid):
        moved = False
        if keys[__import__('pygame').K_UP] or keys[__import__('pygame').K_w]:
            self.dir = UP;    moved = self._try_move(0, -1, grid)
        elif keys[__import__('pygame').K_DOWN] or keys[__import__('pygame').K_s]:
            self.dir = DOWN;  moved = self._try_move(0,  1, grid)
        elif keys[__import__('pygame').K_LEFT] or keys[__import__('pygame').K_a]:
            self.dir = LEFT;  moved = self._try_move(-1, 0, grid)
        elif keys[__import__('pygame').K_RIGHT] or keys[__import__('pygame').K_d]:
            self.dir = RIGHT; moved = self._try_move(1,  0, grid)

    def try_shoot(self, keys):
        import pygame
        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= 1
        if (keys[pygame.K_SPACE] or keys[pygame.K_j]) and self.bullet is None and self.shoot_cooldown == 0:
            bx, by = self.x + DIR_VEC[self.dir][0], self.y + DIR_VEC[self.dir][1]
            self.bullet = Bullet(bx, by, self.dir, 'player')
            self.shoot_cooldown = self.SHOOT_CD

    def _try_move(self, dx, dy, grid):
        nx, ny = self.x + dx, self.y + dy
        if 0 <= nx < GRID_SIZE and 0 <= ny < GRID_SIZE:
            cell = grid[ny][nx]
            if cell in (EMPTY, FOREST):
                self.x, self.y = nx, ny
                return True
        return False

    def take_hit(self):
        if self.invincible > 0:
            return False
        self.lives -= 1
        self.invincible = FPS * 2   # 2 second grace period
        if self.lives <= 0:
            self.alive = False
        else:
            self.x = PLAYER_SPAWN_X
            self.y = PLAYER_SPAWN_Y
        return True

    def update(self):
        if self.invincible > 0:
            self.invincible -= 1

    @property
    def tile(self):
        return self.x, self.y

    def as_dict(self):
        return {'x': self.x, 'y': self.y, 'hp': self.lives, 'dir': self.dir}


# ------------------------------------------------------------------ #
#  Base Enemy Tank                                                    #
# ------------------------------------------------------------------ #

class EnemyTank:
    SHOOT_CD = 30  # override per type

    def __init__(self, x, y, tank_type='basic'):
        self.x = x
        self.y = y
        self.dir = DOWN
        self.hp = 1
        self.alive = True
        self.bullet = None
        self.shoot_cd = self.SHOOT_CD
        self.tank_type = tank_type
        self.path = []
        self.replan_timer = 0
        self.REPLAN_TICKS = FPS * 5   # replan every 5 seconds

    def update(self, grid, player):
        raise NotImplementedError

    def _shoot_if_los(self, grid, player):
        """Shoot if player is in same row/col with no wall between."""
        if self.bullet is not None:
            return
        if self.shoot_cd > 0:
            self.shoot_cd -= 1
            return
        px, py = player.x, player.y
        shoot = False
        shoot_dir = self.dir

        if self.x == px:
            mn, mx = min(self.y, py), max(self.y, py)
            blocked = any(grid[y][self.x] in (STEEL, WATER, BRICK)
                         for y in range(mn+1, mx))
            if not blocked:
                shoot = True
                shoot_dir = DOWN if py > self.y else UP
        elif self.y == py:
            mn, mx = min(self.x, px), max(self.x, px)
            blocked = any(grid[self.y][x] in (STEEL, WATER, BRICK)
                         for x in range(mn+1, mx))
            if not blocked:
                shoot = True
                shoot_dir = RIGHT if px > self.x else LEFT

        if shoot:
            self.dir = shoot_dir
            bx = self.x + DIR_VEC[self.dir][0]
            by = self.y + DIR_VEC[self.dir][1]
            self.bullet = Bullet(bx, by, self.dir, 'enemy')
            self.shoot_cd = self.SHOOT_CD

    def _move_along_path(self, grid):
        """Follow cached path one step. Shoot brick if blocking."""
        if not self.path:
            return

        tx, ty = self.path[0]
        dx, dy = tx - self.x, ty - self.y
        if   dx >  0: self.dir = RIGHT
        elif dx < 0:  self.dir = LEFT
        elif dy > 0:  self.dir = DOWN
        else:         self.dir = UP

        cell = grid[ty][tx]
        if cell == BRICK:
            # Shoot wall to clear it
            if self.bullet is None and self.shoot_cd <= 0:
                bx = self.x + DIR_VEC[self.dir][0]
                by = self.y + DIR_VEC[self.dir][1]
                self.bullet = Bullet(bx, by, self.dir, 'enemy')
                self.shoot_cd = self.SHOOT_CD
            return  # Don't move yet
        elif cell in (STEEL, WATER):
            self.path = []
            return
        elif cell in (EMPTY, FOREST, EAGLE):
            self.x, self.y = tx, ty
            self.path.pop(0)

    def _random_free_direction(self, grid):
        """Pick a random unblocked direction."""
        dirs = list(DIR_VEC.keys())
        random.shuffle(dirs)
        for d in dirs:
            dx, dy = DIR_VEC[d]
            nx, ny = self.x + dx, self.y + dy
            if 0 <= nx < GRID_SIZE and 0 <= ny < GRID_SIZE:
                if grid[ny][nx] not in (STEEL, WATER):
                    self.dir = d
                    return
        
    @property
    def tile(self):
        return self.x, self.y

    def as_dict(self):
        return {'x': self.x, 'y': self.y, 'hp': self.hp, 'dir': self.dir}


# ------------------------------------------------------------------ #
#  TANK TYPE 1 — Basic Tank (Simple Reflex + BFS)                    #
# ------------------------------------------------------------------ #

class BasicTank(EnemyTank):
    """
    Agent Model: Simple Reflex Agent
    Search:      BFS to Eagle
    """
    SHOOT_CD = FPS * 3  # shoot every 3 seconds

    def __init__(self, x, y):
        super().__init__(x, y, 'basic')
        self.hp = 1
        self.move_counter = 0
        self.MOVE_RATE = 4   # 1 tile per 4 ticks

    def update(self, grid, player):
        self.move_counter += 1

        # Replan BFS periodically
        self.replan_timer += 1
        if self.replan_timer >= self.REPLAN_TICKS or not self.path:
            self.path = bfs(grid, (self.x, self.y), (EAGLE_X, EAGLE_Y))
            self.replan_timer = 0

        # Simple Reflex: shoot player if in LOS
        self._shoot_if_los(grid, player)

        if self.move_counter >= self.MOVE_RATE:
            self.move_counter = 0
            if self.path:
                self._move_along_path(grid)
            else:
                # Reflex: try a random direction
                self._random_free_direction(grid)
                dx, dy = DIR_VEC[self.dir]
                nx, ny = self.x + dx, self.y + dy
                if 0 <= nx < GRID_SIZE and 0 <= ny < GRID_SIZE:
                    if grid[ny][nx] in (EMPTY, FOREST):
                        self.x, self.y = nx, ny


# ------------------------------------------------------------------ #
#  TANK TYPE 2 — Fast Tank (Goal-Based + Greedy Best-First)          #
# ------------------------------------------------------------------ #

class FastTank(EnemyTank):
    """
    Agent Model: Goal-Based Agent (goal = destroy Eagle)
    Search:      Greedy Best-First
    """
    SHOOT_CD = FPS  # shoot more often

    def __init__(self, x, y):
        super().__init__(x, y, 'fast')
        self.hp = 1
        self.move_counter = 0
        self.MOVE_RATE = 2   # 1 tile per 2 ticks (fast)

    def update(self, grid, player):
        self.move_counter += 1

        if self.move_counter >= self.MOVE_RATE:
            self.move_counter = 0

            # Greedy: pick neighbor minimising Manhattan dist to Eagle
            next_tile = greedy_next_step(grid, (self.x, self.y), (EAGLE_X, EAGLE_Y))

            if next_tile:
                tx, ty = next_tile
                dx, dy = tx - self.x, ty - self.y
                if   dx >  0: self.dir = RIGHT
                elif dx < 0:  self.dir = LEFT
                elif dy > 0:  self.dir = DOWN
                else:         self.dir = UP

                cell = grid[ty][tx]
                if cell == BRICK:
                    # Rule: shoot and push through (don't detour)
                    if self.bullet is None and self.shoot_cd <= 0:
                        bx = self.x + DIR_VEC[self.dir][0]
                        by = self.y + DIR_VEC[self.dir][1]
                        self.bullet = Bullet(bx, by, self.dir, 'enemy')
                        self.shoot_cd = self.SHOOT_CD
                elif cell in (EMPTY, FOREST, EAGLE):
                    self.x, self.y = tx, ty

        if self.shoot_cd > 0:
            self.shoot_cd -= 1


# ------------------------------------------------------------------ #
#  TANK TYPE 3 — Armor Tank (Model-Based Reflex + A*)                #
# ------------------------------------------------------------------ #

class ArmorTank(EnemyTank):
    """
    Agent Model: Model-Based Reflex Agent (internal state = hitCount)
    Search:      A* with cost-aware terrain
    """
    SHOOT_CD = FPS * 2

    def __init__(self, x, y):
        super().__init__(x, y, 'armor')
        self.hp = 4
        self.hit_count = 0
        self.state = 'attack'   # 'attack' | 'retreat' | 'cover'
        self.cover_timer = 0
        self.move_counter = 0
        self.MOVE_RATE = 3   # medium speed

    def take_hit(self):
        self.hp -= 1
        self.hit_count += 1
        if self.hp <= 0:
            self.alive = False
            return
        # Model-Based Rule: on 3rd hit → retreat
        if self.hit_count >= 3 and self.state == 'attack':
            self.state = 'retreat'
            self.path = bfs_to_nearest(
                self._last_grid, (self.x, self.y), {STEEL}
            ) if hasattr(self, '_last_grid') else []

    def update(self, grid, player):
        self._last_grid = grid
        self.move_counter += 1

        # State machine
        if self.state == 'attack':
            self._attack_update(grid, player)
        elif self.state == 'retreat':
            self._retreat_update(grid)
        elif self.state == 'cover':
            self._cover_update(grid)

    def _attack_update(self, grid, player):
        # Replan A* periodically
        self.replan_timer += 1
        if self.replan_timer >= self.REPLAN_TICKS or not self.path:
            self.path = astar(grid, (self.x, self.y), (EAGLE_X, EAGLE_Y))
            self.replan_timer = 0

        self._shoot_if_los(grid, player)

        if self.move_counter >= self.MOVE_RATE:
            self.move_counter = 0
            if self.path:
                self._move_along_path(grid)
            else:
                self._random_free_direction(grid)

    def _retreat_update(self, grid):
        # Find steel cover via BFS
        if not self.path:
            self.path = bfs_to_nearest(grid, (self.x, self.y), {STEEL})
        if self.move_counter >= self.MOVE_RATE:
            self.move_counter = 0
            if self.path:
                self._move_along_path(grid)
                if not self.path:
                    self.state = 'cover'
                    self.cover_timer = FPS * 2
            else:
                self.state = 'cover'
                self.cover_timer = FPS * 2

    def _cover_update(self, grid):
        self.cover_timer -= 1
        if self.cover_timer <= 0:
            # Resume attack with fresh A*
            self.path = astar(grid, (self.x, self.y), (EAGLE_X, EAGLE_Y))
            self.state = 'attack'
            self.replan_timer = 0


# ------------------------------------------------------------------ #
#  Boss Tank (Adversarial + Minimax + Alpha-Beta)                    #
# ------------------------------------------------------------------ #

class BossTank(EnemyTank):
    """
    Agent Model: Adversarial (Minimax)
    Phase system: changes depth and behaviour at HP thresholds.
    """
    SHOOT_CD = FPS // 2

    def __init__(self, x, y):
        super().__init__(x, y, 'boss')
        self.hp = 10
        self.max_hp = 10
        self.minimax = MinimaxAgent()
        self.move_counter = 0
        self.last_nodes_without = 0
        self.last_nodes_with    = 0
        self.speedup_ratio      = 1.0

    @property
    def phase(self):
        if self.hp >= 7: return 1
        if self.hp >= 3: return 2
        return 3

    @property
    def depth(self):
        return {1: 2, 2: 3, 3: 4}[self.phase]

    @property
    def MOVE_RATE(self):
        return {1: 4, 2: 3, 3: 2}[self.phase]

    def take_hit(self):
        self.hp -= 1
        if self.hp <= 0:
            self.alive = False

    def update(self, grid, player):
        if not self.alive or not player.alive:
            return

        self.move_counter += 1
        if self.move_counter < self.MOVE_RATE:
            return
        self.move_counter = 0

        if self.shoot_cd > 0:
            self.shoot_cd -= 1

        boss_dict   = self.as_dict()
        boss_dict['hp'] = self.hp
        player_dict = player.as_dict()
        player_dict['hp'] = player.lives

        action = self.minimax.choose_action(boss_dict, player_dict, grid, self.depth)

        # Record stats
        self.last_nodes_without = self.minimax.nodes_without_pruning
        self.last_nodes_with    = self.minimax.nodes_with_pruning
        if self.last_nodes_with > 0:
            self.speedup_ratio = self.last_nodes_without / self.last_nodes_with

        if action is None:
            return

        if action == 'SHOOT':
            if self.bullet is None and self.shoot_cd <= 0:
                bx = self.x + DIR_VEC[self.dir][0]
                by = self.y + DIR_VEC[self.dir][1]
                self.bullet = Bullet(bx, by, self.dir, 'boss')
                self.shoot_cd = self.SHOOT_CD
        elif isinstance(action, tuple) and action[0] == 'MOVE':
            d = action[1]
            dx, dy = DIR_VEC[d]
            nx, ny = self.x + dx, self.y + dy
            if 0 <= nx < GRID_SIZE and 0 <= ny < GRID_SIZE:
                cell = grid[ny][nx]
                if cell in (EMPTY, FOREST):
                    self.dir = d
                    self.x, self.y = nx, ny
                elif cell == BRICK and self.bullet is None and self.shoot_cd <= 0:
                    self.dir = d
                    bx = self.x + DIR_VEC[self.dir][0]
                    by = self.y + DIR_VEC[self.dir][1]
                    self.bullet = Bullet(bx, by, self.dir, 'boss')
                    self.shoot_cd = self.SHOOT_CD
