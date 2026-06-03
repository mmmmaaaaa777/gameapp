import { useState } from "react";
import { BattleScreen } from "./components/BattleScreen";
import { ResultScreen } from "./components/ResultScreen";
import { TitleScreen } from "./components/TitleScreen";
import type { AppScreen, BattleResult } from "./types/game";

export default function App() {
  const [screen, setScreen] = useState<AppScreen>("title");
  const [result, setResult] = useState<BattleResult | null>(null);
  const [runId, setRunId] = useState(0);

  const startBattle = () => {
    setResult(null);
    setRunId((current) => current + 1);
    setScreen("battle");
  };

  if (screen === "battle") {
    return (
      <BattleScreen
        key={runId}
        onComplete={(nextResult) => {
          setResult(nextResult);
          setScreen("result");
        }}
      />
    );
  }

  if (screen === "result" && result) {
    return (
      <ResultScreen
        result={result}
        onRetry={startBattle}
        onBackToTitle={() => setScreen("title")}
      />
    );
  }

  return <TitleScreen onStart={startBattle} />;
}
