# Candy Carnage 1000 – Draft Math & Design Spec

> **Status:** Working draft pulled from initial Sweet Bonanza 1000 parity notes. Will be refined after review and SDK validation.

## 1. Core Specs

- **Grid:** 6×5
- **Model:** All-ways / scatter pays (Sweet Bonanza style)
- **Mechanics:**
  - Cascading/tumbling reveals
  - Free spins with multiplier bombs
  - Dual bonus paths: Regular FS and Super FS (Super guarantees ≥20× bomb)
- **Targets:**
  - RTP ≈ 96.2%
  - Max win ≈ 25,000× bet
  - Volatility: very high (SB1000 profile)

Design workstreams:
1. RTP split
2. Base symbol set + weighting
3. Scatter distribution / trigger odds
4. Free-spin structure + multipliers
5. Bonus buys & hunt mode
6. Max-win and volatility shaping

### Volatility Intent (per mode)

- **Base spins:** Medium volatility — plenty of 0.8–1.2× trickles with occasional 20–50× pops.
- **Bonus hunt:** High volatility — drier base reels offset by fast 1-in-70 entries.
- **Regular free spins:** High volatility — 70/25/5 bomb mix keeps most wins modest but lets 100× moments rip.
- **Super free spins:** Very high volatility — more dead boards, but constant 20×+ bomb drops with frequent 500×/1000× teases (bombs can land even if no win connects).

## 2. RTP Split (Top-Down)

| Component                | Target RTP | Notes                                                                 |
| ------------------------ | ---------- | --------------------------------------------------------------------- |
| Base game (no features) | ~62%       | Includes tumbles + scatter pays only (**±0.5% per-slice tolerance**)  |
| Regular free spins      | ~26%       | Natural triggers + bonus-buy contribution (**±0.5% per slice**)       |
| Super free spins        | ~8%        | Natural + super-buy contribution (**±0.5% per slice**)                |
| Rounding / misc         | ~0.2%      | Leave margin for tuning                                               |
| **Total**               | **96.2%**  | Optimizer must finish at exactly **96.2%** overall (no tolerance)     |

Use simulation to fine-tune each slice once the math assets are in place.

## 3. Base Game Design

### 3.1 Symbol Suite

- **Low symbols (5):** L1,L2,L3,L4,L5
- **High symbols (4):** H1,H2,H3,H4
- **RegularScatter:** S - need to land 4+ of these to get into the bonus
- **SuperScatter:** BS - need to land 1 of these with 3+ regular scatters when spinning the slot in order to get into the super_bonus OR you can buy it for 500x bet.
- **No multiplier bombs in base** (bombs are exclusive to bonuses)

Total symbols on reels: 11 (9 paying + 2 different scatters) and this suite is **locked permanently**—no wilds/blockers will be added later.

### 3.2 Hit Model Targets

- Overall hit rate (any win): **~30–35%** of spins, including cascades (feel-first; if RTP runs hot, reduce average win size instead of hit frequency).
- Average cascades per winning spin: **1.6–2.0**; bake this distribution into optimizer fences so we hit the tumble depth “feel”.
- Average winning-spin payout: **≈0.8–1.2×** bet (lets us keep RTP on target while honoring the hit-rate spec).
- Resulting base-game RTP: **≈62%** (±0.5% allowed).

Control via symbol weights per reel (or RNG table) and scatter-pay paytable.

### 3.3 Paytable Shape

- Thresholds map to scatter-count brackets:
  - `t1` → 8–9 of a kind
  - `t2` → 10–11 of a kind
  - `t3` → 12+ of a kind

```
pay_group = {
    # HIGH SYMBOLS
    (t1, "H1"): 10.0,
    (t2, "H1"): 25.0,
    (t3, "H1"): 50.0,

    (t1, "H2"): 2.5,
    (t2, "H2"): 10.0,
    (t3, "H2"): 25.0,

    (t1, "H3"): 2.0,
    (t2, "H3"): 5.0,
    (t3, "H3"): 15.0,

    (t1, "H4"): 1.5,
    (t2, "H4"): 2.0,
    (t3, "H4"): 12.0,

    # LOW SYMBOLS
    (t1, "L1"): 1.0,
    (t2, "L1"): 1.5,
    (t3, "L1"): 10.0,

    (t1, "L2"): 0.8,
    (t2, "L2"): 1.2,
    (t3, "L2"): 8.0,

    (t1, "L3"): 0.5,
    (t2, "L3"): 1.0,
    (t3, "L3"): 5.0,

    (t1, "L4"): 0.4,
    (t2, "L4"): 0.9,
    (t3, "L4"): 4.0,

    (t1, "L5"): 0.25,
    (t2, "L5"): 0.75,
    (t3, "L5"): 2.0,
}
```

Tweak individual symbol multipliers and reel weights to reach the hit-rate/RTP goals. Scatter payouts are defined separately below.

> Engine now runs with these **three tiers only** (old `t4` handling removed from math + docs).

### 3.4 Final Reel Strips & Scatter Density

- `BR0.csv` (normal spins): per-reel scatter counts `[9, 9, 8, 8, 7, 6]` with enforced **≥5-symbol spacing** so a reel can never display more than one scatter at once. Large-batch Monte-Carlo (1M spins) yields a **4+ scatter trigger rate of ≈0.0062 (≈1 in 161 spins)**, right on the 1-in-160 target.
- `BR_HUNT.csv` (bonus_hunt mode): boosted counts `[11, 10, 10, 10, 9, 9]` keep the same spacing rule but overweight reels 1–4 to juice teases. Empirical sampling (~1M spins) lands at **≈0.0145 (≈1 in 69 spins)**—close to the desired 1-in-70 and intentionally a hair on the generous side per spec.
- `FR0.csv` (free spins) and `WCAP.csv` (win-cap protects) remain unchanged from the template.

Always regenerate lookup tables/books after touching these strips to keep downstream math assets in sync.

### 3.5 Distribution Quotas (current)

- **Base bet mode:** `zero_quota = 0.07`, `freegame_quota = 0.08`, remainder (~0.85) stays in the organic basegame fence. This keeps the reels in charge while giving the optimizer just enough forced data.
- **Bonus hunt:** `zero_quota = 0.05`, `freegame_quota = 0.45`, remainder (~0.50) runs through basegame hits. Forced freegames act as a top-up while the juiced reels do most of the work.
- **Bonus / Super buys:** still run 100% through the freegame fence (quota = 1.0) because buys skip base-play entirely.

## 4. Scatter & Free-Spin Triggering

### 4.1 Conditions

- **4+ scatters anywhere** → Free spins
- Entry paths:
  - 4–6 total scatters (any mix of `S`/`BS`) = Regular FS (10 spins)
- 3+ regular scatters **plus exactly one `BS`** during base/hunt play = Super FS (the 500× super-buy automatically converts one scatter to `BS` before the board renders, so the entry board always shows `3×S + 1×BS`)
  - Regular FS buy costs **100×**; Super FS buy costs **500×** and starts with 1 `BS` + 3 `S` on the entry board

### 4.1.1 Scatter Payouts

- 4 scatters → trigger only, **no payout**
- 5 scatters → **5× bet**
- 6 scatters → **100× bet**
- Super scatters count toward both trigger and payout totals (e.g., `3S + 1BS` triggers super bonus and pays as 4 scatters).

### 4.2 Trigger Frequency Targets

- Regular FS: **1 in 120–180** spins (0.55–0.8%) → current reels sim at **≈1 in 161** (base) and **≈1 in 69** (bonus_hunt).
- Super FS (natural): **Target ≈1 in 1,800 spins** (rare, but reachable; keep BS frequency identical between base and hunt).
- Empirical (current reels, no hunt boost):
  - Normal spins: **0.62%** (≈1/161) regular triggers
  - `bonus_hunt`: **~1.45%** (≈1/69)

Tuning levers:
- Scatter weights per reel (reel strips)
- Direct probability tables (if step-based RNG)

### 4.3 Scatter Payout Handling

- Scatter pays (5× for 5 scatters, 100× for 6) always settle **before** the feature starts, both in base and inside free spins.
- `BS` symbols **alias to `S` for payouts**: `4S + 1BS` pays 5× base bet, `5S + 1BS` pays 100× base bet, etc.
- Payout reference is always **base bet**, even when entering via bonus buys.
- Natural triggers respect the exact scatter mix that landed (no clamping). Bonus buys, however, clamp to fixed entry boards (Section 6) so scatter pays cannot overfire.

## 5. Free Spins & Multiplier Bombs

### 5.1 Regular FS Rules

- Start with **10 spins**
- Cascades identical to base
- **Multiplier bombs** can land on winning tumbles
  - Sum all bombs in a tumble
  - Multiply the tumble win by summed value
  - Bombs never pay alone
- **Retriggers:** any 3+ scatters award **+5 spins** (flat, no scaling for higher counts)
- **Super scatters never appear** in either bonus; they exist only on base/bonus_hunt reels

### 5.2 Multiplier Set (Regular)

`{2, 3, 4, 5, 6, 8, 10, 12, 15, 20, 25, 50, 100, 500, 1000}`

Suggested relative weights (normalize in engine):

| Mult | Weight |
| ---- | ------ |
| 2×   | 350    |
| 3×   | 300    |
| 4×   | 260    |
| 5×   | 220    |
| 6×   | 180    |
| 8×   | 120    |
| 10×  | 150    |
| 12×  | 130    |
| 15×  | 110    |
| 20×  | 90     |
| 25×  | 70     |
| 50×  | 35     |
| 100× | 10     |
| 500× | 1.0    |
| 1000×| 0.2    |

> Optimizer may tweak these counts freely **as long as the feel stays ~70% low bombs / 25% mid / 5% high**.

### 5.3 Super Bonus Multipliers

- Minimum bomb value **20×** (engine-enforced).
- Candidate set (current): `{20, 25, 50, 75, 100, 500, 1000}` — the extra 75× rung gives us a controllable mid-high stopgap.
- Intent: **very high volatility** — more dead spins, but bomb reels constantly flash 25×+ values with frequent 500×/1000× teases (bombs can drop even if no win connects).

Example weights (mirrors `game_config.py`):

| Mult | Weight |
| ---- | ------ |
| 20×  | 260    |
| 25×  | 220    |
| 50×  | 140    |
| 75×  | 80     |
| 100× | 40     |
| 500× | 8      |
| 1000×| 1.5    |

### 5.4 Bomb Frequency

Regular FS starting point:

- **Winning tumble** has ~40–50% chance to spawn bombs
- When bombs appear: 80% single bomb, 20% multi-bomb

Super FS:

- Winning tumble has ~60–70% chance
- Bomb count mix: 60% single, 30% double, 10% triple+

Use these knobs (frequency × size × hit rate) to hit target average bonus values. Treat the listed frequencies (regular: 40–50% chance of bombs per win, super: 60–70%) plus bomb-count splits (80/20 regular, 60/30/10 super) as **mood boards** the optimizer can bend to meet EV. Track retrigger cadence (~1 retrigger every 3 bonuses) as another feel metric rather than a hard rule. Remember that bombs can drop on dead boards; lean into that for super mode so 500×/1000× blueballs are common.

### 5.5 Observed Multiplier Distributions (quick check)

Small-scale direct sims (500 bonus-buy rounds per mode) to validate implementation:

| Mode           | Mult events | Avg board mult | Top hits (count)                                            | Bomb count split                         |
| -------------- | ----------- | -------------- | ----------------------------------------------------------- | ---------------------------------------- |
| Regular bonus  | 952         | **≈11.9×**     | 2×155, 3×121, 4×109, 5×103, 6×90, 8×71, 25×47, 10×46, 12×32 | 1 bomb 786, 2 bombs 145, 3 bombs 20, 4=1 |
| Super bonus    | 952         | **≈41.5×**     | 20×225, 25×204, 30×146, 40×123, 50×79, 75×26, 100×21        | same bomb split as above                 |

Larger sims will tighten these numbers, but the shape already matches the intended Sweet Bonanza 1000 feel (many low-mid bombs, super mode dominated by 20×–50×).

## 6. Bonus Buys

| Mode          | Cost | Target EV  | Notes                                                                                     |
| ------------- | ---- | ---------- | ----------------------------------------------------------------------------------------- |
| Regular buy   | 100× | 95.7–96.7× | Clamp entry board to **exactly four regular scatters**; no BS allowed, no extra scat pays. |
| Super buy     | 500× | 481–490×   | Clamp entry board to **exactly 3×S + 1×BS**; min bomb 20× guaranteed from spin 1.          |

Both buys must converge to **96.2% ±0.5%** RTP after tuning. Adjust bomb frequency, weights, retrigger rate, and high-symbol density during FS until simulations converge on desired EV. Since boards are clamped, scatter payouts do **not** apply during buys—players see only the prescribed entry patterns.

## 7. Bonus Hunt Mode (`bonus_hunt`)

Goal: higher feature rate per spin without inflating RTP.

Levers:

- Increase scatter weights (esp. reels 1–3)
- Reduce dead symbols on early reels (~15–20% cut)
- Make reel 3 most scatter-heavy
- Decrease base-game hits to offset added feature EV

Targets:

- Regular bonus trigger ~**1 in 70** spins (focus on boosting regular scatters only).
- Base hit rate should still hover near **30%** to avoid completely dead spins (still lower than base mode).
- BS frequency must remain identical to base mode (match per-reel counts; positions can differ to keep reels interesting).
- Example RTP split (feel reference; will adjust after sims):

| Mode         | Base RTP | FS RTP | Total RTP |
| ------------ | -------- | ------ | --------- |
| Normal spins | ~58%     | ~38%   | ~96%      |
| bonus_hunt   | ~45%     | ~51%   | ~96%      |

Implementation: dedicated bet-mode config (`mode="bonus_hunt"`) with bespoke reel strips and/or distribution overrides.

### 7.1 Target Win-Bucket Contributions

Use the optimization program to steer each mode toward the following RTP splits (percentages reference the RTP share *within* that mode/bucket) — treat them as **directional bands** and be ready to compress/expand once real data comes in:

- **Normal spins (≈62% RTP total)**
  - 0× spins: 30–35% of spins (0% RTP)
  - 0–1×: ~10% RTP
  - 1–5×: ~20% RTP
  - 5–20×: ~14% RTP
  - 20–50×: ~6% RTP
  - 50–100×: ~2% RTP
- **Regular free spins (≈26% RTP normal, 42–44% in hunt)**
  - 0–20×: ~10% RTP
  - 20–50×: ~20%
  - 50–100×: ~25%
  - 100–250×: ~25%
  - 250–500×: ~15%
  - 500–1000×: ~4%
  - 1000–25,000×: ~1%
- **Super free spins (≈8% RTP)**
  - 0–50×: 5–8%
  - 50–100×: 10–15%
  - 100–250×: 25%
  - 250–500×: 25%
  - 500–1,000×: 20%
  - 1,000–2,500×: 7%
  - 2,500–25,000×: 2–3%

Feed these ranges into `optimization_program` (distribution buckets + scaling) once reel math is stable; provide **wide min/max bands** so PigFarm can explore, then tighten after we collect empirical curves.

## 8. Max Win & Volatility

- Target **~25,000×** top prize (engine hard-cap: once cumulative payout hits 25,000×, feature ends immediately and win is locked).
- Strategies:
  - Prefer organic volatility; avoid explicit bomb-count caps unless absolutely necessary.
  - Keep ultra-high multipliers extremely rare but present so we can craft hype moments.
  - Require near-full board of H1 + monster bomb (or similar) for the cap.
  - Build **five reproducible scripted scenarios** that demonstrably reach max win so QA/marketing can showcase them.
- Validation:
  - Log every win ≥1,000× (and especially ≥5,000×) to CSV for auditing.
  - Track summary stats (mean, median, P95, P99) alongside those raw hits to monitor volatility drift.

## 9. Tooling & Verification

- `run.py` now auto-syncs fresh lookup tables into `library/publish_files` before RGS checks—no manual copy steps.
- While reels are still moving, we allow wide RTP variance during `execute_all_tests`; once reel math stabilizes we’ll tighten the warning threshold (goal: ≤5% mode-to-mode delta).
- Always run `make run GAME=0_0_scatter` after reel/math edits so the synced LUTs stay aligned with books before optimizer/analysis steps.
- Optimizer triage when it screams “RTP too high”: (1) relax ConstructScaling top buckets, (2) bleed a little quota from the freegame distribution back into the zero fence (base/hunt) before touching reels/pays, (3) only then tweak strips or paytable values.

---

### Next Steps After Review

1. Confirm/adjust numeric targets (RTP slices, trigger odds, multipliers).
2. Translate this spec into concrete math assets (paytable, reel strips, distributions).
3. Run math-SDK sims per mode to measure RTP, hit rate, and volatility.
4. Iterate until results align with the finalized spec.

