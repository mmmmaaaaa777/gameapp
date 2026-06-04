import type { BattleResult } from "../types/game";

interface ResultScreenProps {
  bossName?: string;
  result: BattleResult;
  onRetry: () => void;
  onHome: () => void;
}

export function ResultScreen({ bossName, result, onRetry, onHome }: ResultScreenProps) {
  const isClear = result.kind === "CLEAR";

  return (
    <main className={`screen result-screen ${isClear ? "clear" : "failed"}`}>
      <section className="result-panel" aria-labelledby="result-title">
        <p className="eyebrow">{isClear ? "討伐完了" : "戦闘不能"}</p>
        <h1 id="result-title">{result.kind}</h1>
        {bossName ? <p className="result-boss-name">対象: {bossName}</p> : null}

        <dl className="result-stats">
          <div>
            <dt>討伐時間</dt>
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
        </dl>

        <div className="result-actions">
          <button className="primary-button" type="button" onClick={onRetry}>
            同じボスに再挑戦
          </button>
          <button className="secondary-button" type="button" onClick={onHome}>
            ホームへ戻る
          </button>
        </div>
      </section>
    </main>
  );
}
