# Candy Carnage 1000 – Math Iteration Plan

This plan tracks how we’ll iterate on `0_0_scatter` (Candy Carnage 1000) until the math, optimization, and artifacts are production ready. Each stage lists its goals, concrete tasks, and “exit criteria” before moving on.

---

## Stage 0 – Prep & Context

**Goals**
- Keep the high-level repo context handy (`docs/math_sdk_repo_overview.md`) so we know where everything lives.
- Ensure the spec (`games/0_0_scatter/docs/candy_carnage_1000_spec.md`) is the contract we’re working toward.

**Tasks**
1. Read/refresh `math_sdk_repo_overview.md`.
2. Re-align on the spec: RTP split targets, reel scatter counts, bomb weights, base hit-rate expectations.
3. Confirm `make run GAME=0_0_scatter` works (5k per mode for fast feedback) and LUT auto-sync is functioning.

**Exit Criteria**
- We can describe the repository architecture from memory.
- We know the current math knobs and the run workflow without re-reading code.

---

## Stage 1 – Stabilize Base & Hunt RTP

**Goals**
- Get base-mode and bonus-hunt RTP into the correct ballpark (base ≈ 0.55–0.65, hunt ≈ 0.9–1.1 relative to cost after contributions).
- Maintain the desired feel: base = medium volatility (30–35% hit rate, avg win 0.8–1.2×), hunt = high volatility with ~1-in-70 bonus entry.

**Tasks**
1. **Adjust distribution quotas**  
   - Start with `zero_quota=0.05 / freegame_quota=0.12` for base, `0.08 / 0.18` for hunt.  
   - If needed, tweak zero/freegame quotas in `game_config.py::build_base_distributions` to keep base hits lively while avoiding forced free-game floods.
2. **Quick sim loops**  
   - Run `make run GAME=0_0_scatter` (5k per mode).  
   - Record the base/hunt RTP and `baseGame vs freeGame` breakdown to see which component is misbehaving.
3. **Reel adjustments (if quotas aren’t enough)**  
   - For base: modify `reels/BR0.csv` scatter counts or spacing if natural trigger rate drifts away from 1-in-160.  
   - For hunt: keep per-reel scatter counts juiced but ensure there’s still ~30% base hit rate.
4. **Spec updates**  
   - Every time we change quotas or reels, update `candy_carnage_1000_spec.md` so docs match code.

**Exit Criteria**
- Base-mode threads consistently print ~0.55–0.65 RTP and the `baseGame` portion sits near 0.04 (≈4% per spin, aligning with the medium-volatility vibe).
- Bonus-hunt sits around ~1.0 RTP (cost = 3×, high variance acceptable) with the natural trigger rate near 1-in-70.
- Spec documents the final quotas and reel counts used.

**Current status (5k fast sims, Jan 2025)**
- Base-mode quota tune now sits at `zero=0.05`, `freegame=0.15`, yielding ~0.5–0.55 RTP (baseGame ≈0.035). We’ll watch whether further reel tweaks are needed to reach the 0.6 target.  
- Bonus-hunt currently uses `zero=0.05`, `freegame=0.45` and returns ~0.5–0.6 RTP. Still short of the 1.0 goal, but at least most spins now come from hunt reels instead of forced free games.

---

## Stage 2 – Free-Spin & Bomb Tuning

**Goals**
- Ensure regular bonus bombs follow the 70/25/5 feel and the EV matches the 96.2% ±0.5% requirement.
- Make super bonus bombs feel “very high volatility”: more dead spins, frequent 20×–100× bombs, occasional 500×/1000× teases.

**Tasks**
1. **Regular bomb weights**  
   - Verify `{2…1000}` weights produce the intended distribution via targeted buy simulations (e.g., run only `bonus` mode with 5k sims or the in-process instrumentation script).
2. **Super bomb adjustments**  
   - Evaluate `{20:260, 25:220, 50:140, 75:80, 100:40, 500:8, 1000:1.5}`.  
   - If high bombs pay too often, reduce 500×/1000× weights; if teases feel too rare, increase dead-board frequency instead.
3. **Retrigger cadence**  
   - Confirm retriggers occur roughly once every 3 bonuses (guideline). If too frequent, lighten scatter density during free spins.
4. **Spec documentation**  
   - Update multiplier tables + narrative in `candy_carnage_1000_spec.md`.

**Exit Criteria**
- Regular buy threads hover near 0.96 RTP and logs show the expected bomb distribution shape.
- Super buy threads land near 2.0 RTP (because cost=500×) with plenty of 25×+ teases but rare paid 500×/1000× hits.
- Spec matches the final bomb weights and behaviour.

**Current status**
- Instrumentation script (1k spins per buy) now reports: regular bombs ~70.6% low / 23.3% mid / 6.1% high; super bombs distribution now starts at 20× with weights heavily favouring the 20×/25×/50× trio and tapering into the ultra-rare 500×/1000× events.
- Spec updated with new weight tables: regular weights `[350, 300, 260, …, 70, 35, 10, 1.0, 0.2]`, super weights `{20:260, 25:220, 50:140, 75:80, 100:40, 500:8, 1000:1.5}`.

---

## Stage 3 – Long Sim & Optimization

**Goals**
- Produce high-confidence lookup tables via 200k+ sims per mode.
- Run PigFarm optimization to hit the final RTP buckets and verify all fences.

**Tasks**
1. **Scale sims up**  
   - Set `sims_per_mode = 200_000` (or higher) in `run.py`.  
   - Ensure `sims % (threads * batch_size) == 0`. With 10 threads & 10k batch, stick to multiples of 100k.
2. **Run `make run GAME=0_0_scatter`**  
   - Let both batches finish per mode.  
   - Verify `utils/rgs_verification` passes without MD5 mismatch (thanks to auto LUT sync).
3. **Enable optimizer**  
   - Flip `run_optimization` to `True` in `run.py`.  
   - Run `make run …` again (or call `OptimizationExecution` manually) to generate tuned LUTs.
4. **Check optimizer results**  
   - Confirm `math_config.json` consumes the updated guardrails (base m2m 1.8–8, etc.).  
   - Watch for “RTP too high/low” loops; apply the documented triage order if needed.

**Exit Criteria**
- Fresh lookup tables exist in `library/lookup_tables` + `publish_files`.
- Optimizer run completes without indefinite loops; per-mode RTP slices match spec within tolerance.
- RGS verification passes (only acceptable warning is the temporary “mode RTP difference” until we tighten thresholds).

---

## Stage 4 – Analysis & Handoff

**Goals**
- Produce supporting data (PAR sheets, stat summaries) and ensure frontend/backend teams know the exact math state.

**Tasks**
1. **Optional analysis**  
   - Set `run_analysis=True` to generate stat sheets via `utils/game_analytics`.
2. **Spec finalization**  
   - Make sure `candy_carnage_1000_spec.md` and `math_sdk_repo_overview.md` reference the final numbers (RTP, multipliers, reels, quotas).
3. **Documentation bundle**  
   - Deliver the spec, math-overview doc, and any optimizer logs to downstream teams.
4. **(Future) uploads**  
   - If needed, use `uploads/aws_upload.py` to push LUTs/configs to S3 (not wired yet).

**Exit Criteria**
- Spec + overview doc reflect the released math.
- Stakeholders have the math files and stats they need.
- Repo is ready for integration/QA runs.

---

## Tracking & Updates

- We’re using 5k-sim runs for fast iteration (`run.py` default). Switch to 200k when math stabilizes.
- Update this plan (or the TODO list in Cursor) whenever we complete a stage or change direction.
- Keep referencing `math_sdk_repo_overview.md` + `candy_carnage_1000_spec.md` so documentation stays synchronized with code.

With this roadmap we can iterate deliberately instead of chasing numbers blind. Let’s keep checking off stages until Candy Carnage 1000 is production-ready. 

