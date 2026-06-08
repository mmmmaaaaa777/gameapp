import { MATERIAL_IDS, MATERIAL_LABELS } from "../game/inventory";
import type { BossDifficulty } from "../game/menu";
import type { BattleResult, BattleReward, PlayerInventory } from "../types/game";

interface ResultScreenProps {
  bossName?: string;
  difficulty?: BossDifficulty;
  inventory: PlayerInventory;
  result: BattleResult;
  reward: BattleReward;
  onRetry: () => void;
  onEquipment: () => void;
  onHome: () => void;
}

export function ResultScreen({
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
        <p className="eyebrow">{isClear ? "討伐完了" : "戦闘不能"}</p>
        <h1 id="result-title">{result.kind}</h1>
        {bossName ? <p className="result-boss-name">対象: {bossName}</p> : null}
        {difficulty ? <p className="result-boss-name">難易度: {difficulty}</p> : null}

        <dl className="result-stats">
          <div>
            <dt>{isClear ? "討伐時間" : "生存時間"}</dt>
            <dd>{result.stats.elapsedSeconds.toFixed(1)}秒</dd>
          </div>
          <div>
            <dt>与ダメージ</dt>
            <dd>{result.stats.dealtDamage}</dd>
          </div>
          <div>
            <dt>被ダメージ</dt>
            <dd>{result.stats.takenDamage}</dd>
          </div>
          <div>
            <dt>回避成功</dt>
            <dd>{result.stats.dodgeSuccessCount}</dd>
          </div>
          <div>
            <dt>ブレイク</dt>
            <dd>{result.stats.breakCount}</dd>
          </div>
        </dl>

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
            {gainedMaterials.map((materialId) => (
              <li key={materialId}>
                <span>{MATERIAL_LABELS[materialId]}</span>
                <strong>+{reward.materials[materialId]}</strong>
              </li>
            ))}
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
                <strong>{inventory[materialId]}</strong>
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
