# Backend Integration Guide

**For Backend Developers: How to Build Games Compatible with This Template**

This guide explains what the backend needs to provide for games built with this template to work correctly.

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Configuration Files](#configuration-files)
3. [Book Event System](#book-event-system)
4. [Game Flow](#game-flow)
5. [Game Type Implementations](#game-type-implementations)
6. [Math Model Requirements](#math-model-requirements)
7. [Testing & Validation](#testing--validation)
8. [API Reference](#api-reference)

---

## Overview

### What is a "Book"?

A **book** is the backend's response to a spin request. It contains:
- The **outcome** of the spin (symbols on reels)
- A sequence of **book events** (what happens during the spin)
- **Win information** (amount, winning lines/clusters)
- **Feature triggers** (free spins, bonuses, etc.)

### Frontend Responsibilities

The frontend (this template):
- ✅ Displays the game UI
- ✅ Handles user input
- ✅ Animates book events in sequence
- ✅ Shows wins and celebrations
- ✅ Manages game state and settings

### Backend Responsibilities

The backend (your math model):
- ✅ Generates random outcomes
- ✅ Evaluates wins
- ✅ Triggers features based on rules
- ✅ Returns book events that describe what happened
- ✅ Ensures RTP and certified math

---

## Configuration Files

### 1. Game Configuration (`src/game/config.ts`)

The frontend game configuration file that you need to understand:

```typescript
{
  gameName: 'kaiju_clash',
  gameID: '0_0_kaiju_clash',
  
  // Math properties you must match
  rtp: 0.962,              // 96.2% RTP
  volatility: 'High',
  
  // Grid configuration
  numReels: 5,
  numRows: [4, 4, 4, 4, 4], // 5×4 grid
  
  // Enabled features (backend must support these)
  features: {
    expandingWilds: true,
    freeSpins: true,
    bonusBuy: true,
  },
  
  // Paytable (backend must use these exact values)
  paytable: {
    symbols: {
      high_1: [0, 0, 5, 25, 100],  // 3/4/5 of a kind
      wild: [0, 0, 10, 50, 200],
      scatter: [0, 0, 2, 5, 50],
    }
  }
}
```

**Backend Action Items:**
1. ✅ Read the `config.ts` file to understand game parameters
2. ✅ Match the RTP value in your math model
3. ✅ Use the exact paytable values
4. ✅ Support enabled features
5. ✅ Generate outcomes that fit the grid size

---

### 2. Theme Configuration (`src/game/theme.json`)

Maps symbol IDs to visual assets:

```json
{
  "game": {
    "id": "0_0_kaiju_clash",
    "name": "Kaiju Clash"
  },
  "symbols": {
    "high_1": {
      "id": "high_1",
      "path": "assets/images/symbols/sym_high_1.png"
    },
    "wild": {
      "id": "wild",
      "path": "assets/images/symbols/sym_wild.png",
      "type": "wild"
    }
  }
}
```

**Backend Action Items:**
1. ✅ Use the symbol IDs from theme.json in your book responses
2. ✅ Symbol IDs must match between config.ts, theme.json, and your backend

---

### 3. Symbol Constants (`src/game/constants.ts`)

Symbol metadata:

```typescript
export const SYMBOL_INFO_MAP = {
  high_1: { id: 'high_1', value: 5, type: 'high' },
  wild: { id: 'wild', value: 10, type: 'wild', substitutes: true },
  scatter: { id: 'scatter', value: 2, type: 'scatter', triggersBonus: true },
};
```

**Backend Action Items:**
1. ✅ Understand which symbols are wilds (substitute for others)
2. ✅ Know which symbols trigger bonuses
3. ✅ Use these IDs in your reel strips and outcomes

---

## Book Event System

### What Are Book Events?

Book events are **sequential actions** that describe what happens during a spin. The frontend plays them in order.

### Book Event Flow

```typescript
{
  bookId: "abc123",
  events: [
    { index: 0, type: 'reveal', outcome: [...] },      // Show spin result
    { index: 1, type: 'expandWild', reels: [2, 4] },   // Expand wilds on reels 2 & 4
    { index: 2, type: 'evaluateWin', wins: [...] },    // Show wins
    { index: 3, type: 'triggerBonus', bonusType: 'free_spins' }, // Trigger free spins
  ]
}
```

---

## Game Flow

### Base Game Spin

```
1. User clicks SPIN
2. Frontend sends spin request to backend
3. Backend generates outcome and returns book
4. Frontend processes book events sequentially:
   a. Spin reels
   b. Reveal outcome (book event: 'reveal')
   c. Apply features (book events: 'expandWild', 'cascade', etc.)
   d. Evaluate wins (book event: 'evaluateWin')
   e. Trigger bonuses (book event: 'triggerBonus')
5. Frontend updates balance and waits for next spin
```

### Example API Flow

```typescript
// 1. Frontend → Backend: Spin request
POST /api/spin
{
  gameId: "0_0_kaiju_clash",
  betAmount: 1.00,
  betMode: "base",
  sessionId: "xyz789"
}

// 2. Backend → Frontend: Book response
{
  bookId: "book_123",
  balanceBefore: 100.00,
  balanceAfter: 95.00,
  totalWin: 0,
  events: [
    {
      index: 0,
      type: "reveal",
      outcome: [
        ["high_1", "low_2", "wild", "low_3"],      // Reel 1
        ["low_3", "high_2", "low_1", "high_1"],    // Reel 2
        ["wild", "wild", "wild", "low_2"],         // Reel 3 (wilds!)
        ["high_1", "low_3", "high_2", "low_1"],    // Reel 4
        ["low_2", "high_1", "low_3", "high_2"]     // Reel 5
      ],
      stopPositions: [12, 8, 15, 3, 22]
    },
    {
      index: 1,
      type: "expandWild",
      reels: [2],  // Reel 3 has wilds, expand it
      multiplier: 2
    },
    {
      index: 2,
      type: "evaluateWin",
      wins: [
        {
          winId: "win_1",
          symbolId: "high_1",
          positions: [[0,0], [1,3], [2,0], [3,0], [4,1]],
          count: 5,
          multiplier: 2,  // From wild multiplier
          payout: 200     // 100 × 2
        }
      ],
      totalWin: 200
    }
  ]
}
```

---

## Game Type Implementations

### 1. Classic Payline Slots

**What Backend Needs to Send:**

```typescript
// Book event 1: Reveal outcome
{
  index: 0,
  type: "reveal",
  outcome: [
    ["high_1", "low_2", "wild", "low_3"],  // Each reel
    // ... 5 reels total
  ],
  stopPositions: [12, 8, 15, 3, 22]
}

// Book event 2: Evaluate wins
{
  index: 1,
  type: "evaluateWin",
  wins: [
    {
      winId: "win_1",
      symbolId: "high_1",
      paylineId: "line_0",           // Which payline won
      positions: [[0,0], [1,0], [2,0], [3,0], [4,0]],
      count: 5,
      multiplier: 1,
      payout: 100
    }
  ],
  totalWin: 100
}
```

**Math Requirements:**
- ✅ Evaluate wins on paylines defined in config
- ✅ Left-to-right only (standard)
- ✅ Wilds substitute for all symbols except scatter
- ✅ Use paytable values from config.ts

---

### 2. Expanding Wilds

**What Backend Needs to Send:**

```typescript
// Event 1: Reveal
{
  index: 0,
  type: "reveal",
  outcome: [...],  // Include wild symbols on some reels
}

// Event 2: Expand wilds
{
  index: 1,
  type: "expandWild",
  reels: [2, 4],              // Which reels have wilds that expand
  multipliers: [2, 3],        // Optional: multiplier per reel
  expandToPositions: [        // Optional: specify exact positions
    [2, 0], [2, 1], [2, 2], [2, 3],  // Reel 2, all positions
    [4, 0], [4, 1], [4, 2], [4, 3]   // Reel 4, all positions
  ]
}

// Event 3: Evaluate wins (with expanded wilds)
{
  index: 2,
  type: "evaluateWin",
  wins: [...],
  totalWin: 500
}
```

**Math Requirements:**
- ✅ Detect when wild symbols land
- ✅ Expand wilds to fill entire reel
- ✅ Optional: Apply multipliers to expanded wilds
- ✅ Evaluate wins AFTER expansion
- ✅ Higher hit frequency for wilds = higher volatility

**Configuration to Check:**

```typescript
features: {
  expandingWilds: true,
},
expandingWildConfig: {
  eligibleReels: [0, 1, 2, 3, 4],  // Which reels can expand
  expandingSymbol: 'wild',
  multipliers: [1, 2, 3, 5],       // Possible multiplier values
}
```

---

### 3. Hold & Spin

**What Backend Needs to Send:**

```typescript
// Event 1: Reveal (6+ coin symbols trigger feature)
{
  index: 0,
  type: "reveal",
  outcome: [...],  // Include 6+ "coin" symbols
}

// Event 2: Trigger hold & spin
{
  index: 1,
  type: "triggerHoldAndSpin",
  triggeredBy: ["coin", "coin", "coin", "coin", "coin", "coin"],
  initialSpins: 3,
  initialCoins: [
    { position: [0, 1], value: 10 },
    { position: [1, 2], value: 15 },
    { position: [2, 0], value: 20 },
    // ... 6 coins total
  ]
}

// Event 3-N: Each respin
{
  index: 2,
  type: "holdAndSpinRespin",
  spinsRemaining: 3,
  newCoins: [
    { position: [3, 1], value: 25 }
  ],
  resetCounter: true  // New coin landed, reset to 3 spins
}

// Final event: Feature end
{
  index: 10,
  type: "holdAndSpinEnd",
  totalCoinValue: 450,
  jackpots: [
    { type: "mini", value: 50 },
    { type: "grand", value: 1000 }
  ],
  totalWin: 1500
}
```

**Math Requirements:**
- ✅ 6+ coin symbols trigger feature
- ✅ Start with 3 respins
- ✅ Each new coin resets respin counter to 3
- ✅ Feature ends when spins reach 0 or grid is full
- ✅ Calculate jackpots based on coins collected
- ✅ Grand jackpot = all 15 positions filled

**Configuration to Check:**

```typescript
features: {
  holdAndSpin: true,
},
holdAndSpinConfig: {
  triggerSymbol: 'coin',
  minTriggerCount: 6,
  initialRespins: 3,
  jackpots: {
    mini: { threshold: 10, value: 50 },
    minor: { threshold: 12, value: 100 },
    major: { threshold: 14, value: 500 },
    grand: { threshold: 15, value: 1000 }
  }
}
```

---

### 4. Cascading Reels

**What Backend Needs to Send:**

```typescript
// Event 1: Initial reveal
{
  index: 0,
  type: "reveal",
  outcome: [...],
}

// Event 2: Evaluate initial wins
{
  index: 1,
  type: "evaluateWin",
  wins: [...],
  totalWin: 50,
  multiplier: 1  // Cascade multiplier starts at 1
}

// Event 3: Cascade (remove winning symbols)
{
  index: 2,
  type: "cascade",
  removePositions: [[0,0], [1,0], [2,0], [3,0], [4,0]],  // Winning positions
  newSymbols: [
    { position: [0, 0], symbol: "low_3" },
    { position: [1, 0], symbol: "high_1" },
    // ... new symbols that drop down
  ],
  cascadeNumber: 1,
  nextMultiplier: 2  // Multiplier increases
}

// Event 4: Evaluate cascade win
{
  index: 3,
  type: "evaluateWin",
  wins: [...],
  totalWin: 100,
  multiplier: 2  // Applied to this win
}

// Event 5: Another cascade (if more wins)
{
  index: 4,
  type: "cascade",
  removePositions: [...],
  newSymbols: [...],
  cascadeNumber: 2,
  nextMultiplier: 3
}

// ... continues until no more wins
```

**Math Requirements:**
- ✅ After each win, remove winning symbols
- ✅ Drop symbols down to fill gaps
- ✅ Add new symbols from top
- ✅ Increase multiplier with each cascade (1x → 2x → 3x → 5x → 10x)
- ✅ Continue until no more wins
- ✅ Return all cascades in single book

**Configuration to Check:**

```typescript
features: {
  cascadingReels: true,
},
cascadeConfig: {
  multiplierProgression: [1, 2, 3, 5, 10],  // Multiplier per cascade
  maxCascades: 10,  // Safety limit
}
```

---

### 5. Cluster Pays

**What Backend Needs to Send:**

```typescript
// Event 1: Reveal (7×7 grid)
{
  index: 0,
  type: "reveal",
  outcome: [
    ["high_1", "low_2", "high_1", "low_3", "high_1", "low_1", "high_2"],
    // ... 7 reels × 7 rows
  ],
}

// Event 2: Evaluate clusters
{
  index: 1,
  type: "evaluateCluster",
  clusters: [
    {
      clusterId: "cluster_1",
      symbolId: "high_1",
      positions: [
        [0, 0], [0, 1], [1, 0], [1, 1], [2, 0]  // 5 connected symbols
      ],
      size: 5,
      payout: 10  // Based on cluster size
    },
    {
      clusterId: "cluster_2",
      symbolId: "low_2",
      positions: [[3, 2], [3, 3], [4, 2], [4, 3], [5, 2], [5, 3]],
      size: 6,
      payout: 8
    }
  ],
  totalWin: 18
}

// Event 3: Cascade (if enabled)
{
  index: 2,
  type: "cascade",
  removePositions: [...],  // All cluster positions
  newSymbols: [...],
}
```

**Math Requirements:**
- ✅ Minimum 5 connected symbols = win
- ✅ Connections: horizontal or vertical (not diagonal)
- ✅ Larger clusters = bigger payouts
- ✅ Multiple clusters can win simultaneously
- ✅ Usually combined with cascading reels

**Configuration to Check:**

```typescript
features: {
  clusterPays: true,
  cascadingReels: true,  // Usually together
},
clusterPayConfig: {
  minClusterSize: 5,
  clusterPaytable: {
    high_1: {
      5: 10, 6: 15, 7: 20, 8: 30, 9: 50,
      10: 75, 11: 100, 12: 150, // ... up to 49 (full grid)
    }
  },
  adjacencyRule: 'orthogonal'  // horizontal/vertical only
}
```

---

### 6. Free Spins

**What Backend Needs to Send:**

```typescript
// Base game: Trigger free spins
{
  index: 0,
  type: "reveal",
  outcome: [...],  // 3+ scatter symbols
}

{
  index: 1,
  type: "evaluateWin",
  wins: [...],  // Scatter wins
  totalWin: 10
}

{
  index: 2,
  type: "triggerBonus",
  bonusType: "free_spins",
  triggeredBy: ["scatter", "scatter", "scatter"],
  spinsAwarded: 10,
  bonusConfig: {
    enhancedFeatures: true,  // e.g., more wilds
    multiplier: 1
  }
}

// During free spins: Regular reveals
{
  index: 0,
  type: "reveal",
  outcome: [...],
  freeSpinNumber: 1,
  freeSpinsRemaining: 9
}

// Retrigger during free spins
{
  index: 2,
  type: "retriggerBonus",
  additionalSpins: 10,
  newTotal: 19
}

// End of free spins
{
  index: 50,
  type: "bonusEnd",
  bonusType: "free_spins",
  totalBonusWin: 500,
  spinsPlayed: 20
}
```

**Math Requirements:**
- ✅ 3/4/5 scatters trigger 10/20/30 free spins
- ✅ Use enhanced reel strips during free spins (more wilds/high symbols)
- ✅ Allow retriggers (3+ scatters during free spins add more spins)
- ✅ Return to base game when spins exhausted

**Configuration to Check:**

```typescript
features: {
  freeSpins: true,
},
freeSpinsConfig: {
  trigger: {
    symbol: 'scatter',
    minCount: 3,
  },
  awards: {
    3: 10,
    4: 20,
    5: 30,
  },
  canRetrigger: true,
  maxTotalSpins: 300,  // Safety limit
}
```

---

## Math Model Requirements

### 1. RTP (Return to Player)

**What the Backend Must Do:**

```typescript
// Example: 96.2% RTP target
const config = {
  rtp: 0.962,  // From config.ts
};

// Your math model must ensure:
// Total wins / Total bets = 0.962 (over millions of spins)
```

**RTP Breakdown Example:**

```
Base Game RTP:     84.5%
Free Spins RTP:    11.0%
Special Features:   0.7%
----------------------
Total RTP:         96.2%
```

### 2. Volatility

**From config.ts:**

```typescript
volatility: 'High'  // Low, Medium-Low, Medium, Medium-High, High, Very High
```

**What This Means:**

| Volatility | Hit Frequency | Max Win | Typical Payout Pattern |
|------------|---------------|---------|------------------------|
| **Low** | 30-40% | 500-1000× | Frequent small wins |
| **Medium** | 20-30% | 1000-5000× | Balanced wins |
| **High** | 15-25% | 5000-20000× | Rare big wins |
| **Very High** | 10-20% | 20000-50000× | Very rare massive wins |

### 3. Max Win

**From config.ts:**

```typescript
max_win: 10000  // Maximum win = 10,000× bet
```

**Backend Requirements:**
- ✅ Cap wins at this value
- ✅ If a spin would win more, cap it at max_win
- ✅ Display capped amount to player

### 4. Symbol Distribution

**Reel Strips Example:**

```typescript
// Backend reel strips must match paytable values
const reelStrips = {
  base: [
    // Reel 1: More low symbols, fewer high symbols
    ['low_1', 'low_2', 'low_3', 'low_4', 'low_5', 
     'mid_1', 'mid_2', 'high_1', 'wild', 'scatter', ...],
    
    // Reel 5: Fewer high symbols (harder to complete lines)
    ['low_1', 'low_2', 'low_3', 'low_4', 'low_5',
     'mid_1', 'high_1', 'wild', 'scatter', ...],
  ],
  
  freeSpins: [
    // Enhanced strips: More wilds and high symbols
    ['wild', 'high_1', 'high_2', 'mid_1', 'mid_2',
     'low_1', 'wild', 'scatter', ...],
  ]
};
```

**Requirements:**
- ✅ Symbol frequencies must match your certified math
- ✅ Use symbol IDs from config.ts
- ✅ Wild symbols must be on strips
- ✅ Scatter symbols must be on strips (for free spins)

---

## Testing & Validation

### Frontend Validation Tool

Run the frontend validator to check config files:

```bash
cd apps/game-template
pnpm run validate --filter=game-template
```

This checks:
- ✅ Config file syntax
- ✅ Symbol ID consistency
- ✅ Feature compatibility
- ✅ RTP values
- ✅ Grid configuration

### Backend Testing Checklist

**Before Integration:**

- [ ] RTP verified (millions of spins)
- [ ] Max win tested and capped correctly
- [ ] All symbol IDs match config.ts
- [ ] Paytable values match exactly
- [ ] Feature book events follow correct format
- [ ] Grid size matches (numReels × numRows)
- [ ] Wilds substitute correctly
- [ ] Scatters don't substitute

**Feature-Specific:**

- [ ] **Expanding Wilds**: Wilds expand to fill reels, wins recalculated
- [ ] **Cascading Reels**: Cascades continue until no wins, multipliers increase
- [ ] **Hold & Spin**: Respins reset on new coin, jackpots awarded correctly
- [ ] **Cluster Pays**: Minimum 5 connected, adjacency rules correct
- [ ] **Free Spins**: Trigger correctly, retriggers work, totals accumulate

### Test Books

Create test books for the frontend team:

```typescript
// test-books/expanding-wilds-big-win.json
{
  "bookId": "test_expanding_wild_1",
  "events": [
    {
      "index": 0,
      "type": "reveal",
      "outcome": [
        ["high_1", "wild", "high_1", "low_3"],
        ["high_1", "wild", "high_1", "low_2"],
        ["high_1", "wild", "high_1", "low_1"],
        ["high_1", "wild", "high_1", "low_4"],
        ["high_1", "wild", "high_1", "low_5"]
      ]
    },
    {
      "index": 1,
      "type": "expandWild",
      "reels": [1, 3],
      "multipliers": [5, 5]
    },
    {
      "index": 2,
      "type": "evaluateWin",
      "wins": [
        {
          "winId": "win_1",
          "symbolId": "high_1",
          "positions": [[0,0], [1,0], [2,0], [3,0], [4,0]],
          "count": 5,
          "multiplier": 25,  // 5 × 5 from two wilds
          "payout": 2500
        }
      ],
      "totalWin": 2500
    }
  ]
}
```

---

## API Reference

### Endpoint: Spin

```typescript
POST /api/spin

Request:
{
  gameId: string;           // e.g., "0_0_kaiju_clash"
  betAmount: number;        // e.g., 1.00
  betMode: string;          // "base" | "bonus_hunt" | "bonus_buy"
  sessionId: string;
}

Response:
{
  bookId: string;
  timestamp: number;
  balanceBefore: number;
  balanceAfter: number;
  totalWin: number;
  events: BookEvent[];
}
```

### Book Event Types

**All Games:**

```typescript
type BookEventReveal = {
  index: number;
  type: 'reveal';
  outcome: string[][];         // [reel][row] symbol IDs
  stopPositions?: number[];    // Reel stop positions
};

type BookEventEvaluateWin = {
  index: number;
  type: 'evaluateWin';
  wins: Win[];
  totalWin: number;
  multiplier?: number;
};

type Win = {
  winId: string;
  symbolId: string;
  paylineId?: string;          // For payline games
  positions: [number, number][]; // [reel, row] positions
  count: number;
  multiplier: number;
  payout: number;
};
```

**Expanding Wilds:**

```typescript
type BookEventExpandWild = {
  index: number;
  type: 'expandWild';
  reels: number[];             // Which reels expand
  multipliers?: number[];      // Multiplier per reel
  expandToPositions?: [number, number][]; // Exact positions
};
```

**Cascading Reels:**

```typescript
type BookEventCascade = {
  index: number;
  type: 'cascade';
  removePositions: [number, number][]; // Positions to remove
  newSymbols: Array<{
    position: [number, number];
    symbol: string;
  }>;
  cascadeNumber: number;
  nextMultiplier: number;
};
```

**Hold & Spin:**

```typescript
type BookEventTriggerHoldAndSpin = {
  index: number;
  type: 'triggerHoldAndSpin';
  triggeredBy: string[];
  initialSpins: number;
  initialCoins: Array<{
    position: [number, number];
    value: number;
  }>;
};

type BookEventHoldAndSpinRespin = {
  index: number;
  type: 'holdAndSpinRespin';
  spinsRemaining: number;
  newCoins: Array<{
    position: [number, number];
    value: number;
  }>;
  resetCounter: boolean;
};

type BookEventHoldAndSpinEnd = {
  index: number;
  type: 'holdAndSpinEnd';
  totalCoinValue: number;
  jackpots: Array<{
    type: 'mini' | 'minor' | 'major' | 'grand';
    value: number;
  }>;
  totalWin: number;
};
```

**Free Spins:**

```typescript
type BookEventTriggerBonus = {
  index: number;
  type: 'triggerBonus';
  bonusType: 'free_spins';
  triggeredBy: string[];
  spinsAwarded: number;
  bonusConfig?: {
    enhancedFeatures?: boolean;
    multiplier?: number;
  };
};

type BookEventRetriggerBonus = {
  index: number;
  type: 'retriggerBonus';
  additionalSpins: number;
  newTotal: number;
};

type BookEventBonusEnd = {
  index: number;
  type: 'bonusEnd';
  bonusType: string;
  totalBonusWin: number;
  spinsPlayed: number;
};
```

---

## Integration Workflow

### Step 1: Backend Team Receives Game Config

```bash
# Frontend provides these files:
apps/game-template/src/game/config.ts
apps/game-template/src/game/theme.json
apps/game-template/src/game/constants.ts
apps/game-template/docs/guides/GAME_TYPES.md  # For feature details
```

### Step 2: Backend Builds Math Model

```
1. Read config.ts for:
   - RTP target
   - Volatility
   - Grid size
   - Enabled features
   - Paytable values

2. Design reel strips that achieve RTP

3. Implement win evaluation logic

4. Implement feature logic (expanding wilds, cascades, etc.)

5. Create book event generators
```

### Step 3: Backend Creates Test Books

```bash
# Create JSON test files
test-books/
├── base-game-win.json
├── expanding-wild-big-win.json
├── free-spins-trigger.json
├── cascade-sequence.json
└── max-win.json
```

### Step 4: Frontend Team Tests with Test Books

```bash
# Frontend loads test books in Storybook
cd apps/game-template
pnpm run storybook --filter=game-template

# Test each book event type
```

### Step 5: Integration Testing

```
1. Backend exposes API endpoint
2. Frontend connects to backend
3. Test real spins
4. Verify:
   - Book events play correctly
   - Wins display accurately
   - Features trigger properly
   - Balance updates correctly
```

### Step 6: Certification

```
1. Backend provides certified math report
2. Frontend validates config matches math
3. Run regression tests
4. Submit for approval
```

---

## Quick Reference

### Backend Checklist

**For Every Game:**
- [ ] Game ID matches config.ts
- [ ] RTP matches config.ts
- [ ] Symbol IDs match theme.json
- [ ] Paytable values match config.ts exactly
- [ ] Grid size matches (numReels × numRows)
- [ ] Book events follow TypeScript types
- [ ] Max win is capped correctly

**For Specific Features:**
- [ ] **Expanding Wilds**: Send `expandWild` event before `evaluateWin`
- [ ] **Cascading Reels**: Send multiple `cascade` events until no wins
- [ ] **Hold & Spin**: Send respin events sequentially, reset counter on new coin
- [ ] **Cluster Pays**: Calculate clusters with correct adjacency rules
- [ ] **Free Spins**: Send `triggerBonus`, then separate book per free spin

### Common Mistakes to Avoid

❌ **Don't:**
- Use symbol IDs not defined in config
- Send book events out of order
- Forget to apply multipliers to wins
- Cap wins incorrectly
- Use wrong paytable values
- Forget about wild substitution rules

✅ **Do:**
- Validate symbol IDs against config
- Send events in sequential order (index: 0, 1, 2...)
- Apply all multipliers correctly
- Test max win scenarios
- Use exact paytable from config.ts
- Implement wild substitution (except for scatters)

---

## Support & Questions

### Documentation References

- **Frontend Config**: `apps/game-template/src/game/config.ts`
- **Game Types Guide**: `apps/game-template/docs/guides/GAME_TYPES.md`
- **Template Spec**: `apps/game-template/docs/TEMPLATE_SPEC.md`
- **Customization Guide**: `apps/game-template/docs/CUSTOMIZATION_GUIDE.md`

### Contact

For questions about:
- **Book event format**: See GAME_TYPES.md for your specific game type
- **Config structure**: See TEMPLATE_SPEC.md
- **Feature behavior**: See GAME_TYPES.md feature sections
- **Integration issues**: Run `pnpm run validate` on frontend

---

## Example: Complete Backend Implementation

See `docs/guides/examples/backend-example.ts` for a complete example backend implementation (pseudocode).

---

**Ready to integrate?** Start by reading the game's `config.ts` file and checking `GAME_TYPES.md` for the specific feature implementations needed. 🚀

