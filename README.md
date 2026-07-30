<div align="center">

# 🎮 Battle City

### A Tank 1990–style arcade game powered entirely by classic AI search algorithms

**AL2002 — Artificial Intelligence Lab**
*Spring 2026 · Sections 6A & 6B*

</div>

---

## 📌 About

**Battle City** is a full recreation of the classic *Tank 1990* arcade game — but every enemy tank, map layout, and boss fight is driven by a real AI technique from the course: **CSP, BFS, Greedy Best-First, A\*, and Minimax with Alpha-Beta Pruning.**

It's not just a game — it's a live demo of how different search strategies behave, compete, and scale under pressure.

---



<div align="center">

<img width="424" alt="Battle City — Main Menu" src="https://github.com/user-attachments/assets/39d41272-af46-4fc7-acb7-cb8259f65b89" />

<img width="432" alt="Battle City — Level 1: Brick Maze" src="https://github.com/user-attachments/assets/a64c7a45-2dd8-4f3d-99db-cb3ed3d7404d" />

<img width="431" alt="Battle City — Gameplay in Action" src="https://github.com/user-attachments/assets/1ddc0009-14ba-4c29-aee8-5787364c1a26" />

</div>

---

## 🕹️ Controls

| Key | Action |
|---|---|
| `W A S D` / Arrow Keys | Move tank |
| `SPACE` / `J` | Shoot |
| `ESC` | Pause / Resume |
| `ENTER` | Start / Next Level |

---

## 🗺️ Levels

| Level | Name | Enemies | AI Modules |
|:---:|---|---|---|
| 1 | 🧱 Brick Maze | Basic ×7, Fast ×5 | CSP + BFS + Greedy |
| 2 | 🛡️ Steel Fortress | Fast ×4, Armor ×3, Power ×2 | CSP + Greedy + A* |
| 3 | 👑 Tank Commander | Boss ×1 | CSP + Minimax + Alpha-Beta |

---

## 🧠 AI Modules

### 🔲 Module A — CSP Map Generator `modules/csp_map.py`
Generates a guaranteed-playable map using **Constraint Satisfaction**:
- 676 tile variables, each with domain `{Empty, Brick, Steel, Water, Forest, Eagle}`
- Eagle base must be shielded by a full ring of Brick/Steel
- A valid BFS path must exist from every spawn point to the Eagle
- Spawns kept ≥10 tiles from the player's starting position
- Wall density capped at 40%, with water never fully blocking the only path

### 🔍 Module B — Search Algorithms `modules/search.py`

| Algorithm | Used By | Behavior |
|---|---|---|
| **BFS** | Basic Tank | Shortest-hop path to the Eagle, cost-blind, replans every 5s |
| **Greedy Best-First** | Fast Tank | Chases lowest Manhattan distance one step at a time — can fall into local minima |
| **A\*** | Armor Tank | Cost-aware pathing (`Empty=1, Brick=3, Steel=∞`) — smart enough to shoot through walls when cheaper than detouring |

### ⚔️ Module C — Adversarial Search `modules/minimax.py`
**Minimax + Alpha-Beta Pruning** drives the Boss Tank:
- MAX node = Boss, MIN node = simulated player
- Search depth scales with boss phase (2 → 3 → 4)
- Live UI panel shows nodes evaluated *with* vs *without* pruning

**Boss Heuristic**

| Factor | Score |
|---|---:|
| Player within 3 tiles | +60 |
| Player in line-of-sight | +50 |
| Boss adjacent to steel | +30 |
| Player HP missing (per HP) | +20 |
| Boss HP missing (per HP) | −40 |
| Player in forest tile | −20 |

**Boss Phases**

| Phase | HP | Behavior | Search Depth |
|:---:|:---:|---|:---:|
| 1 | 10–7 | Aggressive push | 2 |
| 2 | 6–3 | Balanced attack + cover | 3 |
| 3 | 2–1 | Desperate rush | 4 |

---

## 🚗 Tank Roster

| Tank | HP | Speed | Agent Model | Search |
|---|:---:|---|---|---|
| 🟩 Basic | 1 | Slow | Simple Reflex | BFS |
| 🟥 Fast | 1 | Fast | Goal-Based | Greedy Best-First |
| 🟦 Armor | 4 | Medium | Model-Based Reflex | A* |
| 🟪 Boss | 10 | Phase-dependent | Adversarial | Minimax + Alpha-Beta |

---

## 🚀 Getting Started

### Requirements
- Python 3.8 – 3.12 *(pygame doesn't yet support 3.14 — use 3.12 if you have multiple versions installed)*
- pygame 2.x

### Install & Run
```bash
pip install -r requirements.txt
python main.py
```

---

## 📁 Project Structure

```
battle_city/
├── main.py           # Entry point
├── game.py           # Game loop, level management, collision
├── tanks.py           # All tank classes + Bullet
├── renderer.py        # Pygame drawing
├── constants.py        # All constants
├── requirements.txt
└── modules/
    ├── csp_map.py     # Module A — CSP Map Generator
    ├── search.py      # Module B — BFS, Greedy, A*
    └── minimax.py      # Module C — Minimax + Alpha-Beta
```

---

## 📊 Implementation Notes

**BFS vs A\*:** Place a 1-tile brick wall across the direct path with a 6+ tile detour — BFS blindly detours around it (cost-blind), while A* shoots straight through since the cost (3) beats the detour (6+).

**Alpha-Beta Speedup (Boss, depth 4, branching ≈5):**
- Without pruning: ~625 nodes evaluated
- With Alpha-Beta: ~25 nodes evaluated
- **≈25× speedup**

---

<div align="center">

## 👥 Team

**Muhammad Ahsan** · **Daniyal Shafique**
*Supervised by Dr. Rabia Maqsood*

*AL2002 — Artificial Intelligence Lab, Spring 2026*

</div>
