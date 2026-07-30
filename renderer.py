# renderer.py — Pygame rendering for Battle City

import pygame
import math
from constants import *


class Renderer:
    def __init__(self, screen):
        self.screen = screen
        self.tick = 0

        # Fonts
        try:
            self.font_sm = pygame.font.SysFont('monospace', 13, bold=True)
            self.font_md = pygame.font.SysFont('monospace', 18, bold=True)
            self.font_lg = pygame.font.SysFont('monospace', 28, bold=True)
            self.font_xl = pygame.font.SysFont('monospace', 48, bold=True)
        except:
            self.font_sm = pygame.font.Font(None, 14)
            self.font_md = pygame.font.Font(None, 20)
            self.font_lg = pygame.font.Font(None, 30)
            self.font_xl = pygame.font.Font(None, 50)

        # Pre-render tile surfaces
        self._build_tile_surfaces()

    def _build_tile_surfaces(self):
        T = TILE_SIZE
        self.tiles = {}

        # Empty
        s = pygame.Surface((T, T))
        s.fill((18, 18, 18))
        self.tiles[EMPTY] = s

        # Brick
        s = pygame.Surface((T, T))
        s.fill((160, 70, 30))
        for row in range(3):
            for col in range(3):
                px = col * (T//3)
                py = row * (T//3)
                pygame.draw.rect(s, (180, 90, 40), (px+1, py+1, T//3-2, T//3-2))
        self.tiles[BRICK] = s

        # Steel
        s = pygame.Surface((T, T))
        s.fill((100, 100, 120))
        pygame.draw.rect(s, (160, 160, 180), (2, 2, T-4, T-4))
        pygame.draw.line(s, (200, 200, 220), (2, 2), (T-4, 2), 2)
        pygame.draw.line(s, (200, 200, 220), (2, 2), (2, T-4), 2)
        pygame.draw.line(s, (60, 60, 80), (T-4, 2), (T-4, T-4), 2)
        pygame.draw.line(s, (60, 60, 80), (2, T-4), (T-4, T-4), 2)
        self.tiles[STEEL] = s

        # Water (2 frames for animation)
        self.water_frames = []
        for frame in range(2):
            s = pygame.Surface((T, T))
            s.fill(C_WATER1)
            for i in range(0, T, 6):
                offset = (i + frame * 3) % T
                pygame.draw.line(s, C_WATER2, (offset, 0), (offset + T//4, T), 2)
            self.water_frames.append(s)
        self.tiles[WATER] = self.water_frames[0]

        # Forest
        s = pygame.Surface((T, T), pygame.SRCALPHA)
        s.fill((0, 0, 0, 0))
        for cx, cy in [(T//4, T//4), (3*T//4, T//4), (T//2, T//2), (T//4, 3*T//4), (3*T//4, 3*T//4)]:
            pygame.draw.circle(s, (34, 120, 34), (cx, cy), T//4)
        self.tiles[FOREST] = s

        # Eagle
        s = pygame.Surface((T, T))
        s.fill((18, 18, 18))
        points = [(T//2, 2), (T-4, T-4), (T//2, T-8), (4, T-4)]
        pygame.draw.polygon(s, C_EAGLE, points)
        pygame.draw.polygon(s, C_ORANGE, points, 2)
        self.tiles[EAGLE] = s

        # Destroyed Eagle
        s = pygame.Surface((T, T))
        s.fill((18, 18, 18))
        points = [(T//2, 2), (T-4, T-4), (T//2, T-8), (4, T-4)]
        pygame.draw.polygon(s, (60, 60, 60), points)
        self.tiles['DEAD_EAGLE'] = s

    def update(self):
        self.tick += 1

    def draw_all(self, state):
        self.screen.fill(C_BLACK)
        self.draw_grid(state['grid'], state.get('eagle_alive', True))
        self.draw_bullets(state.get('bullets', []))
        self.draw_enemies(state.get('enemies', []))
        self.draw_player(state.get('player'))
        self.draw_ui(state)
        pygame.display.flip()

    def draw_grid(self, grid, eagle_alive=True):
        T = TILE_SIZE
        water_surf = self.water_frames[(self.tick // 15) % 2]

        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                px, py = x * T, y * T
                cell = grid[y][x]

                if cell == WATER:
                    self.screen.blit(water_surf, (px, py))
                elif cell == FOREST:
                    self.screen.blit(self.tiles[EMPTY], (px, py))
                    self.screen.blit(self.tiles[FOREST], (px, py))
                elif cell == EAGLE:
                    key = EAGLE if eagle_alive else 'DEAD_EAGLE'
                    self.screen.blit(self.tiles[key], (px, py))
                elif cell in self.tiles:
                    self.screen.blit(self.tiles[cell], (px, py))

        # Grid border
        pygame.draw.rect(self.screen, C_GRAY,
                         (0, 0, GRID_SIZE * T, GRID_SIZE * T), 2)

    def draw_player(self, player):
        if player is None or not player.alive:
            return
        T = TILE_SIZE
        px, py = player.x * T + T//2, player.y * T + T//2

        # Flash when invincible
        if player.invincible > 0 and (self.tick // 4) % 2 == 0:
            return

        color = C_YELLOW
        self._draw_tank(px, py, T, player.dir, color, border=(200, 200, 0))

    def draw_enemies(self, enemies):
        T = TILE_SIZE
        COLORS = {
            'basic': (C_GREEN, (40, 130, 40)),
            'fast':  (C_RED,   (180, 30, 30)),
            'armor': (C_ARMOR, (80, 130, 180)),
            'boss':  (C_BOSS,  (140, 0, 140)),
        }

        for e in enemies:
            if not e.alive:
                continue
            px, py = e.x * T + T//2, e.y * T + T//2
            col, border = COLORS.get(e.tank_type, (C_GREEN, (40, 130, 40)))

            # Armor tank: color changes by damage stage
            if e.tank_type == 'armor':
                stages = [(C_ARMOR, (80, 130, 180)),
                           (C_CYAN,  (0, 150, 150)),
                           (C_YELLOW,(200, 180, 0)),
                           (C_RED,   (180, 30, 30))]
                hits = getattr(e, 'hit_count', 0)
                col, border = stages[min(hits, 3)]

            self._draw_tank(px, py, T, e.dir, col, border=border)

            # HP pips for armor
            if e.tank_type == 'armor' and e.hp > 1:
                for i in range(e.hp):
                    pip_x = e.x * T + 2 + i * 5
                    pip_y = e.y * T + T - 5
                    pygame.draw.rect(self.screen, C_YELLOW, (pip_x, pip_y, 4, 4))

            # Boss HP bar
            if e.tank_type == 'boss':
                bar_x = e.x * T
                bar_y = e.y * T - 6
                bar_w = T
                ratio = e.hp / e.max_hp
                pygame.draw.rect(self.screen, C_RED,   (bar_x, bar_y, bar_w, 4))
                pygame.draw.rect(self.screen, C_GREEN, (bar_x, bar_y, int(bar_w * ratio), 4))

    def _draw_tank(self, cx, cy, T, direction, color, border=(200, 200, 200)):
        half = T // 2 - 2
        # Body
        pygame.draw.rect(self.screen, border,
                         (cx - half - 1, cy - half - 1, half*2+2, half*2+2))
        pygame.draw.rect(self.screen, color,
                         (cx - half, cy - half, half*2, half*2))

        # Turret barrel
        blen = T // 2
        dx, dy = DIR_VEC[direction]
        ex, ey = cx + dx * blen, cy + dy * blen
        pygame.draw.line(self.screen, border, (cx, cy), (ex, ey), 5)
        pygame.draw.line(self.screen, (240, 240, 240), (cx, cy), (ex, ey), 3)

        # Direction indicator dot
        pygame.draw.circle(self.screen, (255, 255, 255), (cx, cy), 3)

    def draw_bullets(self, bullets):
        T = TILE_SIZE
        for b in bullets:
            if not b.alive:
                continue
            bx = int(b.x * T + T // 2)
            by = int(b.y * T + T // 2)
            color = C_YELLOW if b.owner == 'player' else C_RED
            if b.owner == 'boss':
                color = C_BOSS
            pygame.draw.circle(self.screen, color, (bx, by), 4)
            pygame.draw.circle(self.screen, (255, 255, 255), (bx, by), 2)

    def draw_ui(self, state):
        T  = TILE_SIZE
        ux = GRID_SIZE * T + 10
        uy = 10
        panel_w = UI_WIDTH - 20

        # Panel background
        pygame.draw.rect(self.screen, (15, 15, 20),
                         (GRID_SIZE * T, 0, UI_WIDTH, SCREEN_H))
        pygame.draw.rect(self.screen, C_GRAY,
                         (GRID_SIZE * T, 0, UI_WIDTH, SCREEN_H), 2)

        def text(txt, x, y, font=None, color=C_WHITE):
            f = font or self.font_sm
            surf = f.render(str(txt), True, color)
            self.screen.blit(surf, (x, y))

        # Title
        text("BATTLE CITY", ux, uy, self.font_md, C_YELLOW)
        text("AL2002 AI Lab", ux, uy + 22, self.font_sm, C_GRAY)
        uy += 52

        pygame.draw.line(self.screen, C_GRAY, (ux - 5, uy), (ux + panel_w, uy))
        uy += 8

        player = state.get('player')
        if player:
            text(f"LIVES : {player.lives}", ux, uy, color=C_YELLOW)
            uy += 18
            text(f"LEVEL : {state.get('level', 1)}", ux, uy)
            uy += 18
            text(f"KILLS : {state.get('kills', 0)}", ux, uy)
            uy += 18
            remaining = state.get('enemy_pool', 20) - state.get('kills', 0) - len(state.get('enemies', []))
            text(f"QUEUE : {max(0, remaining)}", ux, uy)
            uy += 18

        uy += 8
        pygame.draw.line(self.screen, C_GRAY, (ux - 5, uy), (ux + panel_w, uy))
        uy += 8

        # Enemy count icons
        text("ENEMIES:", ux, uy, color=C_RED)
        uy += 18
        active = state.get('enemies', [])
        for i, e in enumerate(active):
            col = {'basic': C_GREEN, 'fast': C_RED,
                   'armor': C_ARMOR, 'boss': C_BOSS}.get(e.tank_type, C_WHITE)
            icon_x = ux + (i % 4) * 28
            icon_y = uy + (i // 4) * 20
            pygame.draw.rect(self.screen, col, (icon_x, icon_y, 14, 14))
            tname = {'basic': 'B', 'fast': 'F', 'armor': 'A', 'boss': '!'}
            text(tname.get(e.tank_type, '?'), icon_x + 3, icon_y + 1,
                 self.font_sm, (0, 0, 0))
        uy += 40

        pygame.draw.line(self.screen, C_GRAY, (ux - 5, uy), (ux + panel_w, uy))
        uy += 8

        # Controls
        text("CONTROLS", ux, uy, color=C_YELLOW)
        uy += 18
        controls = [
            "WASD / Arrows: Move",
            "SPACE / J: Shoot",
            "ESC: Pause",
        ]
        for c in controls:
            text(c, ux, uy, color=(180, 180, 180))
            uy += 16

        uy += 8
        pygame.draw.line(self.screen, C_GRAY, (ux - 5, uy), (ux + panel_w, uy))
        uy += 8

        # Level info
        level = state.get('level', 1)
        level_names = {1: "Brick Maze", 2: "Steel Fortress", 3: "Boss Battle"}
        text(f"MAP: {level_names.get(level, '?')}", ux, uy, color=C_CYAN)
        uy += 18

        # AI module info
        text("AI MODULES:", ux, uy, color=C_YELLOW)
        uy += 16
        text("A: CSP Map Gen", ux, uy, color=(180, 180, 180))
        uy += 14
        text("B: BFS/Greedy/A*", ux, uy, color=(180, 180, 180))
        uy += 14
        if level == 3:
            text("C: Minimax+AB", ux, uy, color=C_BOSS)
            uy += 14

        # Boss stats (if boss level)
        boss_list = [e for e in state.get('enemies', []) if e.tank_type == 'boss']
        if boss_list:
            boss = boss_list[0]
            uy += 8
            pygame.draw.line(self.screen, C_BOSS, (ux - 5, uy), (ux + panel_w, uy))
            uy += 8
            text("BOSS STATS", ux, uy, color=C_BOSS)
            uy += 16
            text(f"HP:    {boss.hp}/{boss.max_hp}", ux, uy)
            uy += 14
            text(f"Phase: {boss.phase}", ux, uy)
            uy += 14
            text(f"Depth: {boss.depth}", ux, uy)
            uy += 14
            text(f"Nodes(no prune):", ux, uy)
            uy += 14
            text(f"  {boss.last_nodes_without}", ux, uy, color=C_RED)
            uy += 14
            text(f"Nodes(AB prune):", ux, uy)
            uy += 14
            text(f"  {boss.last_nodes_with}", ux, uy, color=C_GREEN)
            uy += 14
            text(f"Speedup: {boss.speedup_ratio:.1f}x", ux, uy, color=C_YELLOW)
            uy += 14

        # Bottom status bar
        status = state.get('status_msg', '')
        if status:
            pygame.draw.rect(self.screen, (30, 30, 0),
                             (0, GRID_PIXEL + 2, GRID_PIXEL, 40))
            surf = self.font_md.render(status, True, C_YELLOW)
            self.screen.blit(surf, (GRID_PIXEL // 2 - surf.get_width() // 2,
                                    GRID_PIXEL + 10))

    def draw_overlay(self, title, subtitle='', color=C_YELLOW):
        """Full-screen overlay for win/lose/pause."""
        overlay = pygame.Surface((GRID_PIXEL, GRID_PIXEL), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        self.screen.blit(overlay, (0, 0))

        cy = GRID_PIXEL // 2 - 40
        surf = self.font_xl.render(title, True, color)
        self.screen.blit(surf, (GRID_PIXEL // 2 - surf.get_width() // 2, cy))

        if subtitle:
            surf2 = self.font_md.render(subtitle, True, C_WHITE)
            self.screen.blit(surf2, (GRID_PIXEL // 2 - surf2.get_width() // 2, cy + 60))

        pygame.display.flip()
