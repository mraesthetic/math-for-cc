# Backend Symbol ID Update Guide

## Overview

The game template now uses standardized symbol IDs that differ from the Space Dummies symbol IDs. All backend/RGS responses must use these new IDs.

## Symbol ID Mapping

### Low Symbols (Card Values)
| Old ID | New ID | Description |
|--------|--------|-------------|
| `l1`   | `s10`  | 10 (lowest card) |
| `l2`   | `sj`   | Jack |
| `l3`   | `sq`   | Queen |
| `l4`   | `sk`   | King |
| `l5`   | `sa`   | Ace |

### Mid-Tier Symbols
| Old ID | New ID | Description |
|--------|--------|-------------|
| `c1`   | `sc1`  | Mid symbol 1 |
| `c2`   | `sc2`  | Mid symbol 2 |
| `c3`   | `sc3`  | Mid symbol 3 |

### Premium Symbols (High-Value)
| Old ID | New ID | Description |
|--------|--------|-------------|
| `prem1` | `prem1` | Premium symbol 1 (no change) |
| `prem2`  | `prem2`  | Premium symbol 2 (no change) |

### Feature Symbols
| Old ID | New ID | Description |
|--------|--------|-------------|
| `W` or `wild` | `wild` | Wild symbol |
| `S` or `scatter` | `scatter` | Scatter symbol |

## What Needs to Change

### 1. Reelstrip Configuration

**Before (Space Dummies):**
```python
# Old reelstrips
reelstrips = [
    ['l1', 'l2', 'l3', 'prem1', 'wild', 'l4', 'l5', 'scatter', ...],
    # ... more reels
]
```

**After (Game Template):**
```python
# New reelstrips
reelstrips = [
    ['s10', 'sj', 'sq', 'prem1', 'wild', 'sk', 'sa', 'scatter', ...],
    # ... more reels
]
```

### 2. Paytable Configuration

**Before:**
```python
paytable = {
    'l1': [0, 0, 0.2, 0.6, 2.0],
    'l2': [0, 0, 0.2, 0.8, 2.4],
    'l3': [0, 0, 0.2, 1.0, 3.0],
    'l4': [0, 0, 0.4, 1.4, 4.0],
    'l5': [0, 0, 0.4, 2.0, 5.0],
    'c1': [0, 0, 1.0, 3.0, 6.0],
    'c2': [0, 0, 1.2, 4.0, 8.0],
    'c3': [0, 0, 1.4, 5.0, 10.0],
    # ...
}
```

**After:**
```python
paytable = {
    's10': [0, 0, 0.2, 0.6, 2.0],
    'sj': [0, 0, 0.2, 0.8, 2.4],
    'sq': [0, 0, 0.2, 1.0, 3.0],
    'sk': [0, 0, 0.4, 1.4, 4.0],
    'sa': [0, 0, 0.4, 2.0, 5.0],
    'sc1': [0, 0, 1.0, 3.0, 6.0],
    'sc2': [0, 0, 1.2, 4.0, 8.0],
    'sc3': [0, 0, 1.4, 5.0, 10.0],
    # ...
}
```

### 3. Book Event Responses

All book events sent to the frontend must use the new symbol IDs in the `board` arrays:

**Before:**
```json
{
  "bookEvent": {
    "type": "reelsSpin",
    "board": [
      [{"name": "l1"}, {"name": "l2"}, {"name": "l3"}, {"name": "l4"}],
      [{"name": "l5"}, {"name": "c1"}, {"name": "c2"}, {"name": "c3"}],
      ...
    ]
  }
}
```

**After:**
```json
{
  "bookEvent": {
    "type": "reelsSpin",
    "board": [
      [{"name": "s10"}, {"name": "sj"}, {"name": "sq"}, {"name": "sk"}],
      [{"name": "sa"}, {"name": "sc1"}, {"name": "sc2"}, {"name": "sc3"}],
      ...
    ]
  }
}
```

## Testing the Changes

After updating your backend:

1. Start your backend/RGS server
2. Run the frontend: `pnpm run dev`
3. Place a bet and verify that:
   - Symbols render correctly on the board
   - No console errors about missing symbols
   - Winning combinations are calculated correctly

## Common Mistakes

❌ **Don't** mix old and new symbol IDs  
❌ **Don't** forget to update symbol removal feature (if used)  
❌ **Don't** forget to update bonus game reelstrips  

✅ **Do** update ALL reelstrips (base game, free games, bonus)  
✅ **Do** update ALL configuration files  
✅ **Do** test thoroughly before deploying  

## Reference: Complete Symbol List

Frontend expects these exact symbol IDs (case-sensitive):

```typescript
// From apps/game-template/src/game/config.ts
paytable: {
  symbols: {
    // Low symbols
    s10: [0, 0, 0.2, 0.6, 2.0],
    sj: [0, 0, 0.2, 0.8, 2.4],
    sq: [0, 0, 0.2, 1.0, 3.0],
    sk: [0, 0, 0.4, 1.4, 4.0],
    sa: [0, 0, 0.4, 2.0, 5.0],
    
    // Mid symbols
    sc1: [0, 0, 1.0, 3.0, 6.0],
    sc2: [0, 0, 1.2, 4.0, 8.0],
    sc3: [0, 0, 1.4, 5.0, 10.0],
    
    // Premium symbols
    prem1: [0, 0, 3.0, 15.0, 40.0],
    prem2: [0, 0, 4.0, 20.0, 100.0],
    
    // Feature symbols
    wild: [0, 0, 10.0, 50.0, 200.0],
    scatter: [0, 0, 2.0, 5.0, 50.0],
  }
}
```

## Questions?

If you encounter any issues, check:
1. Backend logs for the symbol IDs being sent
2. Browser console for frontend errors
3. The frontend `config.ts` file for the expected symbol IDs
4. The frontend `constants.ts` `SYMBOL_INFO_MAP` for defined symbols

## Related Documentation

- See `docs/backend/BACKEND_INTEGRATION_GUIDE.md` for full backend integration details
- See `docs/backend/BACKEND_QUICK_REFERENCE.md` for API format reference


