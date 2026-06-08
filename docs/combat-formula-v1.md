# combat formula v1

## 採用したダメージ計算式

v3.1.2では、通常攻撃、スキル攻撃、ボス攻撃の最終ダメージを以下の共通式で計算する。

```ts
const DAMAGE_CONSTANT = 30;
const effectiveDefense = Math.max(0, defense);

const damageRaw =
  (1 + attackPower * DAMAGE_CONSTANT / (DAMAGE_CONSTANT + effectiveDefense))
  * elementMultiplier
  * criticalMultiplier
  * skillDamageMultiplier
  * downMultiplier
  * damageTakenMultiplier;

const damage = Math.max(1, Math.floor(damageRaw + 0.5));
```

## 丸めルール

- `DAMAGE_CONSTANT` は `30` 固定。
- 防御力は `Math.max(0, defense)` で0未満にならないようにする。
- 最終ダメージは `Math.floor(damageRaw + 0.5)` で四捨五入する。
- 最低ダメージは `1`。

## プレイヤー基準ステータス

- 基礎攻撃力: `10`
- 基礎防御力: `5`
- 基礎HP: `100`
- クリティカル率: `5%`
- クリティカル倍率: `1.5`

既存装備の効果は維持し、攻撃力、最大HP、移動速度へ加算または倍率反映する。

## ボス防御力

v3.1.2時点では全難易度でボス防御力を `5` とする。将来調整しやすいように、難易度別設定として `src/game/difficulty.ts` に分離した。

## 難易度別HP

`src/game/difficulty.ts` の `BOSS_DIFFICULTY_STATS` を参照する。

- Normal: HP `3000` / 防御力 `5`
- Hard: HP `6500` / 防御力 `5`
- Extreme: HP `12000` / 防御力 `5`

## 属性相性仕様

既存仕様の確認対象:

- `src/types/game.ts`
- `src/game` 配下
- `src/components` 配下
- `src/three` 配下の属性エフェクト定義
- `docs` 配下
- `README.md`
- `tests` 配下

確認した範囲では、属性ID、表示名、属性エフェクト、ボス属性は存在するが、属性相性表、有利/不利関係、属性倍率の既存仕様は見つからなかった。

そのため、v3.1.2では属性相性テーブルを新規作成せず、`elementMultiplier = 1.0` の等倍固定で計算する。ダメージ計算関数自体は `elementMultiplier` を引数として受け取るため、既存仕様が決まり次第、呼び出し側から倍率を渡せる。

## クリティカル

プレイヤー攻撃のみ、攻撃ごとにクリティカル率 `5%` で判定する。発生時は `criticalMultiplier = 1.5`、通常時は `1.0`。

ボス攻撃はv3.1.2時点ではクリティカルなしとし、`criticalMultiplier = 1.0` を使う。

## 既存補正の扱い

既存スキルのダメージ値は、基礎通常攻撃力 `10` に対する倍率として扱う。

- 通常攻撃: `skillDamageMultiplier = 1.0`
- クイックスラッシュ: `20 / 10 = 2.0`
- 属性バースト: `35 / 10 = 3.5`
- ブレイクアーツ: `60 / 10 = 6.0`

ボスダウン補正や被ダメージ倍率は、現時点で既存仕様がないため `1.0` のままとする。
