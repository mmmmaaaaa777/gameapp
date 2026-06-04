import { useState } from "react";
import { BattleScreen } from "./components/BattleScreen";
import {
  BossSelectScreen,
  EquipmentScreen,
  FormationScreen,
  HomeScreen,
  SettingsScreen,
  SortiePrepScreen,
} from "./components/MenuScreens";
import { ResultScreen } from "./components/ResultScreen";
import { BOSS_OPTIONS, MAIN_SKILLS, type BossDifficulty } from "./game/menu";
import type { AppScreen, BattleResult } from "./types/game";

export default function App() {
  const [screen, setScreen] = useState<AppScreen>("home");
  const [result, setResult] = useState<BattleResult | null>(null);
  const [selectedBoss, setSelectedBoss] = useState(BOSS_OPTIONS[0]);
  const [difficulty, setDifficulty] = useState<BossDifficulty>("Normal");
  const [mainSkill, setMainSkill] = useState(MAIN_SKILLS[0]);
  const [runId, setRunId] = useState(0);
  const bossSelection = {
    boss: selectedBoss,
    difficulty,
  };

  const startBattle = () => {
    setResult(null);
    setRunId((current) => current + 1);
    setScreen("battle");
  };

  const goHome = () => {
    setScreen("home");
  };

  if (screen === "home") {
    return (
      <HomeScreen
        mainSkill={mainSkill}
        onChallenge={() => setScreen("bossSelect")}
        onNavigate={(nextScreen) => setScreen(nextScreen)}
      />
    );
  }

  if (screen === "bossSelect") {
    return (
      <BossSelectScreen
        selection={bossSelection}
        onSelectBoss={setSelectedBoss}
        onSelectDifficulty={setDifficulty}
        onHome={goHome}
        onPrep={() => setScreen("sortiePrep")}
      />
    );
  }

  if (screen === "sortiePrep") {
    return (
      <SortiePrepScreen
        mainSkill={mainSkill}
        selection={bossSelection}
        onBack={() => setScreen("bossSelect")}
        onStart={startBattle}
      />
    );
  }

  if (screen === "formation") {
    return (
      <FormationScreen
        mainSkill={mainSkill}
        onSave={setMainSkill}
        onHome={goHome}
      />
    );
  }

  if (screen === "equipment") {
    return <EquipmentScreen onHome={goHome} />;
  }

  if (screen === "settings") {
    return <SettingsScreen onHome={goHome} />;
  }

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
        bossName={selectedBoss.name}
        result={result}
        onRetry={startBattle}
        onHome={goHome}
      />
    );
  }

  return null;
}
