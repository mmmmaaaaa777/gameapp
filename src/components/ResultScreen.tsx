import { MATERIAL_IDS, MATERIAL_LABELS } from "../game/inventory";
import type { BattleBalanceSummary } from "../game/balance";
import { DIFFICULTY_LABELS, getDifficultyLabel, type BossDifficulty } from "../game/menu";
import type { BattleResult, BattleReward, PlayerInventory } from "../types/game";

interface ResultScreenProps {
  balance: BattleBalanceSummary;
  bossName?: string;
  difficulty?: BossDifficulty;
  inventory: PlayerInventory;
  result: BattleResult;
  reward: BattleReward;
  onRetry: () => void;
  onEquipment: () => void;
  onHome: () => void;
}

function getWeaponLevelText(balance: BattleBalanceSummary): string {
  return balance.weaponLevel ? `Lv${balance.weaponLevel}` : "-";
}

function ResultBalancePanel({
  balance,
  result,
}: {
  balance: BattleBalanceSummary;
  result: BattleResult;
}) {
  const rows = [
    ["難易度", getDifficultyLabel(balance.difficulty)],
    ["ボス名", balance.bossName],
    ["ボス役割", balance.bossRoleLabel],
    ["報酬ランク", balance.rewardTier],
    ["難易度倍率", `${getDifficultyLabel(balance.difficulty)} x${balance.difficultyRewardMultiplier.toFixed(1)}`],
    ["ボスHP", balance.bossHp.toLocaleString("ja-JP")],
    ["ボス防御", balance.bossDefense.toLocaleString("ja-JP")],
    ["装備中武器", balance.equippedWeaponName],
    ["武器Lv", getWeaponLevelText(balance)],
    ["攻撃属性", balance.attackAttributeLabel],
    ["防御属性", balance.defenseAttributeLabel],
    ["ボス属性", balance.bossAttributeLabel],
    ["ブレイク", balance.bossBreakGauge.toLocaleString("ja-JP")],
    ["ダウン", `${balance.bossDownDurationSeconds.toFixed(1)}秒`],
    ["前方攻撃", balance.bossFrontalAttackPower.toLocaleString("ja-JP")],
    ["突進", balance.bossChargeAttackPower.toLocaleString("ja-JP")],
    ["範囲攻撃", balance.bossAreaAttackPower.toLocaleString("ja-JP")],
    ["攻撃相性", balance.attackRelationLabel],
    ["被弾相性", balance.defenseRelationLabel],
    ["時間", `${result.stats.elapsedSeconds.toFixed(1)}秒`],
    ["与ダメージ", result.stats.dealtDamage.toLocaleString("ja-JP")],
    ["被ダメージ", result.stats.takenDamage.toLocaleString("ja-JP")],
    ["回避成功", result.stats.dodgeSuccessCount.toLocaleString("ja-JP")],
    ["ブレイク", result.stats.breakCount.toLocaleString("ja-JP")],
    ["通常攻撃目安", `${balance.normalAttackDamage.toLocaleString("ja-JP")} ダメージ`],
  ];

  return (
    <details className="balance-panel result-balance-panel">
      <summary className="balance-heading" aria-label="バランス確認を開閉">
        <span>BALANCE</span>
        <strong>戦闘条件と結果</strong>
      </summary>
      <dl className="balance-grid result-balance-grid">
        {rows.map(([label, value]) => (
          <div key={label}>
            <dt>{label}</dt>
            <dd>{value}</dd>
          </div>
        ))}
      </dl>
    </details>
  );
}

export function ResultScreen({
  balance,
  bossName,
  difficulty,
  inventory,
  result,
  reward,
  onRetry,
  onEquipment,
  onHome,
}: ResultScreenProps) {
  const isClear = result.kind === "CLEAR";
  const gainedMaterials = MATERIAL_IDS.filter((materialId) => reward.materials[materialId] > 0);

  return (
    <main className={`screen result-screen ${isClear ? "clear" : "failed"}`}>
      <section className="result-panel" aria-labelledby="result-title">
        <p className="eyebrow">{result.kind}</p>
        <h1 id="result-title">{isClear ? "討伐完了" : "戦闘失敗"}</h1>
        {bossName ? <p className="result-boss-name">対象: {bossName}</p> : null}
        {difficulty ? (
          <p className="result-boss-name">難易度: {DIFFICULTY_LABELS[difficulty]}</p>
        ) : null}

        <dl className="result-stats">
          <div>
            <dt>{isClear ? "クリア時間" : "生存時間"}</dt>
            <dd>{result.stats.elapsedSeconds.toFixed(1)}秒</dd>
          </div>
          <div>
            <dt>与ダメージ</dt>
            <dd>{result.stats.dealtDamage.toLocaleString("ja-JP")}</dd>
          </div>
          <div>
            <dt>被ダメージ</dt>
            <dd>{result.stats.takenDamage.toLocaleString("ja-JP")}</dd>
          </div>
          <div>
            <dt>回避成功</dt>
            <dd>{result.stats.dodgeSuccessCount.toLocaleString("ja-JP")}</dd>
          </div>
          <div>
            <dt>ブレイク</dt>
            <dd>{result.stats.breakCount.toLocaleString("ja-JP")}</dd>
          </div>
        </dl>

        <ResultBalancePanel balance={balance} result={result} />

        <div className="result-equipment-cta">
          <button
            className="secondary-button result-equipment-button"
            type="button"
            onClick={onEquipment}
          >
            装備を確認
          </button>
        </div>

        <section className="reward-panel" aria-label="今回獲得した報酬">
          <div className="reward-heading">
            <span>GET</span>
            <strong>コイン +{reward.coin.toLocaleString("ja-JP")}</strong>
          </div>
          <ul className="reward-list">
            {gainedMaterials.length > 0 ? (
              gainedMaterials.map((materialId) => (
                <li key={materialId}>
                  <span>{MATERIAL_LABELS[materialId]}</span>
                  <strong>+{reward.materials[materialId]}</strong>
                </li>
              ))
            ) : (
              <li>
                <span>素材</span>
                <strong>なし</strong>
              </li>
            )}
          </ul>
        </section>

        <section className="reward-panel inventory-panel" aria-label="現在の所持素材">
          <div className="reward-heading">
            <span>STOCK</span>
            <strong>所持コイン {inventory.coin.toLocaleString("ja-JP")}</strong>
          </div>
          <ul className="reward-list compact">
            {MATERIAL_IDS.map((materialId) => (
              <li key={materialId}>
                <span>{MATERIAL_LABELS[materialId]}</span>
                <strong>{inventory[materialId].toLocaleString("ja-JP")}</strong>
              </li>
            ))}
          </ul>
        </section>

        <div className="result-actions">
          <button className="primary-button" type="button" onClick={onRetry}>
            もう一度出撃
          </button>
          <button className="secondary-button" type="button" onClick={onHome}>
            ホームへ戻る
          </button>
        </div>
      </section>
    </main>
  );
}
