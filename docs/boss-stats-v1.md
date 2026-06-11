# Boss Stats v1

## Overview

v3.2.2 introduces boss-specific base stats. Difficulty is applied mainly as an HP multiplier, while defense, attack power, break gauge, and down duration are taken from each boss definition.

The combat damage formula and `DAMAGE_CONSTANT = 30` are unchanged.

## Difficulty HP Multipliers

- Normal: 1.0
- Hard: 2.2
- Extreme: 4.0

Final HP is calculated as:

```ts
finalHp = Math.round(bossBaseNormalHp * difficultyHpMultiplier)
```

## Boss Roles

### Tutorial Boss

- Role: `tutorial`
- Reward tier: `tutorial`
- Normal HP: 1500
- Defense: 2
- Break gauge: 70
- Down duration: 6.5s
- Attacks: frontal 8 / charge 14 / area 12

This boss is intentionally weaker so early mobile controls and battle flow can be learned with initial equipment.

### Standard Boss

- Role: `standard`
- Reward tier: `standard`
- Normal HP: 3000
- Defense: 5
- Break gauge: 100
- Down duration: 6.0s
- Attacks: frontal 15 / charge 25 / area 20

This boss is the current baseline for balance checks.

### Advanced Boss

- Role: `advanced`
- Reward tier: `advanced`
- Normal HP: 4200
- Defense: 8
- Break gauge: 130
- Down duration: 5.5s
- Attacks: frontal 18 / charge 30 / area 24

This boss is slightly stronger even on Normal and is intended for players who are used to the controls.

## Reward Tier

Each boss has a `rewardTier` field. In v3.2.3 this field is used by reward calculation:

- `tutorial`: lower rewards for weaker tutorial farming.
- `standard`: baseline rewards, matching the previous Normal reward range.
- `advanced`: slightly higher rewards for stronger bosses.

Detailed multipliers are documented in `docs/reward-tier-v1.md`.
