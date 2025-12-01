# Candy Carnage 1000

## Summary

- 6×5 scatter-pay slot with cascades.
- RTP target ~96.2%; max win capped near 25,000×.
- Symbols: 5 lows (L1–L5), 4 highs (H1–H4), scatter `S`, super scatter `BS`, multiplier `M`.
- Bet modes:
  - `base` – standard cost 1×.
  - `bonus_hunt` – 3× bet, custom reel strip boosts regular scatters (≈1/70 entry) without increasing BS odds.
  - `bonus` – 100× buy, starts with 10 spins.
  - `super_bonus` – 500× buy, forces 3×`S` + 1×`BS` entry and minimum 20× bombs.

Paytable tiers follow the Sweet Bonanza 8–9 / 10–11 / 12+ bracket structure. Scatter pays: 4 scatters trigger only, 5 scatters pay 5×, 6+ scatters pay 100×, and `BS` counts toward both trigger and payout totals.

## Base Game

- 4+ total scatters trigger free spins (10 spins). Scatter counts beyond 4 only add payout; spin count stays fixed.
- Super bonus on natural spins requires 3+ regular scatters plus exactly one `BS`. Only one `BS` can exist on the base/bonus_hunt reels at a time.
- `bonus_hunt` mode uses bespoke base reels with extra scatter density on reels 1–3 and fewer dead lows; free-game reels are unchanged.

## Free Spins

- All entry paths start with 10 spins.
- Retrigger: landing 3 or more regular scatters during the bonus adds +5 spins flat.
- Multipliers reset to 1 at the start of every free spin. Bombs (`M`) appear only in bonuses, sum per tumble, and then multiply that tumble’s win.
- Regular bonus bomb weights heavily favor 2×–15×; super bonus bombs guarantee ≥20× with elevated 25×–50× frequency.
- `BS` never appears during regular or super free spins; it is base-only.

## Bonus Buys

- `bonus` buy: 100× bet, target EV ≈95–97%.
- `super_bonus` buy: 500× bet, target EV ≈95–97%, guarantees the `BS` entry condition and ≥20× bombs.

## Events

- `winInfo`: per-tumble symbol wins + multiplier context.
- `tumbleBanner`: running tumble totals with applied multiplier.
- `setWin`: total for the latest spin (base or bonus spin).
- `setTotalWin`: cumulative total for the round (increments through bonuses).

