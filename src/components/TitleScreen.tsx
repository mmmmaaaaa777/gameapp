interface TitleScreenProps {
  onStart: () => void;
}

export function TitleScreen({ onStart }: TitleScreenProps) {
  return (
    <main className="screen title-screen">
      <section className="title-panel" aria-labelledby="app-title">
        <p className="eyebrow">Three.js 操作感デモ</p>
        <h1 id="app-title">gameapp Three.jsデモ版</h1>
        <p className="subtitle">Unity本番前の操作感・雰囲気確認用デモ</p>
        <button className="primary-button start-button" type="button" onClick={onStart}>
          START
        </button>
      </section>

      <section className="control-guide" aria-label="操作説明">
        <h2>操作説明</h2>
        <dl>
          <div>
            <dt>スワイプ</dt>
            <dd>移動</dd>
          </div>
          <div>
            <dt>タップ</dt>
            <dd>攻撃</dd>
          </div>
          <div>
            <dt>フリック</dt>
            <dd>回避</dd>
          </div>
          <div>
            <dt>スキルボタン</dt>
            <dd>スキル発動</dd>
          </div>
          <div>
            <dt>属性ボタン</dt>
            <dd>攻撃エフェクト属性の切り替え</dd>
          </div>
        </dl>
      </section>
    </main>
  );
}
