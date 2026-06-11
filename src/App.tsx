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
import {
  calculateEquipmentBonus,
  canCraftEquipment,
  consumeEquipmentCost,
  createEmptyEquippedEquipment,
  createEmptyEquipmentLevels,
  createEmptyOwnedEquipment,
  equipEquipment,
  EQUIPMENT_BY_ID,
  loadEquippedEquipment,
  loadEquipmentLevels,
  loadOwnedEquipment,
  getCraftableEquipmentIds,
  getRebirthableWeaponIds,
  getUpgradeableEquipmentIds,
  rebirthWeapon as applyRebirthWeapon,
  saveEquippedEquipment,
  saveEquipmentLevels,
  saveOwnedEquipment,
  upgradeEquipment as applyUpgradeEquipment,
} from "./game/equipment";
import { createBattleBalanceSummary, type BattleBalanceSummary } from "./game/balance";
import { createRetryBattleSelection } from "./game/difficulty";
import {
  addRewardToInventory,
  addDemoMaterialsToInventory,
  createEmptyInventory,
  loadPlayerInventory,
  savePlayerInventory,
} from "./game/inventory";
import { BOSS_OPTIONS, MAIN_SKILLS, type BossDifficulty } from "./game/menu";
import { generateBattleReward } from "./game/rewards";
import type { AppScreen, BattleResult, BattleReward, EquipmentId } from "./types/game";
import type { WeaponId } from "./game/equipment";

interface RewardedBattleResult {
  balance: BattleBalanceSummary;
  battle: BattleResult;
  reward: BattleReward;
}

export default function App() {
  const [screen, setScreen] = useState<AppScreen>("home");
  const [result, setResult] = useState<RewardedBattleResult | null>(null);
  const [inventory, setInventory] = useState(loadPlayerInventory);
  const [ownedEquipment, setOwnedEquipment] = useState(loadOwnedEquipment);
  const [equippedEquipment, setEquippedEquipment] = useState(loadEquippedEquipment);
  const [equipmentLevels, setEquipmentLevels] = useState(loadEquipmentLevels);
  const [selectedBoss, setSelectedBoss] = useState(BOSS_OPTIONS[0]);
  const [difficulty, setDifficulty] = useState<BossDifficulty>("Normal");
  const [mainSkill, setMainSkill] = useState(MAIN_SKILLS[0]);
  const [runId, setRunId] = useState(0);
  const bossSelection = {
    boss: selectedBoss,
    difficulty,
  };
  const craftableEquipmentCount = getCraftableEquipmentIds(inventory, ownedEquipment).length;
  const rebirthableWeaponCount = getRebirthableWeaponIds(inventory, ownedEquipment).length;
  const upgradeableEquipmentCount = getUpgradeableEquipmentIds(
    inventory,
    ownedEquipment,
    equipmentLevels,
  ).length;
  const equipmentNoticeCount = craftableEquipmentCount + rebirthableWeaponCount + upgradeableEquipmentCount;
  const equipmentBonus = calculateEquipmentBonus(equippedEquipment, equipmentLevels);

  const startBattle = () => {
    setResult(null);
    setRunId((current) => current + 1);
    setScreen("battle");
  };

  const retryBattle = () => {
    const retrySelection = createRetryBattleSelection(bossSelection);
    setSelectedBoss(retrySelection.boss);
    setDifficulty(retrySelection.difficulty);
    startBattle();
  };

  const goHome = () => {
    setScreen("home");
  };

  const resetInventory = () => {
    const emptyInventory = createEmptyInventory();
    const emptyOwnedEquipment = createEmptyOwnedEquipment();
    const emptyEquippedEquipment = createEmptyEquippedEquipment();
    const emptyEquipmentLevels = createEmptyEquipmentLevels();
    savePlayerInventory(emptyInventory);
    saveOwnedEquipment(emptyOwnedEquipment);
    saveEquippedEquipment(emptyEquippedEquipment);
    saveEquipmentLevels(emptyEquipmentLevels);
    setInventory(emptyInventory);
    setOwnedEquipment(emptyOwnedEquipment);
    setEquippedEquipment(emptyEquippedEquipment);
    setEquipmentLevels(emptyEquipmentLevels);
  };

  const grantDemoMaterials = () => {
    const nextInventory = addDemoMaterialsToInventory(inventory);
    savePlayerInventory(nextInventory);
    setInventory(nextInventory);
  };

  const craftEquipment = (equipmentId: EquipmentId): boolean => {
    const equipment = EQUIPMENT_BY_ID[equipmentId];

    if (ownedEquipment[equipmentId] || !canCraftEquipment(inventory, equipment)) {
      return false;
    }

    const nextInventory = consumeEquipmentCost(inventory, equipment);
    const nextOwnedEquipment = {
      ...ownedEquipment,
      [equipmentId]: true,
    };
    const nextEquipmentLevels = {
      ...equipmentLevels,
      [equipmentId]: 1,
    };

    savePlayerInventory(nextInventory);
    saveOwnedEquipment(nextOwnedEquipment);
    saveEquipmentLevels(nextEquipmentLevels);
    setInventory(nextInventory);
    setOwnedEquipment(nextOwnedEquipment);
    setEquipmentLevels(nextEquipmentLevels);

    return true;
  };

  const equipOwnedEquipment = (equipmentId: EquipmentId): boolean => {
    if (!ownedEquipment[equipmentId]) {
      return false;
    }

    const nextEquippedEquipment = equipEquipment(equippedEquipment, equipmentId);
    saveEquippedEquipment(nextEquippedEquipment);
    setEquippedEquipment(nextEquippedEquipment);

    return true;
  };

  const rebirthWeapon = (equipmentId: WeaponId): boolean => {
    const result = applyRebirthWeapon(inventory, ownedEquipment, equipmentLevels, equipmentId);

    if (!result.result.success || !result.result.nextWeaponId) {
      return false;
    }

    const nextInventory = result.inventory;
    const nextOwnedEquipment = result.ownedEquipment;
    const nextEquipmentLevels = result.equipmentLevels;
    const nextEquippedEquipment = {
      ...equippedEquipment,
      weapon:
        equippedEquipment.weapon === equipmentId ? result.result.nextWeaponId : equippedEquipment.weapon,
    };

    savePlayerInventory(nextInventory);
    saveOwnedEquipment(nextOwnedEquipment);
    saveEquipmentLevels(nextEquipmentLevels);
    saveEquippedEquipment(nextEquippedEquipment);
    setInventory(nextInventory);
    setOwnedEquipment(nextOwnedEquipment);
    setEquipmentLevels(nextEquipmentLevels);
    setEquippedEquipment(nextEquippedEquipment);

    return true;
  };

  const upgradeEquipment = (equipmentId: EquipmentId): boolean => {
    const result = applyUpgradeEquipment(inventory, ownedEquipment, equipmentLevels, equipmentId);

    if (!result.result.success) {
      return false;
    }

    savePlayerInventory(result.inventory);
    saveEquipmentLevels(result.equipmentLevels);
    setInventory(result.inventory);
    setEquipmentLevels(result.equipmentLevels);

    return true;
  };

  if (screen === "home") {
    return (
      <HomeScreen
        equipmentNoticeCount={equipmentNoticeCount}
        equippedEquipment={equippedEquipment}
        inventory={inventory}
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
        equipmentBonus={equipmentBonus}
        equipmentLevels={equipmentLevels}
        equippedEquipment={equippedEquipment}
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
        equipmentNoticeCount={equipmentNoticeCount}
        mainSkill={mainSkill}
        onSave={setMainSkill}
        onNavigate={(nextScreen) => setScreen(nextScreen)}
      />
    );
  }

  if (screen === "equipment") {
    return (
      <EquipmentScreen
        craftableEquipmentCount={craftableEquipmentCount}
        equipmentLevels={equipmentLevels}
        equipmentNoticeCount={equipmentNoticeCount}
        equippedEquipment={equippedEquipment}
        inventory={inventory}
        ownedEquipment={ownedEquipment}
        rebirthableWeaponCount={rebirthableWeaponCount}
        upgradeableEquipmentCount={upgradeableEquipmentCount}
        onCraftEquipment={craftEquipment}
        onEquipEquipment={equipOwnedEquipment}
        onRebirthWeapon={rebirthWeapon}
        onUpgradeEquipment={upgradeEquipment}
        onNavigate={(nextScreen) => setScreen(nextScreen)}
      />
    );
  }

  if (screen === "settings") {
    return (
      <SettingsScreen
        equipmentLevels={equipmentLevels}
        equipmentNoticeCount={equipmentNoticeCount}
        equippedEquipment={equippedEquipment}
        inventory={inventory}
        ownedEquipment={ownedEquipment}
        onHome={goHome}
        onNavigate={(nextScreen) => setScreen(nextScreen)}
        onGrantDemoMaterials={grantDemoMaterials}
        onResetInventory={resetInventory}
      />
    );
  }

  if (screen === "battle") {
    return (
      <BattleScreen
        equipmentBonus={equipmentBonus}
        key={runId}
        selection={bossSelection}
        equippedWeaponId={equippedEquipment.weapon}
        onComplete={(nextResult) => {
          const reward = generateBattleReward(nextResult.kind, Math.random, {
            difficulty,
            rewardTier: selectedBoss.rewardTier,
          });
          setInventory((currentInventory) => {
            const nextInventory = addRewardToInventory(currentInventory, reward);
            savePlayerInventory(nextInventory);
            return nextInventory;
          });
          setResult({
            balance: createBattleBalanceSummary({
              activeAttribute: nextResult.activeAttribute,
              equipmentBonus,
              equipmentLevels,
              equippedEquipment,
              selection: bossSelection,
            }),
            battle: nextResult,
            reward,
          });
          setScreen("result");
        }}
      />
    );
  }

  if (screen === "result" && result) {
    return (
      <ResultScreen
        bossName={selectedBoss.name}
        balance={result.balance}
        difficulty={difficulty}
        inventory={inventory}
        result={result.battle}
        reward={result.reward}
        onRetry={retryBattle}
        onEquipment={() => setScreen("equipment")}
        onHome={goHome}
      />
    );
  }

  return null;
}
