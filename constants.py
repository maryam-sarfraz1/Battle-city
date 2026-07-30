# constants.py — Game-wide constants

GRID_SIZE = 26
TILE_SIZE = 24
GRID_PIXEL = GRID_SIZE * TILE_SIZE  # 624
UI_WIDTH = 260
SCREEN_W = GRID_PIXEL + UI_WIDTH    # 884 → padded to 900
SCREEN_H = GRID_PIXEL + 76         # 700

FPS = 30

# Terrain types
EMPTY  = 0
BRICK  = 1
STEEL  = 2
WATER  = 3
FOREST = 4
EAGLE  = 5

# Directions
UP    = 0
RIGHT = 1
DOWN  = 2
LEFT  = 3

DIR_VEC = {
    UP:    (0, -1),
    DOWN:  (0,  1),
    LEFT:  (-1, 0),
    RIGHT: (1,  0),
}

# Colors
C_BLACK      = (0,   0,   0)
C_WHITE      = (255, 255, 255)
C_GRAY       = (80,  80,  80)
C_DARK       = (20,  20,  20)
C_YELLOW     = (255, 220, 0)
C_GREEN      = (60,  180, 60)
C_RED        = (220, 50,  50)
C_ORANGE     = (255, 140, 0)
C_BLUE       = (50,  120, 220)
C_CYAN       = (0,   200, 200)
C_BROWN      = (139, 90,  43)
C_STEEL      = (160, 160, 180)
C_WATER1     = (30,  80,  200)
C_WATER2     = (60,  130, 240)
C_FOREST     = (34,  100, 34)
C_EAGLE      = (255, 180, 0)
C_BOSS       = (180, 0,   180)
C_ARMOR      = (100, 160, 220)

# Eagle position (tile coords)
EAGLE_X = 12
EAGLE_Y = 24

# Player spawn
PLAYER_SPAWN_X = 4
PLAYER_SPAWN_Y = 24

# Enemy spawn points
ENEMY_SPAWNS = [(0, 0), (12, 0), (24, 0)]

# A* costs
ASTAR_COST = {
    EMPTY:  1,
    BRICK:  3,
    STEEL:  float('inf'),
    WATER:  float('inf'),
    FOREST: 1,
    EAGLE:  1,
}

# Bullet speed (tiles per tick)
BULLET_SPEED = 2

# Max simultaneous enemies on screen
MAX_ACTIVE_ENEMIES = 3

# Total enemies per level
TOTAL_ENEMIES = 20

# Player starting lives
PLAYER_LIVES = 10
