import type { CSSProperties } from "react";
import { useState } from "react";
import { ATTRIBUTE_BY_ID, PLAYER_BASE_ATTACK, PLAYER_MAX_HP } from "../game/constants";
import { getPlayerBattleStats } from "../game/combat";
import { getBossStatsForSelection } from "../game/difficulty";
import {
  canCraftEquipment,
  canRebirthWeapon,
  canUpgradeEquipment,
  EQUIPMENT_BY_ID,
  EQUIPMENT_DEFINITIONS,
  EQUIPMENT_SLOT_LABELS,
  getEquipmentLevel,
  getEquipmentUpgradeCost,
  getNextEquipmentLevel,
  getWeaponRebirthCost,
  getScaledEquipmentEffect,
} from "../game/equipment";
import { MATERIAL_IDS, MATERIAL_LABELS } from "../game/inventory";
import {
  BOSS_OPTIONS,
  DIFFICULTIES,
  MAIN_SKILLS,
  SUB_SKILLS,
  type BossDifficulty,
  type BossOption,
  type BossSelection,
  type MainSkillOption,
} from "../game/menu";
import type {
  AttributeId,
  BattleEquipmentBonus,
  EquipmentDefinition,
  EquipmentId,
  EquipmentLevel,
  EquipmentLevelMap,
  EquipmentSlot,
  EquippedEquipment,
  OwnedEquipment,
  PlayerInventory,
} from "../types/game";
import type { WeaponId } from "../game/equipment";

type NavScreen = "home" | "formation" | "equipment" | "settings";

interface HomeScreenProps {
  equipmentNoticeCount: number;
  equippedEquipment: EquippedEquipment;
  inventory: PlayerInventory;
  mainSkill: MainSkillOption;
  onChallenge: () => void;
  onNavigate: (screen: NavScreen) => void;
}

interface BossSelectScreenProps {
  selection: BossSelection;
  onSelectBoss: (boss: BossOption) => void;
  onSelectDifficulty: (difficulty: BossDifficulty) => void;
  onHome: () => void;
  onPrep: () => void;
}

interface SortiePrepScreenProps {
  equipmentBonus: BattleEquipmentBonus;
  equipmentLevels: EquipmentLevelMap;
  equippedEquipment: EquippedEquipment;
  selection: BossSelection;
  mainSkill: MainSkillOption;
  onBack: () => void;
  onStart: () => void;
}

interface FormationScreenProps {
  equipmentNoticeCount: number;
  mainSkill: MainSkillOption;
  onSave: (skill: MainSkillOption) => void;
  onNavigate: (screen: NavScreen) => void;
}

interface EquipmentScreenProps {
  craftableEquipmentCount: number;
  equipmentLevels: EquipmentLevelMap;
  equipmentNoticeCount: number;
  equippedEquipment: EquippedEquipment;
  inventory: PlayerInventory;
  ownedEquipment: OwnedEquipment;
  upgradeableEquipmentCount: number;
  rebirthableWeaponCount: number;
  onCraftEquipment: (equipmentId: EquipmentId) => boolean;
  onEquipEquipment: (equipmentId: EquipmentId) => boolean;
  onUpgradeEquipment: (equipmentId: EquipmentId) => boolean;
  onRebirthWeapon: (weaponId: WeaponId) => boolean;
  onNavigate: (screen: NavScreen) => void;
}

interface SettingsScreenProps {
  equipmentLevels: EquipmentLevelMap;
  equipmentNoticeCount: number;
  equippedEquipment: EquippedEquipment;
  inventory: PlayerInventory;
  ownedEquipment: OwnedEquipment;
  onHome: () => void;
  onNavigate: (screen: NavScreen) => void;
  onResetInventory: () => void;
}

const NAV_ITEMS = [
  ["home", "ホーム", "⌂"],
  ["formation", "編成", "✦"],
  ["equipment", "装備", "◆"],
  ["settings", "設定", "⚙"],
] as const;

const EQUIPMENT_SLOT_ORDER: EquipmentSlot[] = ["weapon", "head", "body", "feet"];

const INITIAL_EQUIPMENT_LABELS: Record<EquipmentSlot, string> = {
  weapon: "初期武器",
  head: "初期頭防具",
  body: "初期胴体防具",
  feet: "初期足防具",
};

function AttributePill({ attributeId }: { attributeId: AttributeId }) {
  const attribute = ATTRIBUTE_BY_ID[attributeId];

  return (
    <span
      className="menu-attribute-pill"
      style={{
        "--attribute-color": attribute.cssColor,
        "--attribute-accent": attribute.cssAccent,
      } as CSSProperties}
    >
      {attribute.label}
    </span>
  );
}

function ScreenHeader({
  title,
  eyebrow,
  onHome,
}: {
  title: string;
  eyebrow: string;
  onHome?: () => void;
}) {
  return (
    <header className="game-header">
      <div>
        <p>{eyebrow}</p>
        <h1>{title}</h1>
      </div>
      {onHome ? (
        <button className="icon-home-button" type="button" onClick={onHome}>
          <span aria-hidden="true">⌂</span>
          ホーム
        </button>
      ) : null}
    </header>
  );
}

function BottomMenu({
  active,
  equipmentNoticeCount = 0,
  onNavigate,
}: {
  active?: NavScreen;
  equipmentNoticeCount?: number;
  onNavigate: (screen: NavScreen) => void;
}) {
  return (
    <nav className="bottom-menu" aria-label="下部メニュー">
      {NAV_ITEMS.map(([screen, label, icon]) => (
        <button
          className={active === screen ? "active" : ""}
          key={screen}
          type="button"
          onClick={() => onNavigate(screen)}
        >
          <span aria-hidden="true">{icon}</span>
          <strong>{label}</strong>
          {screen === "equipment" && equipmentNoticeCount > 0 ? (
            <em className="nav-notice" aria-label={`${equipmentNoticeCount}件の装備更新あり`}>
              !
            </em>
          ) : null}
        </button>
      ))}
    </nav>
  );
}

function HeroAvatar({ label = "煌" }: { label?: string }) {
  return (
    <div className="hero-avatar" aria-label="プレイヤーキャラ">
      <div className="avatar-aura" />
      <div className="avatar-head" />
      <div className="avatar-body">
        <span>{label}</span>
      </div>
      <div className="avatar-cape" />
      <div className="avatar-blade" />
    </div>
  );
}

function EquipmentSlots({
  compact = false,
  equipmentLevels,
  equippedEquipment,
}: {
  compact?: boolean;
  equipmentLevels: EquipmentLevelMap;
  equippedEquipment: EquippedEquipment;
}) {
  return (
    <div className={compact ? "slot-grid compact" : "slot-grid"}>
      {EQUIPMENT_SLOT_ORDER.map((slot) => {
        const equipmentId = equippedEquipment[slot];
        const equipment = equipmentId ? EQUIPMENT_BY_ID[equipmentId] : null;
        const label = equipment
          ? `${equipment.name} Lv${getEquipmentLevel(equipmentLevels, equipment.id)}`
          : INITIAL_EQUIPMENT_LABELS[slot];

        return (
          <div className={equipment ? "gear-slot equipped" : "gear-slot"} key={slot}>
            <span className="slot-icon" aria-hidden="true">
              {EQUIPMENT_SLOT_LABELS[slot].slice(0, 1)}
            </span>
            <small>{EQUIPMENT_SLOT_LABELS[slot]}</small>
            <strong>{label}</strong>
          </div>
        );
      })}
    </div>
  );
}

function SkillSlots({ mainSkill }: { mainSkill: MainSkillOption }) {
  return (
    <div className="skill-slot-grid">
      <div className="skill-slot main">
        <small>MAIN</small>
        <strong>{mainSkill.name}</strong>
      </div>
      {SUB_SKILLS.map((skill, index) => (
        <div className="skill-slot" key={skill}>
          <small>SUB {index + 1}</small>
          <strong>{skill}</strong>
        </div>
      ))}
    </div>
  );
}

function getEquippedName(
  equippedEquipment: EquippedEquipment,
  slot: keyof EquippedEquipment,
  fallback: string,
): string {
  const equipmentId = equippedEquipment[slot];
  return equipmentId ? EQUIPMENT_BY_ID[equipmentId].name : fallback;
}

function getMaterialTotal(inventory: PlayerInventory): number {
  return MATERIAL_IDS.reduce((total, materialId) => total + inventory[materialId], 0);
}

function EquipmentCost({ equipment }: { equipment: EquipmentDefinition }) {
  const materialCosts = MATERIAL_IDS.filter(
    (materialId) => (equipment.cost.materials[materialId] ?? 0) > 0,
  );

  return (
    <div className="equipment-cost-list" aria-label="必要素材">
      <span>コイン {equipment.cost.coin}</span>
      {materialCosts.map((materialId) => (
        <span key={materialId}>
          {MATERIAL_LABELS[materialId]} {equipment.cost.materials[materialId]}
        </span>
      ))}
    </div>
  );
}

function getEquipmentEffectText(equipment: EquipmentDefinition, level: EquipmentLevel): string {
  const effect = getScaledEquipmentEffect(equipment, level);

  if (effect.attackBonus) {
    return `通常攻撃 +${effect.attackBonus}`;
  }

  if (effect.maxHpBonus) {
    return `最大HP +${effect.maxHpBonus}`;
  }

  if (effect.moveSpeedPercentBonus) {
    return `移動速度 +${effect.moveSpeedPercentBonus}%`;
  }

  return equipment.effectLabel;
}

function getEquipmentBattlePreview(equipment: EquipmentDefinition, level: EquipmentLevel): string {
  const effect = getScaledEquipmentEffect(equipment, level);

  if (effect.attackBonus) {
    return `攻撃力 ${PLAYER_BASE_ATTACK} → ${PLAYER_BASE_ATTACK + effect.attackBonus}`;
  }

  if (effect.maxHpBonus) {
    return `最大HP ${PLAYER_MAX_HP} → ${PLAYER_MAX_HP + effect.maxHpBonus}`;
  }

  if (effect.moveSpeedPercentBonus) {
    return `移動速度 +${effect.moveSpeedPercentBonus}%`;
  }

  return equipment.effectLabel;
}

export function HomeScreen({
  equipmentNoticeCount,
  equippedEquipment,
  inventory,
  mainSkill,
  onChallenge,
  onNavigate,
}: HomeScreenProps) {
  return (
    <main className="screen menu-screen lobby-screen has-bottom-menu">
      <div className="lobby-topbar">
        <div className="player-chip">
          <span>Lv.1</span>
          <strong>ゲストプレイヤー</strong>
        </div>
        <div className="currency-chip">コイン {inventory.coin.toLocaleString("ja-JP")}</div>
        <div className="mail-chip" aria-label="お知らせ">
          <span aria-hidden="true" />
          <strong>3</strong>
        </div>
      </div>

      <section className="lobby-stage" aria-label="ホーム">
        <div className="guild-arch" aria-hidden="true">
          <span className="guild-skyline" />
          <span className="guild-banner left" />
          <span className="guild-banner right" />
          <span className="guild-board" />
          <span className="guild-lantern" />
          <span className="guild-crate" />
          <span className="guild-shield" />
        </div>
        <HeroAvatar />
      </section>

      <section className="lobby-loadout" aria-label="現在ビルド">
        <div className="mini-status">
          <span>BUILD</span>
          <strong>{mainSkill.name}</strong>
        </div>
        <div className="mini-status">
          <span>WEAPON</span>
          <strong>{getEquippedName(equippedEquipment, "weapon", "初期武器")}</strong>
        </div>
        <div className="mini-status">
          <span>ARMOR</span>
          <strong>{getEquippedName(equippedEquipment, "body", "初期装備")}</strong>
        </div>
      </section>

      <button className="primary-button challenge-button game-cta" type="button" onClick={onChallenge}>
        <span>RAID START</span>
        出撃
      </button>

      <BottomMenu
        active="home"
        equipmentNoticeCount={equipmentNoticeCount}
        onNavigate={onNavigate}
      />
    </main>
  );
}

export function BossSelectScreen({
  selection,
  onSelectBoss,
  onSelectDifficulty,
  onHome,
  onPrep,
}: BossSelectScreenProps) {
  return (
    <main className="screen menu-screen quest-screen">
      <ScreenHeader title="討伐対象" eyebrow="RAID QUEST" onHome={onHome} />

      <section className="quest-banner-list" aria-label="ボス一覧">
        {BOSS_OPTIONS.map((boss) => {
          const selected = boss.id === selection.boss.id;

          return (
            <button
              className={`quest-banner ${selected ? "selected" : ""}`}
              key={boss.id}
              type="button"
              onClick={() => onSelectBoss(boss)}
            >
              <span className="boss-emblem" aria-hidden="true" />
              <span className="quest-copy">
                <small>RAID BOSS</small>
                <strong>{boss.name}</strong>
              </span>
              <AttributePill attributeId={boss.attributeId} />
            </button>
          );
        })}
      </section>

      <section className="dock-panel quest-dock">
        <div className="difficulty-row">
          {DIFFICULTIES.map((difficulty) => (
            <button
              className={selection.difficulty === difficulty ? "selected" : ""}
              key={difficulty}
              type="button"
              onClick={() => onSelectDifficulty(difficulty)}
            >
              {difficulty}
            </button>
          ))}
        </div>
        <button className="primary-button game-cta" type="button" onClick={onPrep}>
          出撃準備へ
        </button>
      </section>
    </main>
  );
}

export function SortiePrepScreen({
  equipmentBonus,
  equipmentLevels,
  equippedEquipment,
  selection,
  mainSkill,
  onBack,
  onStart,
}: SortiePrepScreenProps) {
  const bossStats = getBossStatsForSelection(selection);
  const playerStats = getPlayerBattleStats(equipmentBonus);

  return (
    <main className="screen menu-screen loadout-screen">
      <ScreenHeader title="出撃準備" eyebrow="LOADOUT" />

      <section className="target-plate">
        <span className="boss-emblem large" aria-hidden="true" />
        <div>
          <small>TARGET</small>
          <h2>{selection.boss.name}</h2>
        </div>
        <div className="target-tags">
          <AttributePill attributeId={selection.boss.attributeId} />
          <span>{selection.difficulty}</span>
          <span>HP {bossStats.maxHp.toLocaleString("ja-JP")}</span>
          <span>防御 {bossStats.defense}</span>
        </div>
      </section>

      <section className="battle-stat-strip" aria-label="出撃ステータス">
        <span>攻撃 {playerStats.attackPower}</span>
        <span>防御 {playerStats.defense}</span>
        <span>HP {playerStats.maxHp}</span>
        <span>移動 x{playerStats.moveSpeedMultiplier.toFixed(2)}</span>
      </section>

      <section className="slot-panel">
        <h2>SKILL DECK</h2>
        <SkillSlots mainSkill={mainSkill} />
      </section>

      <section className="slot-panel">
        <h2>EQUIPMENT</h2>
        <EquipmentSlots
          compact
          equipmentLevels={equipmentLevels}
          equippedEquipment={equippedEquipment}
        />
      </section>

      <div className="fixed-action-row">
        <button className="secondary-button" type="button" onClick={onBack}>
          戻る
        </button>
        <button className="primary-button game-cta" type="button" onClick={onStart}>
          出撃
        </button>
      </div>
    </main>
  );
}

export function FormationScreen({
  equipmentNoticeCount,
  mainSkill,
  onSave,
  onNavigate,
}: FormationScreenProps) {
  const [selectedSkill, setSelectedSkill] = useState(mainSkill);
  const [notice, setNotice] = useState("スキル選択中");

  return (
    <main className="screen menu-screen deck-screen has-bottom-menu">
      <ScreenHeader title="編成" eyebrow="SKILL DECK" />

      <section className="deck-feature">
        <small>SELECTED</small>
        <h2>{selectedSkill.name}</h2>
        <p>{selectedSkill.role}</p>
      </section>

      <section className="skill-card-wheel" aria-label="主要スキル一覧">
        {MAIN_SKILLS.map((skill) => (
          <button
            className={selectedSkill.id === skill.id ? "selected" : ""}
            key={skill.id}
            type="button"
            onClick={() => {
              setSelectedSkill(skill);
              setNotice(`${skill.name}を選択中`);
            }}
          >
            <span aria-hidden="true">✦</span>
            <strong>{skill.name}</strong>
            <small>{skill.role}</small>
          </button>
        ))}
      </section>

      <section className="slot-panel">
        <h2>SUB SLOT</h2>
        <div className="subslot-row">
          {SUB_SKILLS.map((skill, index) => (
            <span key={skill}>SUB {index + 1}: {skill}</span>
          ))}
        </div>
      </section>

      <p className="game-toast" aria-live="polite">{notice}</p>

      <div className="fixed-action-row single">
        <button
          className="primary-button game-cta"
          type="button"
          onClick={() => {
            onSave(selectedSkill);
            setNotice(`${selectedSkill.name}を保存しました`);
          }}
        >
          保存
        </button>
      </div>

      <BottomMenu
        active="formation"
        equipmentNoticeCount={equipmentNoticeCount}
        onNavigate={onNavigate}
      />
    </main>
  );
}

export function EquipmentScreen({
  craftableEquipmentCount,
  equipmentLevels,
  equipmentNoticeCount,
  equippedEquipment,
  inventory,
  ownedEquipment,
  rebirthableWeaponCount,
  upgradeableEquipmentCount,
  onCraftEquipment,
  onEquipEquipment,
  onUpgradeEquipment,
  onRebirthWeapon,
  onNavigate,
}: EquipmentScreenProps) {
  const [notice, setNotice] = useState("素材を集めて装備を作成できます");
  const equippedCount = Object.values(equippedEquipment).filter(Boolean).length;

  return (
    <main className="screen menu-screen forge-screen has-bottom-menu">
      <ScreenHeader title="装備" eyebrow="FORGE" />

      <section className="slot-panel equipped-summary-panel">
        <h2>EQUIPPED</h2>
        <div className="equipped-slot-grid">
          {Object.entries(EQUIPMENT_SLOT_LABELS).map(([slot, label]) => (
            <div className="equipped-slot" key={slot}>
              <small>{label}</small>
              <strong>
                {getEquippedName(
                  equippedEquipment,
                  slot as keyof EquippedEquipment,
                  "未装備",
                )}
              </strong>
            </div>
          ))}
        </div>
      </section>

      <section className="material-chip-panel equipment-stock-panel" aria-label="所持素材">
        <span className="material-chip">
          <i aria-hidden="true" />
          コイン <strong>{inventory.coin}</strong>
        </span>
        {MATERIAL_IDS.map((materialId) => (
          <span className="material-chip" key={materialId}>
            <i aria-hidden="true" />
            {MATERIAL_LABELS[materialId]} <strong>{inventory[materialId]}</strong>
          </span>
        ))}
      </section>

      {craftableEquipmentCount > 0 ? (
        <p className="craftable-summary">作成可能な装備 {craftableEquipmentCount}件</p>
      ) : null}
      {rebirthableWeaponCount > 0 ? (
        <p className="craftable-summary rebirthable-summary">Rebirth available: {rebirthableWeaponCount}</p>
      ) : null}

      {upgradeableEquipmentCount > 0 ? (
        <p className="craftable-summary upgradeable-summary">
          強化可能な装備 {upgradeableEquipmentCount}件
        </p>
      ) : null}

      <p className="game-toast" aria-live="polite">{notice}</p>

      <section className="equipment-craft-list" aria-label="作成可能な装備">
        {EQUIPMENT_DEFINITIONS.map((equipment) => {
          const owned = ownedEquipment[equipment.id];
          const equipped = equippedEquipment[equipment.slot] === equipment.id;
          const craftable = canCraftEquipment(inventory, equipment);
          const level = getEquipmentLevel(equipmentLevels, equipment.id);
          const nextLevel = getNextEquipmentLevel(level);
          const upgradeCost = getEquipmentUpgradeCost(level);
          const rebirthable = equipment.slot === "weapon"
            ? canRebirthWeapon(inventory, ownedEquipment, equipment.id as WeaponId)
            : false;
          const rebirthCost = rebirthable
            ? getWeaponRebirthCost(equipment.id as WeaponId)
            : null;
          const upgradeable = canUpgradeEquipment(
            inventory,
            ownedEquipment,
            equipmentLevels,
            equipment,
          );

          return (
            <article
              className={`equipment-craft-card ${equipped ? "equipped" : ""} ${
                craftable && !owned ? "craftable" : ""
              } ${upgradeable ? "upgradeable" : ""}`}
              key={equipment.id}
            >
              <div className="equipment-card-main">
                <span className="slot-icon" aria-hidden="true">
                  {EQUIPMENT_SLOT_LABELS[equipment.slot].slice(0, 1)}
                </span>
                <div>
                  <small>{EQUIPMENT_SLOT_LABELS[equipment.slot]}</small>
                  <h2>{equipment.name}</h2>
                  <p>{equipment.effectLabel}</p>
                </div>
                {craftable && !owned ? <span className="craftable-badge">作成可能</span> : null}
                {upgradeable ? <span className="craftable-badge upgradeable-badge">強化可能</span> : null}
                {rebirthable ? <span className="craftable-badge rebirth-badge">再生可能</span> : null}
              </div>
              <div className="equipment-level-row">
                <span>Lv{level}</span>
                {equipped ? <strong>装備中</strong> : null}
              </div>
              <div className="equipment-effect-preview">
                <span>現在</span>
                <strong>{getEquipmentEffectText(equipment, level)}</strong>
                {nextLevel ? (
                  <>
                    <span>次</span>
                    <strong>{getEquipmentEffectText(equipment, nextLevel)}</strong>
                  </>
                ) : (
                  <>
                    <span>到達</span>
                    <strong>最大Lv</strong>
                  </>
                )}
              </div>
              <div className="equipment-effect-preview battle-preview">
                <span>バトル</span>
                <strong>{getEquipmentBattlePreview(equipment, level)}</strong>
              </div>
              <EquipmentCost equipment={equipment} />
              {!owned ? (
                <button
                  className="primary-button game-cta"
                  disabled={!craftable}
                  type="button"
                  onClick={() => {
                    const crafted = onCraftEquipment(equipment.id);
                    setNotice(
                      crafted
                        ? `${equipment.name}を作成しました`
                        : `${equipment.name}は素材またはコインが不足しています`,
                    );
                  }}
                >
                  {craftable ? "作成" : "素材不足"}
                </button>
              ) : (
                <div className="equipment-action-stack">
                  {rebirthable && rebirthCost ? (
                    <>
                      <div className="upgrade-cost">
                        再生コスト: コイン×{rebirthCost.coin}
                        {Object.entries(rebirthCost.materials).map(([materialId, amount]) =>
                          amount > 0 ? ` / ${materialId}×${amount}` : "",
                        )}
                      </div>
                      <button
                        className="secondary-button rebirth-button"
                        disabled={!rebirthable}
                        type="button"
                        onClick={() => {
                          const reborn = onRebirthWeapon(equipment.id as WeaponId);
                          setNotice(
                            reborn
                              ? `${equipment.name}を再生しました`
                              : `${equipment.name}はまだ再生できません`,
                          );
                        }}
                      >
                        再生する
                      </button>
                    </>
                  ) : null}
                  <button
                    className={equipped ? "secondary-button equipped-button" : "primary-button game-cta"}
                    disabled={equipped}
                    type="button"
                    onClick={() => {
                      const equippedNow = onEquipEquipment(equipment.id);
                      setNotice(
                        equippedNow
                          ? `${equipment.name}を装備しました`
                          : `${equipment.name}はまだ作成されていません`,
                      );
                    }}
                  >
                    {equipped ? "装備中" : "装備する"}
                  </button>
                  {upgradeCost ? (
                    <>
                      <div className="upgrade-cost">
                        必要: 魔力の欠片×{upgradeCost.magicShard} / コイン×{upgradeCost.coin}
                      </div>
                      <button
                        className="secondary-button upgrade-button"
                        disabled={!upgradeable}
                        type="button"
                        onClick={() => {
                          const upgraded = onUpgradeEquipment(equipment.id);
                          setNotice(
                            upgraded
                              ? `${equipment.name}をLv${level + 1}に強化しました`
                              : `${equipment.name}は素材またはコインが不足しています`,
                          );
                        }}
                      >
                        {upgradeable ? "強化する" : "強化素材不足"}
                      </button>
                    </>
                  ) : (
                    <div className="max-level-label">最大Lv</div>
                  )}
                </div>
              )}
            </article>
          );
        })}
      </section>

      <p className="game-toast">装備中 {equippedCount}/4</p>

      <BottomMenu
        active="equipment"
        equipmentNoticeCount={equipmentNoticeCount}
        onNavigate={onNavigate}
      />
    </main>
  );
}

export function SettingsScreen({
  equipmentLevels,
  equipmentNoticeCount,
  equippedEquipment,
  inventory,
  ownedEquipment,
  onHome,
  onNavigate,
  onResetInventory,
}: SettingsScreenProps) {
  const [resetNotice, setResetNotice] = useState(
    "リセットするとコイン・素材・作成済み装備・装備Lv・装備中状態がすべて初期化されます",
  );

  return (
    <main className="screen menu-screen option-screen has-bottom-menu">
      <ScreenHeader title="設定" eyebrow="OPTIONS" />

      <section className="help-command-grid" aria-label="操作説明">
        {[
          ["SWIPE", "移動"],
          ["TAP", "攻撃"],
          ["FLICK", "回避"],
          ["SKILL", "発動"],
        ].map(([action, description]) => (
          <div className="help-command" key={action}>
            <span>{action}</span>
            <strong>{description}</strong>
          </div>
        ))}
      </section>

      <section className="coming-soon-panel">
        <span>COMING SOON</span>
        <strong>スキルボタン位置調整</strong>
      </section>

      <section className="slot-panel">
        <h2>GRAPHICS</h2>
        <div className="difficulty-row segment-row">
          <button type="button">低</button>
          <button className="selected" type="button">標準</button>
          <button type="button">高</button>
        </div>
      </section>

      <section className="slot-panel demo-data-panel">
        <h2>DEMO DATA</h2>
        <div className="demo-data-row">
          <span>コイン {inventory.coin.toLocaleString("ja-JP")}</span>
          <span>素材合計 {getMaterialTotal(inventory)}</span>
          <span>作成済み {Object.values(ownedEquipment).filter(Boolean).length}</span>
          <span>装備中 {Object.values(equippedEquipment).filter(Boolean).length}</span>
          <span>Lv合計 {Object.values(equipmentLevels).reduce((total, level) => total + level, 0)}</span>
        </div>
        <button
          className="secondary-button"
          type="button"
          onClick={() => {
            onResetInventory();
            setResetNotice("コイン・素材・作成済み装備・装備Lv・装備中状態を初期化しました");
          }}
        >
          所持データリセット
        </button>
        <p className="game-toast" aria-live="polite">{resetNotice}</p>
      </section>

      <div className="fixed-action-row single">
        <button className="primary-button game-cta" type="button" onClick={onHome}>
          ホームへ戻る
        </button>
      </div>

      <BottomMenu
        active="settings"
        equipmentNoticeCount={equipmentNoticeCount}
        onNavigate={onNavigate}
      />
    </main>
  );
}
