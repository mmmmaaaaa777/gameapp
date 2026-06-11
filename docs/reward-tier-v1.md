# Reward Tier v1

## Overview

v3.2.3 applies boss `rewardTier` and difficulty to battle rewards.

`standard + Normal` remains the existing baseline. Tutorial bosses give less reward because they are weaker, while advanced bosses give slightly more reward because they are stronger.

## Reward Tier Multipliers

| rewardTier | Coin | Materials |
| --- | ---: | ---: |
| `tutorial` | 0.7 | 0.8 |
| `standard` | 1.0 | 1.0 |
| `advanced` | 1.25 | 1.15 |

## Difficulty Reward Multipliers

| Difficulty | Reward |
| --- | ---: |
| Normal | 1.0 |
| Hard | 1.4 |
| Extreme | 2.0 |

## Formula

```ts
finalCoin = Math.round(baseCoin * rewardTier.coinMultiplier * difficulty.rewardMultiplier)
finalMaterialAmount = Math.round(
  baseMaterialAmount * rewardTier.materialMultiplier * difficulty.rewardMultiplier,
)
```

For CLEAR rewards, material drops that are present before scaling are guaranteed to stay at least 1 after scaling.

FAILED rewards use the same multiplier structure, while preserving the existing small coin reward, random material drop, and low magic shard chance behavior.

## Future

The current implementation only scales existing rewards. Later versions can extend `rewardTier` into boss-specific material tables or unique boss drops without changing localStorage keys.
