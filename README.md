# Battle City — AL2002 Artificial Intelligence Lab
## Spring 2026 | Sections 6A & 6B

---

## Setup & Run

### Requirements
- Python 3.8+
- pygame 2.x

### Install dependencies
```bash
pip install pygame
```

### Run the game
```bash
python main.py
```

---

## Controls

| Key | Action |
|-----|--------|
| WASD / Arrow Keys | Move tank |
| SPACE / J | Shoot |
| ESC | Pause / Resume |
| ENTER | Start / Next Level |

---

## Game Structure

### Levels
| Level | Name | Enemy Types | AI Modules |
|-------|------|-------------|------------|
| 1 | Brick Maze | Basic (7) + Fast (5) | CSP + BFS + Greedy |
| 2 | Steel Fortress | Fast (4) + Armor (3) + Power (2) | CSP + Greedy + A* |
| 3 | Tank Commander | Boss (1) | CSP + Minimax + Alpha-Beta |

---

## AI Modules

### Module A — CSP Map Generator (`modules/csp_map.py`)
Generates a valid playable map using constraint satisfaction:
- **Variables**: Each of the 676 tiles X_{i,j}
- **Domain**: {Empty, Brick, Steel, Water, Forest, Eagle}
- **Constraint 1**: Eagle surrounded by ≥1 ring of Brick/Steel
- **Constraint 2**: BFS path from every spawn to Eagle must exist
- **Constraint 3**: No spawn within 10 tiles of player start
- **Constraint 4**: ≤40% wall tiles
- **Constraint 5**: Water must not block only path to Eagle

### Module B — Search Algorithms (`modules/search.py`)

#### BFS — Basic Tank
- Finds shortest-hop path to Eagle
- Re-plans every 5 seconds and on map change
- Treats all passable tiles as equal cost = 1

#### Greedy Best-First — Fast Tank
- Picks neighbor with lowest Manhattan distance to Eagle
- Single-step decision each tick (no full path computed)
- Can get stuck in local minima (intentional — shows Greedy limits)

#### A* — Armor Tank
- Cost-aware navigation: Empty=1, Brick=3, Steel=∞, Water=∞
- Discovers it's cheaper to shoot through thin walls than detour
- Re-plans on spawn, after retreat, and on map change

### Module C — Adversarial Search (`modules/minimax.py`)

#### Minimax + Alpha-Beta Pruning — Boss Tank
- MAX node: Boss (maximises heuristic)
- MIN node: Simulated player (minimises heuristic)
- Depth varies by phase: Phase 1=2, Phase 2=3, Phase 3=4
- Alpha-Beta prunes branches where alpha ≥ beta
- UI shows live node counts: without pruning vs with pruning

#### Boss Heuristic
| Factor | Score |
|--------|-------|
| Player within 3 tiles | +60 |
| Player in line-of-sight | +50 |
| Boss adjacent to steel | +30 |
| Player HP missing (per HP) | +20 |
| Boss HP missing (per HP) | -40 |
| Player in forest tile | -20 |

#### Boss Phase System
| Phase | HP | Behaviour | Depth |
|-------|----|-----------|-------|
| 1 | 10-7 | Aggressive push | 2 |
| 2 | 6-3 | Balanced attack + cover | 3 |
| 3 | 2-1 | Desperate rush | 4 |

---

## Tank Types

| Tank | HP | Speed | Agent Model | Search |
|------|----|-------|-------------|--------|
| Basic | 1 | Slow (1/4 ticks) | Simple Reflex | BFS |
| Fast | 1 | Fast (1/2 ticks) | Goal-Based | Greedy BFS |
| Armor | 4 | Medium (1/3 ticks) | Model-Based Reflex | A* |
| Boss | 10 | Variable by phase | Adversarial | Minimax+AB |

---

## Project Structure

```
battle_city/
├── main.py           # Entry point
├── game.py           # Game loop, level management, collision
├── tanks.py          # All tank classes + Bullet
├── renderer.py       # Pygame drawing
├── constants.py      # All constants
├── requirements.txt
├── README.md
└── modules/
    ├── __init__.py
    ├── csp_map.py    # Module A: CSP Map Generator
    ├── search.py     # Module B: BFS, Greedy, A*
    └── minimax.py    # Module C: Minimax + Alpha-Beta
```

---

## Implementation Notes for Report

### Algorithm Analysis

**BFS vs A* Comparison**:  
Place a 1-tile-wide brick wall across the direct path with a 6+ tile detour:
- BFS takes the detour (cost-blind, shortest hops)
- A* shoots through the wall (cost 3 < cost 6+)
- Greedy may get confused by local minima

**Alpha-Beta Speedup**:  
Check the Boss level UI panel — it shows live:
- Nodes evaluated without pruning
- Nodes evaluated with Alpha-Beta
- Speedup ratio (theoretically O(b^d) → O(b^(d/2)))

At depth 4, branching factor ~5:  
- Without pruning: ~625 nodes
- With Alpha-Beta: ~25 nodes
- Speedup: ~25x

---

*Prepared for AL2002 AI Lab — Spring 2026*  
*Muhammad Ahsan | Daniyal Shafique | Dr. Rabia Maqsood*
