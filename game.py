# game.py — Main Game orchestrator

import pygame
import random
from constants import *
from renderer import Renderer
from tanks import PlayerTank, BasicTank, FastTank, ArmorTank, BossTank, Bullet
from modules.csp_map import CSPMapGenerator, generate_boss_arena


# ------------------------------------------------------------------ #
#  Level configuration                                                #
# ------------------------------------------------------------------ #

LEVEL_CONFIGS = {
    1: {
        'name':      'Brick Maze',
        'pool':      [('basic', 7), ('fast', 5)],  # 7 basic then 5 fast after 10 kills
        'fast_after': 10,
        'max_active': 3,
    },
    2: {
        'name':      'Steel Fortress',
        'pool':      [('fast', 4), ('armor', 3), ('power', 2)],
        'fast_after': 0,
        'max_active': 3,
    },
    3: {  # Boss Level
        'name':      'Tank Commander',
        'pool':      [('boss', 1)],
        'fast_after': 0,
        'max_active': 1,
    },
}


# ------------------------------------------------------------------ #
#  Game states                                                        #
# ------------------------------------------------------------------ #

STATE_MENU    = 'menu'
STATE_PLAYING = 'playing'
STATE_PAUSED  = 'paused'
STATE_WIN     = 'win'
STATE_LOSE    = 'lose'
STATE_LEVEL_CLEAR = 'level_clear'


class Game:
    def __init__(self, screen, clock):
        self.screen  = screen
        self.clock   = clock
        self.renderer = Renderer(screen)
        self.state   = STATE_MENU
        self.level   = 1
        self.kills   = 0
        self.total_kills = 0

        self.grid    = None
        self.player  = None
        self.enemies = []
        self.bullets = []
        self.enemy_pool = []    # list of tank type strings
        self.spawn_queue_idx = 0
        self.spawn_timer = 0
        self.eagle_alive = True
        self.status_msg  = ''
        self.state_timer = 0   # for overlay timers

    # ---------------------------------------------------------------- #
    #  Main loop                                                        #
    # ---------------------------------------------------------------- #

    def run(self):
        while True:
            self._handle_events()
            self._update()
            self._render()
            self.clock.tick(FPS)

    def _handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                import sys; sys.exit()
            if event.type == pygame.KEYDOWN:
                self._handle_key(event.key)

    def _handle_key(self, key):
        if key == pygame.K_ESCAPE:
            if self.state == STATE_PLAYING:
                self.state = STATE_PAUSED
            elif self.state == STATE_PAUSED:
                self.state = STATE_PLAYING

        elif key == pygame.K_RETURN or key == pygame.K_SPACE:
            if self.state in (STATE_MENU, STATE_WIN, STATE_LOSE):
                if self.state == STATE_LOSE:
                    self.level = 1
                    self.total_kills = 0
                self._start_level(self.level)
            elif self.state == STATE_LEVEL_CLEAR:
                self.level += 1
                if self.level > 3:
                    self.level = 1
                self._start_level(self.level)

    def _update(self):
        self.renderer.update()

        if self.state == STATE_PLAYING:
            self._game_tick()

        elif self.state in (STATE_WIN, STATE_LOSE, STATE_LEVEL_CLEAR):
            self.state_timer -= 1

    def _render(self):
        if self.state == STATE_MENU:
            self._draw_menu()
        elif self.state in (STATE_PLAYING, STATE_PAUSED):
            self.renderer.draw_all(self._build_state())
            if self.state == STATE_PAUSED:
                self.renderer.draw_overlay("PAUSED", "Press ESC to resume")
        elif self.state == STATE_LEVEL_CLEAR:
            self.renderer.draw_all(self._build_state())
            self.renderer.draw_overlay(
                "LEVEL CLEAR!", "Press ENTER for next level", C_GREEN)
        elif self.state == STATE_WIN:
            self.renderer.draw_all(self._build_state())
            self.renderer.draw_overlay("YOU WIN!", "Press ENTER to restart", C_YELLOW)
        elif self.state == STATE_LOSE:
            self.renderer.draw_all(self._build_state())
            self.renderer.draw_overlay("GAME OVER", "Press ENTER to restart", C_RED)

    # ---------------------------------------------------------------- #
    #  Level setup                                                      #
    # ---------------------------------------------------------------- #

    def _start_level(self, level):
        self.level = level
        self.kills = 0
        self.eagle_alive = True
        self.enemies = []
        self.bullets = []
        self.spawn_timer = FPS * 2
        self.state = STATE_PLAYING
        self.status_msg = ''

        # Generate map via CSP
        if level == 3:
            self.grid = generate_boss_arena()
        else:
            gen = CSPMapGenerator(level=level, seed=random.randint(0, 9999))
            self.grid = gen.generate()

        # Player
        self.player = PlayerTank(PLAYER_SPAWN_X, PLAYER_SPAWN_Y)

        # Build enemy pool
        cfg = LEVEL_CONFIGS.get(level, LEVEL_CONFIGS[1])
        pool = []
        for ttype, count in cfg['pool']:
            pool.extend([ttype] * count)
        self.enemy_pool = pool
        self.spawn_queue_idx = 0

        # For level 1: fill pool correctly
        # Basic first, then fast (handled in spawn logic)

    # ---------------------------------------------------------------- #
    #  Game tick                                                        #
    # ---------------------------------------------------------------- #

    def _game_tick(self):
        keys = pygame.key.get_pressed()

        # 1. Player input
        self.player.handle_input(keys, self.grid)
        self.player.try_shoot(keys)
        self.player.update()

        # 2. Enemy AI decisions
        for e in self.enemies:
            if e.alive:
                e.update(self.grid, self.player)

        # 3. Collect all bullets
        all_bullets = []
        if self.player.bullet and self.player.bullet.alive:
            all_bullets.append(self.player.bullet)
        for e in self.enemies:
            if e.bullet and e.bullet.alive:
                all_bullets.append(e.bullet)
        self.bullets = all_bullets

        # 4. Update bullets
        for b in list(self.bullets):
            result = b.update(self.grid)
            if result == 'eagle':
                self.eagle_alive = False
                self.grid[EAGLE_Y][EAGLE_X] = EAGLE  # keep tile for rendering
                self._lose()
                return

        # 5. Bullet-tank collision
        self._check_bullet_tank_collisions()

        # 6. Bullet-bullet collision
        self._check_bullet_bullet_collisions()

        # 7. Clear dead bullets from owners
        if self.player.bullet and not self.player.bullet.alive:
            self.player.bullet = None
        for e in self.enemies:
            if e.bullet and not e.bullet.alive:
                e.bullet = None

        # 8. Remove dead enemies
        dead = [e for e in self.enemies if not e.alive]
        self.kills += len(dead)
        self.total_kills += len(dead)
        self.enemies = [e for e in self.enemies if e.alive]

        # 9. Check win/lose
        if not self.player.alive:
            self._lose()
            return

        if self.kills >= len(self.enemy_pool) and not self.enemies:
            self._level_clear()
            return

        # 10. Spawn new enemies
        self._spawn_tick()

        # 11. Replan enemies whose path tile changed (map mutation)
        self._notify_map_change()

    def _check_bullet_tank_collisions(self):
        for b in self.bullets:
            if not b.alive:
                continue
            bx, by = b.tile

            # Bullet vs player
            if b.owner != 'player' and self.player.alive:
                if bx == self.player.x and by == self.player.y:
                    b.alive = False
                    self.player.take_hit()
                    continue

            # Bullet vs enemies
            for e in self.enemies:
                if not e.alive:
                    continue
                if b.owner == 'enemy' and e.tank_type != 'boss':
                    continue  # friendly fire skip for basic enemies
                if bx == e.x and by == e.y:
                    if b.owner in ('player', 'boss') or (b.owner == 'enemy' and e.tank_type == 'boss'):
                        b.alive = False
                        if hasattr(e, 'take_hit'):
                            e.take_hit()
                        else:
                            e.hp -= 1
                            if e.hp <= 0:
                                e.alive = False
                        break

    def _check_bullet_bullet_collisions(self):
        alive = [b for b in self.bullets if b.alive]
        for i in range(len(alive)):
            for j in range(i+1, len(alive)):
                b1, b2 = alive[i], alive[j]
                if b1.tile == b2.tile:
                    b1.alive = False
                    b2.alive = False

    def _spawn_tick(self):
        if self.spawn_queue_idx >= len(self.enemy_pool):
            return
        if len(self.enemies) >= LEVEL_CONFIGS.get(self.level, {}).get('max_active', 3):
            return

        self.spawn_timer -= 1
        if self.spawn_timer > 0:
            return
        self.spawn_timer = FPS * 2  # 2 second between spawns

        # For level 1: basic first 10 kills, then fast
        ttype = self.enemy_pool[self.spawn_queue_idx]
        if self.level == 1 and self.kills >= 10 and ttype == 'basic':
            ttype = 'fast'

        # Pick spawn point (rotation)
        sp_idx = self.spawn_queue_idx % len(ENEMY_SPAWNS)
        sx, sy = ENEMY_SPAWNS[sp_idx]

        # Fairness constraint: not within 10 tiles of player
        dist = abs(sx - self.player.x) + abs(sy - self.player.y)
        if dist < 10:
            sp_idx = (sp_idx + 1) % len(ENEMY_SPAWNS)
            sx, sy = ENEMY_SPAWNS[sp_idx]

        # Don't spawn on another tank
        occupied = any(e.x == sx and e.y == sy for e in self.enemies)
        if occupied:
            return

        tank = self._create_tank(ttype, sx, sy)
        if tank:
            self.enemies.append(tank)
            self.spawn_queue_idx += 1

    def _create_tank(self, ttype, x, y):
        if ttype == 'basic':
            return BasicTank(x, y)
        elif ttype == 'fast' or ttype == 'power':
            return FastTank(x, y)
        elif ttype == 'armor':
            return ArmorTank(x, y)
        elif ttype == 'boss':
            return BossTank(x, y)
        return BasicTank(x, y)

    def _notify_map_change(self):
        """After bullet destroys a brick, enemies with that tile in path replan."""
        # Simple: any enemy whose next path step is now destroyed brick will naturally
        # replan when _move_along_path sees the tile type changed.
        pass

    # ---------------------------------------------------------------- #
    #  State transitions                                                #
    # ---------------------------------------------------------------- #

    def _level_clear(self):
        if self.level == 3:
            self.state = STATE_WIN
        else:
            self.state = STATE_LEVEL_CLEAR
        self.state_timer = FPS * 3

    def _lose(self):
        self.eagle_alive = False
        self.state = STATE_LOSE
        self.state_timer = FPS * 3

    # ---------------------------------------------------------------- #
    #  Build state dict for renderer                                    #
    # ---------------------------------------------------------------- #

    def _build_state(self):
        return {
            'grid':        self.grid,
            'player':      self.player,
            'enemies':     self.enemies,
            'bullets':     self.bullets,
            'level':       self.level,
            'kills':       self.kills,
            'enemy_pool':  len(self.enemy_pool),
            'eagle_alive': self.eagle_alive,
            'status_msg':  self.status_msg,
        }

    # ---------------------------------------------------------------- #
    #  Menu                                                             #
    # ---------------------------------------------------------------- #

    def _draw_menu(self):
        self.screen.fill((10, 10, 15))
        cx = GRID_PIXEL // 2

        # Title
        title = self.renderer.font_xl.render("BATTLE CITY", True, C_YELLOW)
        self.screen.blit(title, (cx - title.get_width()//2, 80))

        sub = self.renderer.font_md.render("AL2002 Artificial Intelligence Lab", True, C_CYAN)
        self.screen.blit(sub, (cx - sub.get_width()//2, 145))

        # Tank type info
        info = [
            ("Basic Tank  →  Simple Reflex + BFS",         C_GREEN),
            ("Fast Tank   →  Goal-Based + Greedy BFS",     C_RED),
            ("Armor Tank  →  Model-Based + A* Search",     C_ARMOR),
            ("Boss Tank   →  Adversarial + Minimax+AB",    C_BOSS),
        ]
        y = 210
        for txt, col in info:
            s = self.renderer.font_sm.render(txt, True, col)
            self.screen.blit(s, (cx - s.get_width()//2, y))
            y += 22

        # Levels
        y += 20
        lvl_info = [
            "Level 1 — Brick Maze    (BFS tanks)",
            "Level 2 — Steel Fortress (A* tanks)",
            "Level 3 — Tank Commander (Boss/Minimax)",
        ]
        for txt in lvl_info:
            s = self.renderer.font_sm.render(txt, True, C_WHITE)
            self.screen.blit(s, (cx - s.get_width()//2, y))
            y += 20

        # Controls reminder
        y += 20
        ctrl = self.renderer.font_sm.render("WASD/Arrows: Move   SPACE: Shoot   ESC: Pause", True, (150, 150, 150))
        self.screen.blit(ctrl, (cx - ctrl.get_width()//2, y))

        # Press enter
        tick = pygame.time.get_ticks() // 500
        if tick % 2 == 0:
            start = self.renderer.font_lg.render("Press ENTER to Start", True, C_YELLOW)
            self.screen.blit(start, (cx - start.get_width()//2, y + 50))

        pygame.display.flip()
