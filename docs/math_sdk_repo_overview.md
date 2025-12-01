# Math SDK Repository Overview

This document captures how the Stake Engine Math SDK repository is organized, how the core toolchain fits together, and the specific layout/behaviour of the `0_0_scatter` game that we're iterating on. It’s meant to be the “one-stop” refresher whenever we jump back into this repo.

---

## 1. Top-Level Architecture

| Area | Purpose | Key Notes |
| --- | --- | --- |
| `docs/` | MkDocs-powered documentation for math, frontend, and RGS integration. | Published at https://stakeengine.github.io/math-sdk/. Useful subfolders: `math_docs/`, `rgs_docs/`, `simple_example/`. |
| `games/` | Each math package lives here. Directory per game (e.g. `0_0_scatter`) with config, state overrides, reels, docs, and generated library assets. | Most files follow a common template: `game_config.py`, `game_executables.py`, `game_override.py`, `gamestate.py`, `game_optimization.py`, `run.py`. |
| `src/` | Shared engine modules (config, state machine, executables, calculations, events, write-data). | Python package installed via `setup.py` / `requirements.txt`. All games import from here. |
| `optimization_program/` | Rust crate (“PigFarm”) that tunes lookup-table weights to target RTP/volatility. Invoked via `optimization_program/run_script.py`. | Reads `games/<game>/library/math_config.json` generated during `run.py`. |
| `utils/` | Housekeeping scripts: analytics, formatting books, LUT merging, RGS verification, etc. | `utils/rgs_verification.py` is called after every run when `run_format_checks` is `True`. |
| `uploads/` | Helpers for pushing artifacts to AWS. | Not in daily use yet, but wired for `aws_upload.py`. |
| `tests/` | Pytest suite for shared win-calculation utilities. | Run with `make test`. |
| `Makefile` | Wraps env setup and per-game runs: `make setup`, `make run GAME=0_0_scatter`, etc. | `run` target activates the venv and executes the chosen game’s `run.py`. |

### Languages & Tooling
- **Python 3.12+** for the math engine.
- **Rust/Cargo** for `optimization_program`.
- Optional: `make`, `pip`, `virtualenv`.
- Output artifacts: lookup tables, force files, event logs, stat sheets, RGS publish files.

---

## 2. Build & Simulation Flow

1. **`make run GAME=...`**  
   - Uses `env/bin/python games/<game>/run.py`.
   - Current defaults (per `games/0_0_scatter/run.py`): `num_threads=32`, `batching_size=20_000`, `sims_per_mode=250_000`, compression on, profiling off (adjust down to 5k for quick loops if needed).

2. **`run.py` sequence**
   - Instantiates `GameConfig`, `GameState`, and `OptimizationSetup`.
   - Calls `create_books` (from `src/state/run_sims.py`) for each bet mode, writing temp JSON/ZST books.
   - Generates math configs (`generate_configs`) and, if enabled, runs the Rust optimizer followed by analysis.
   - Before RGS verification it auto-copies `library/lookup_tables/*.csv` → `library/publish_files/*_0.csv` to keep the published LUTs in sync.
   - Calls `utils/rgs_verification.execute_all_tests()` which sanity-checks LUT/book parity, payout hashes, etc.

3. **`create_books` internals**
   - Validates that `num_sims` divides evenly into `threads * batch_size`.
   - For each bet mode, dispatches `num_threads` processes running `gamestate.run_sims`.
   - `run_sims` iterates through spins based on distribution criteria (basegame/freegame/zero fences), accumulates wins, emits per-thread RTP (`"Thread X finished with ... RTP"`), and writes temporary lookup tables & force files.

4. **Optimization**
   - `OptimizationSetup` (Python) writes target RTP buckets, scaling, and guardrails to `math_config.json`.
   - `optimization_program` (Rust) reads that config and iteratively adjusts lookup-table weights until the observed distributions fall inside the provided ranges.
   - After optimization, rerun `generate_configs` to capture the tuned LUT weights.

5. **RGS Verification & Publishing**
   - `utils/rgs_verification.py` compares fresh books to `publish_files`, ensures compression flags are compatible, and warns if per-mode RTP drift exceeds the accepted delta (currently loose, slated to tighten once math stabilizes).

---

## 3. Shared Engine Modules (`src/`)

- `config/`: BetMode, Distribution, Config base classes; responsible for storing paytables, reels, bet-mode metadata.  
- `state/`: Core simulation loop (`state.py`), threading harness (`run_sims.py`).  
- `executables/`: Default win-handling logic (tumbles, event emission).  
- `calculations/`: Scatter pay calculator, line-pay helper, RNG utilities.  
- `events/`: Emits formatted payloads for downstream consumers (emitter, frontend).  
- `wins/`: Win tracking/manager classes.  
- `write_data/`: Serializes books, lookup tables, segmented LUTs, stat sheets.  
- All games extend these base classes via their `game_*` modules.

---

## 4. Utilities & Supporting Docs

- `docs/math_docs/*`: Deep dive into the math engine, gamestate overrides, optimization, uploads, etc. `math_docs/quickstart.md` explains the “Thread finished with X RTP” output.
- `docs/rgs_docs/*`: Expectations for the remote gaming server integration.
- `utils/analysis` & `utils/game_analytics`: Scripts for PAR sheets, stat summaries, or event digging.
- `utils/format_books_json.py`: Pretty-prints JSON books when compression is disabled.
- `utils/merge_luts`: Helper to stitch segmented LUTs when needed.
- `uploads/aws_*`: CLI glue for pushing lookup tables + configs to S3 (not currently in use).

---

## 5. Game Spotlight – `0_0_scatter`

### Goals / Current Theme
- Rebranded as **Candy Carnage 1000**, inspired by Sweet Bonanza 1000.  
- Scatter-pay, 6×5 grid, cascading wins, Sweet Bonanza-style tumbling multipliers only during free spins.  
- Bet modes: `base`, `bonus_hunt`, `bonus_buy`, `super_bonus_buy`.
- Target RTP split (pre-optimization): Base ≈ 62%, Regular FS ≈ 26%, Super FS ≈ 8%, overall ≈ 96.2% (±0.5% per slice).
- Volatility: Base = medium, Hunt = high, Regular FS = high, Super FS = very high.

### Important Files

| File | Description |
| --- | --- |
| `games/0_0_scatter/docs/candy_carnage_1000_spec.md` | Living spec describing mechanics, RTP targets, reel counts, bomb weights, buy rules, and workflow notes. |
| `game_config.py` | Defines paytable (3 tiers), scatter payouts, symbol aliases (`BS` counts as `S`), bet modes, distribution quotas, multiplier weights (regular vs super), free-spin retrigger amount (+5). Recently tuned to `zero_quota=0.05 / freegame_quota=0.12` for base and `0.08 / 0.18` for hunt. |
| `game_executables.py` | Handles tumble resolution, scatter replacements, and board enforcement (regular buy clamps to 4 `S`, super buy to 3 `S` + 1 `BS`). |
| `game_override.py` | Custom behaviours: assigns bomb multipliers only in free spins (uses the weights above), enforces “no BS in base/hunt except for super triggers”, optional bonus-hunt scatter boost hook (currently disabled). |
| `gamestate.py` | Overrides `run_spin` loop: draws board, forces scatter layouts when buying, applies hunt boosts, handles free-spin triggers, resets global multiplier each spin, awards retriggers (+5). |
| `game_optimization.py` | Defines optimizer guardrails: RTP targets per fence, scaling buckets, new mean/median bands (base 1.8–8, hunt 2–10, bonus 1.5–15, super 1.5–18), bias ranges. |
| `reels/BR0.csv`, `BR_HUNT.csv`, `FR0.csv`, `WCAP.csv` | Base & hunt reel strips (scatter counts `[9,9,8,8,7,6]` and `[11,10,10,10,9,9]` with ≥5-symbol spacing), free-spin reels, and win-cap reels. |
| `run.py` | Entry point described earlier (10 threads, 10k batch size, 5k sims right now).

### Mechanics Recap
- **Base / Hunt:**
  - Scatter pays anywhere; cascades remove winning symbols.
  - No multipliers in the base grid.
  - Bonus triggers: ≥4 scatters for regular FS (10 spins), or 3+ `S` plus exactly 1 `BS` for super FS.
  - `bonus_hunt` uses juiced reels + higher freegame quota to target ~1-in-70 triggers.

- **Regular Free Spins:**
  - Bomb set `{2,3,4,5,6,8,10,12,15,20,25,50,100,500,1000}` with weights targeting ~70% low / 25% mid / 5% high.
  - Bombs reset every spin; bombs only appear on winning tumbles, but probability per tumble is ~45%.
  - Retriggers: any 3+ scatters (+5 spins). `BS` never appears in free spins.

- **Super Free Spins:**
  - Minimum bomb 20×; current weights `{20:260, 25:220, 50:140, 75:80, 100:40, 500:8, 1000:1.5}` to bias teases.
  - Multipliers can appear even on dead boards (bomb with no win) to “blueball” the player, reinforcing the very-high-volatility feel.
  - Super buy entry board is forcibly `3×S + 1×BS`, and natural triggers respect whatever scatter mix landed (still paying 5×/100× as appropriate).

- **Bonus Buys:**
  - Regular buy = 100× bet; entry board clamped to exactly four `S` (no BS, no extra scatter pays).
  - Super buy = 500× bet; entry board shows 3×S + 1×BS visually with guaranteed ≥20× bomb.
  - Target EV for both buys: 96.2% ± 0.5%.

### Current Tweaks & Open Items
- **Distribution tuning:** Latest quotas drastically cooled base/hunt RTP; we’ll continue to tweak until the per-mode totals land near spec before running long (200k) simulations.
- **Bomb weights:** Super mode now has aggressive 20×+ distribution; still monitoring to ensure high bombs mostly tease unless a big tumble is underway.
- **Optimizer guardrails:** Already tightened; next step is to re-run PigFarm once reel/distribution math stabilizes.
- **Spec alignment:** The MKDocs spec mirrors these settings; keep updating it as decisions change.

### Useful Commands
```bash
# Quick 5k-per-mode run (current default)
make run GAME=0_0_scatter

# Regenerate math config + sync LUTs
PYTHONPATH=. env/bin/python games/0_0_scatter/run.py

# Run optimizer after math assets look good
env/bin/python games/0_0_scatter/run.py   # with run_optimization toggled on inside run.py
```

---

## 6. What to Remember When Re-Entering the Repo

- **Always sync LUTs before RGS checks** – already automated in `run.py`, but keep it in mind if you script custom flows.
- **Batch size vs sims** – `num_sims` must divide evenly by `threads * batching_size`. With 10 threads and 10k batches, use multiples of 100k (or lower like 5k when testing).
- **Look at both base & free splits** – the console output shows two numbers: `[baseGame: X, freeGame: Y]`. Use these to diagnose whether the RTP issue lives in the reels (base) or in forced freegames (distribution quotas).
- **Spec is the single source of truth** – update `games/0_0_scatter/docs/candy_carnage_1000_spec.md` whenever you change math so design/engineering stay aligned.
- **Optimizer triage order** – ① relax scaling ranges, ② adjust zero/freegame quotas, ③ only then touch paytables/reels.

With this overview + the per-game spec you should be able to pick up any task quickly, whether it’s code, math tuning, or documentation updates. Feel free to grow this doc as the project evolves. 


