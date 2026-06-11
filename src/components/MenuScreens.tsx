import type { CSSProperties } from "react";
import { useState } from "react";
import { ATTRIBUTE_BY_ID, PLAYER_BASE_ATTACK, PLAYER_MAX_HP } from "../game/constants";
import { createBattleBalanceSummary, type BattleBalanceSummary } from "../game/balance";
import {
  canCraftEquipment,
  canRebirthWeapon,
  canUpgradeEquipment,
  EQUIPMENT_BY_ID,
  EQUIPMENT_SLOT_LABELS,
  type EquipmentScreenMode,
  getEquipmentImageSrc,
  getEquipmentListForMode,
  getEquipmentLevel,
  getEquipmentUpgradeCost,
  getNextEquipmentLevel,
  getNextRebirthWeapon,
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
  EquipmentUpgradeCost,
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
  rebirthableWeaponCount: number;
  upgradeableEquipmentCount: number;
  onCraftEquipment: (equipmentId: EquipmentId) => boolean;
  onEquipEquipment: (equipmentId: EquipmentId) => boolean;
  onRebirthWeapon: (weaponId: WeaponId) => boolean;
  onUpgradeEquipment: (equipmentId: EquipmentId) => boolean;
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
  onGrantDemoMaterials: () => void;
  onResetInventory: () => void;
}

const NAV_ITEMS = [
  ["home", "ホーム", "⌂"],
  ["formation", "編成", "✦"],
  ["equipment", "装備", "◆"],
  ["settings", "設定", "⚙"],
] as const;

const EQUIPMENT_SLOT_ORDER: EquipmentSlot[] = ["weapon", "head", "body", "feet"];

const EQUIPMENT_MODE_LABELS: Record<EquipmentScreenMode, string> = {
  craft: "作成",
  rebirth: "転生",
  upgrade: "強化",
};

const EQUIPMENT_MODE_ORDER: EquipmentScreenMode[] = ["craft", "rebirth", "upgrade"];

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

function EquipmentImage({ equipment }: { equipment: EquipmentDefinition }) {
  return (
    <figure className="equipment-image-frame">
      <img
        alt={`${equipment.name}の仮画像`}
        loading="lazy"
        src={getEquipmentImageSrc(equipment)}
        onError={(event) => {
          event.currentTarget.classList.add("image-missing");
          event.currentTarget.removeAttribute("src");
        }}
      />
    </figure>
  );
}

function EquipmentCost({
  cost,
  inventory,
  title = "必要素材",
}: {
  cost: EquipmentDefinition["cost"];
  inventory: PlayerInventory;
  title?: string;
}) {
  const materialCosts = MATERIAL_IDS.filter((materialId) => (cost.materials[materialId] ?? 0) > 0);
  const coinEnough = inventory.coin >= cost.coin;

  return (
    <div className="equipment-cost-block">
      <strong>{title}</strong>
      <div className="equipment-cost-list" aria-label={title}>
        <span className={coinEnough ? "enough" : "short"}>
          コイン {cost.coin} / 所持 {inventory.coin}
        </span>
        {materialCosts.map((materialId) => {
          const required = cost.materials[materialId] ?? 0;
          const enough = inventory[materialId] >= required;

          return (
            <span className={enough ? "enough" : "short"} key={materialId}>
              {MATERIAL_LABELS[materialId]} {required} / 所持 {inventory[materialId]}
            </span>
          );
        })}
      </div>
    </div>
  );
}

function EquipmentUpgradeCostView({
  cost,
  inventory,
}: {
  cost: EquipmentUpgradeCost;
  inventory: PlayerInventory;
}) {
  const coinEnough = inventory.coin >= cost.coin;
  const shardEnough = inventory.magicShard >= cost.magicShard;

  return (
    <div className="equipment-cost-block">
      <strong>必要素材</strong>
      <div className="equipment-cost-list" aria-label="強化に必要な素材">
        <span className={coinEnough ? "enough" : "short"}>
          コイン {cost.coin} / 所持 {inventory.coin}
        </span>
        <span className={shardEnough ? "enough" : "short"}>
          {MATERIAL_LABELS.magicShard} {cost.magicShard} / 所持 {inventory.magicShard}
        </span>
      </div>
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

function getWeaponLevelText(summary: BattleBalanceSummary): string {
  return summary.weaponLevel ? `Lv${summary.weaponLevel}` : "-";
}

function SortieBalancePanel({ summary }: { summary: BattleBalanceSummary }) {
  const rows = [
    ["難易度", summary.difficulty],
    ["ボス役割", summary.bossRoleLabel],
    ["ボスHP", summary.bossHp.toLocaleString("ja-JP")],
    ["ボス防御", summary.bossDefense.toLocaleString("ja-JP")],
    ["ボス属性", summary.bossAttributeLabel],
    ["ブレイク", summary.bossBreakGauge.toLocaleString("ja-JP")],
    ["ダウン", `${summary.bossDownDurationSeconds.toFixed(1)}秒`],
    ["前方攻撃", summary.bossFrontalAttackPower.toLocaleString("ja-JP")],
    ["突進", summary.bossChargeAttackPower.toLocaleString("ja-JP")],
    ["範囲攻撃", summary.bossAreaAttackPower.toLocaleString("ja-JP")],
    ["装備中武器", summary.equippedWeaponName],
    ["武器Lv", getWeaponLevelText(summary)],
    ["攻撃属性", summary.attackAttributeLabel],
    ["防御属性", summary.defenseAttributeLabel],
    ["攻撃相性", summary.attackRelationLabel],
    ["被弾相性", summary.defenseRelationLabel],
    ["攻撃力", summary.attackPower.toLocaleString("ja-JP")],
    ["防御力", summary.defense.toLocaleString("ja-JP")],
    ["最大HP", summary.maxHp.toLocaleString("ja-JP")],
    ["通常攻撃", `${summary.normalAttackDamage.toLocaleString("ja-JP")} ダメージ`],
  ];

  return (
    <section className="balance-panel sortie-balance-panel" aria-label="バランス確認">
      <div className="balance-heading">
        <span>BALANCE</span>
        <strong>出撃条件</strong>
      </div>
      <dl className="balance-grid">
        {rows.map(([label, value]) => (
          <div key={label}>
            <dt>{label}</dt>
            <dd>{value}</dd>
          </div>
        ))}
      </dl>
    </section>
  );
}

function CraftEquipmentCard({
  equipment,
  equipmentLevels,
  equippedEquipment,
  inventory,
  ownedEquipment,
  onCraftEquipment,
  onEquipEquipment,
  onNotice,
}: {
  equipment: EquipmentDefinition;
  equipmentLevels: EquipmentLevelMap;
  equippedEquipment: EquippedEquipment;
  inventory: PlayerInventory;
  ownedEquipment: OwnedEquipment;
  onCraftEquipment: (equipmentId: EquipmentId) => boolean;
  onEquipEquipment: (equipmentId: EquipmentId) => boolean;
  onNotice: (message: string) => void;
}) {
  const owned = ownedEquipment[equipment.id];
  const equipped = equippedEquipment[equipment.slot] === equipment.id;
  const craftable = canCraftEquipment(inventory, equipment);
  const level = getEquipmentLevel(equipmentLevels, equipment.id);

  return (
    <article
      className={`equipment-craft-card equipment-mode-card ${equipped ? "equipped" : ""} ${
        craftable && !owned ? "craftable" : ""
      }`}
    >
      <div className="equipment-card-main">
        <EquipmentImage equipment={equipment} />
        <div className="equipment-card-copy">
          <small>{EQUIPMENT_SLOT_LABELS[equipment.slot]}</small>
          <h2>{equipment.name}</h2>
          <p>{getEquipmentEffectText(equipment, level)}</p>
          {equipment.element ? <AttributePill attributeId={equipment.element} /> : null}
        </div>
        {craftable && !owned ? <span className="craftable-badge">作成可能</span> : null}
        {owned ? <span className="craftable-badge owned-badge">作成済み</span> : null}
      </div>

      <div className="equipment-level-row">
        <span>{EQUIPMENT_SLOT_LABELS[equipment.slot]}</span>
        {equipped ? <strong>装備中</strong> : owned ? <strong>作成済み</strong> : <strong>未作成</strong>}
      </div>

      <div className="equipment-effect-preview battle-preview">
        <span>反映</span>
        <strong>{getEquipmentBattlePreview(equipment, level)}</strong>
      </div>

      <EquipmentCost cost={equipment.cost} inventory={inventory} />

      {!owned ? (
        <button
          className="primary-button game-cta"
          disabled={!craftable}
          type="button"
          onClick={() => {
            const crafted = onCraftEquipment(equipment.id);
            onNotice(
              crafted
                ? `${equipment.name}を作成しました`
                : `${equipment.name}は素材またはコインが不足しています`,
            );
          }}
        >
          {craftable ? "作成する" : "素材不足"}
        </button>
      ) : (
        <div className="equipment-action-stack">
          <button
            className={equipped ? "secondary-button equipped-button" : "primary-button game-cta"}
            disabled={equipped}
            type="button"
            onClick={() => {
              const equippedNow = onEquipEquipment(equipment.id);
              onNotice(
                equippedNow
                  ? `${equipment.name}を装備しました`
                  : `${equipment.name}はまだ作成されていません`,
              );
            }}
          >
            {equipped ? "装備中" : "装備する"}
          </button>
        </div>
      )}
    </article>
  );
}

function RebirthEquipmentCard({
  equipment,
  equipmentLevels,
  equippedEquipment,
  inventory,
  ownedEquipment,
  onEquipEquipment,
  onNotice,
  onRebirthWeapon,
}: {
  equipment: EquipmentDefinition;
  equipmentLevels: EquipmentLevelMap;
  equippedEquipment: EquippedEquipment;
  inventory: PlayerInventory;
  ownedEquipment: OwnedEquipment;
  onEquipEquipment: (equipmentId: EquipmentId) => boolean;
  onNotice: (message: string) => void;
  onRebirthWeapon: (weaponId: WeaponId) => boolean;
}) {
  const weaponId = equipment.id as WeaponId;
  const owned = ownedEquipment[equipment.id];
  const equipped = equippedEquipment.weapon === equipment.id;
  const nextWeaponId = getNextRebirthWeapon(equipment.id);
  const nextEquipment = nextWeaponId ? EQUIPMENT_BY_ID[nextWeaponId] : null;
  const nextOwned = nextWeaponId ? ownedEquipment[nextWeaponId] : false;
  const rebirthable = canRebirthWeapon(inventory, ownedEquipment, weaponId);
  const rebirthCost = nextWeaponId ? getWeaponRebirthCost(weaponId) : null;
  const level = getEquipmentLevel(equipmentLevels, equipment.id);
  const status = !owned
    ? "未所持"
    : !nextWeaponId
      ? "転生先なし"
      : nextOwned
        ? "転生済み"
        : rebirthable
          ? "転生可能"
          : "素材不足";

  return (
    <article
      className={`equipment-craft-card equipment-mode-card ${equipped ? "equipped" : ""} ${
        rebirthable ? "rebirthable" : ""
      }`}
    >
      <div className="equipment-card-main">
        <EquipmentImage equipment={equipment} />
        <div className="equipment-card-copy">
          <small>{equipped ? "装備中" : "所持武器"}</small>
          <h2>{equipment.name}</h2>
          <p>{getEquipmentEffectText(equipment, level)}</p>
          {equipment.element ? <AttributePill attributeId={equipment.element} /> : null}
        </div>
        <span className={rebirthable ? "craftable-badge rebirth-badge" : "craftable-badge muted-badge"}>
          {status}
        </span>
      </div>

      <div className="equipment-effect-preview">
        <span>転生先</span>
        <strong>{nextEquipment ? nextEquipment.name : "転生先なし"}</strong>
      </div>

      {nextEquipment ? (
        <div className="equipment-effect-preview battle-preview">
          <span>変化</span>
          <strong>
            {getEquipmentBattlePreview(equipment, level)} / {getEquipmentBattlePreview(nextEquipment, level)}
          </strong>
        </div>
      ) : null}

      {rebirthCost ? (
        <EquipmentCost cost={rebirthCost} inventory={inventory} title="転生素材" />
      ) : (
        <div className="max-level-label">転生素材なし</div>
      )}

      <div className="equipment-action-stack">
        {owned ? (
          <button
            className={equipped ? "secondary-button equipped-button" : "primary-button game-cta"}
            disabled={equipped}
            type="button"
            onClick={() => {
              const equippedNow = onEquipEquipment(equipment.id);
              onNotice(
                equippedNow
                  ? `${equipment.name}を装備しました`
                  : `${equipment.name}はまだ作成されていません`,
              );
            }}
          >
            {equipped ? "装備中" : "装備する"}
          </button>
        ) : null}
        <button
          className="secondary-button rebirth-button"
          disabled={!rebirthable}
          type="button"
          onClick={() => {
            const reborn = onRebirthWeapon(weaponId);
            onNotice(
              reborn
                ? `${equipment.name}を転生しました`
                : `${equipment.name}はまだ転生できません`,
            );
          }}
        >
          {rebirthable ? "転生する" : status}
        </button>
      </div>
    </article>
  );
}

function UpgradeEquipmentCard({
  equipment,
  equipmentLevels,
  equippedEquipment,
  inventory,
  ownedEquipment,
  onEquipEquipment,
  onNotice,
  onUpgradeEquipment,
}: {
  equipment: EquipmentDefinition;
  equipmentLevels: EquipmentLevelMap;
  equippedEquipment: EquippedEquipment;
  inventory: PlayerInventory;
  ownedEquipment: OwnedEquipment;
  onEquipEquipment: (equipmentId: EquipmentId) => boolean;
  onNotice: (message: string) => void;
  onUpgradeEquipment: (equipmentId: EquipmentId) => boolean;
}) {
  const equipped = equippedEquipment[equipment.slot] === equipment.id;
  const level = getEquipmentLevel(equipmentLevels, equipment.id);
  const nextLevel = getNextEquipmentLevel(level);
  const upgradeCost = getEquipmentUpgradeCost(level);
  const upgradeable = canUpgradeEquipment(inventory, ownedEquipment, equipmentLevels, equipment);
  const status = !nextLevel ? "最大Lv" : upgradeable ? "強化可能" : "素材不足";

  return (
    <article
      className={`equipment-craft-card equipment-mode-card ${equipped ? "equipped" : ""} ${
        upgradeable ? "upgradeable" : ""
      }`}
    >
      <div className="equipment-card-main">
        <EquipmentImage equipment={equipment} />
        <div className="equipment-card-copy">
          <small>{equipped ? "装備中" : EQUIPMENT_SLOT_LABELS[equipment.slot]}</small>
          <h2>{equipment.name}</h2>
          <p>Lv{level}</p>
          {equipment.element ? <AttributePill attributeId={equipment.element} /> : null}
        </div>
        <span className={upgradeable ? "craftable-badge upgradeable-badge" : "craftable-badge muted-badge"}>
          {status}
        </span>
      </div>

      <div className="equipment-level-row">
        <span>現在Lv</span>
        <strong>Lv{level}</strong>
      </div>

      <div className="equipment-effect-preview">
        <span>現在</span>
        <strong>{getEquipmentEffectText(equipment, level)}</strong>
      </div>

      {nextLevel ? (
        <div className="equipment-effect-preview battle-preview">
          <span>次</span>
          <strong>{getEquipmentEffectText(equipment, nextLevel)}</strong>
        </div>
      ) : (
        <div className="max-level-label">最大Lv</div>
      )}

      {upgradeCost ? (
        <EquipmentUpgradeCostView cost={upgradeCost} inventory={inventory} />
      ) : null}

      <div className="equipment-action-stack">
        <button
          className={equipped ? "secondary-button equipped-button" : "primary-button game-cta"}
          disabled={equipped}
          type="button"
          onClick={() => {
            const equippedNow = onEquipEquipment(equipment.id);
            onNotice(
              equippedNow
                ? `${equipment.name}を装備しました`
                : `${equipment.name}はまだ作成されていません`,
            );
          }}
        >
          {equipped ? "装備中" : "装備する"}
        </button>
        {nextLevel ? (
          <button
            className="secondary-button upgrade-button"
            disabled={!upgradeable}
            type="button"
            onClick={() => {
              const upgraded = onUpgradeEquipment(equipment.id);
              onNotice(
                upgraded
                  ? `${equipment.name}をLv${nextLevel}に強化しました`
                  : `${equipment.name}は素材またはコインが不足しています`,
              );
            }}
          >
            {upgradeable ? "強化する" : "素材不足"}
          </button>
        ) : null}
      </div>
    </article>
  );
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
                <small>{boss.roleLabel}</small>
                <strong>{boss.name}</strong>
                <em>{boss.roleDescription}</em>
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
  const balanceSummary = createBattleBalanceSummary({
    equipmentBonus,
    equipmentLevels,
    equippedEquipment,
    selection,
  });

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
          <span>{balanceSummary.bossRoleLabel}</span>
          <span>HP {balanceSummary.bossHp.toLocaleString("ja-JP")}</span>
          <span>防御 {balanceSummary.bossDefense}</span>
        </div>
      </section>

      <section className="battle-stat-strip" aria-label="出撃ステータス">
        <span>攻撃 {balanceSummary.attackPower}</span>
        <span>防御 {balanceSummary.defense}</span>
        <span>HP {balanceSummary.maxHp}</span>
        <span>通常 {balanceSummary.normalAttackDamage}</span>
      </section>

      <SortieBalancePanel summary={balanceSummary} />

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

      <div className="formation-save-row">
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

      <section className="slot-panel">
        <h2>SUB SLOT</h2>
        <div className="subslot-row">
          {SUB_SKILLS.map((skill, index) => (
            <span key={skill}>SUB {index + 1}: {skill}</span>
          ))}
        </div>
      </section>

      <p className="game-toast" aria-live="polite">{notice}</p>

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
  onRebirthWeapon,
  onUpgradeEquipment,
  onNavigate,
}: EquipmentScreenProps) {
  const [notice, setNotice] = useState("作成・転生・強化を選んで装備を確認できます");
  const [mode, setMode] = useState<EquipmentScreenMode>("craft");
  const [selectedSlot, setSelectedSlot] = useState<EquipmentSlot>("weapon");
  const equippedCount = Object.values(equippedEquipment).filter(Boolean).length;
  const targetEquipment = getEquipmentListForMode(mode, selectedSlot, ownedEquipment);
  const modeTitle = `${EQUIPMENT_MODE_LABELS[mode]} / ${EQUIPMENT_SLOT_LABELS[selectedSlot]}`;
  const isRebirthUnsupportedSlot = mode === "rebirth" && selectedSlot !== "weapon";
  const emptyMessage =
    mode === "upgrade"
      ? "この部位の強化できる装備はまだありません"
      : "表示できる装備がありません";

  return (
    <main className="screen menu-screen forge-screen has-bottom-menu">
      <ScreenHeader title="装備" eyebrow="FORGE" />

      <section className="slot-panel equipped-summary-panel">
        <h2>現在装備</h2>
        <div className="equipped-slot-grid">
          {EQUIPMENT_SLOT_ORDER.map((slot) => (
            <div className="equipped-slot" key={slot}>
              <small>{EQUIPMENT_SLOT_LABELS[slot]}</small>
              <strong>
                {getEquippedName(
                  equippedEquipment,
                  slot,
                  "未装備",
                )}
              </strong>
            </div>
          ))}
        </div>
      </section>

      <section className="equipment-filter-panel" aria-label="装備操作切替">
        <div className="equipment-filter-group">
          <span>操作</span>
          <div className="equipment-toggle-row">
            {EQUIPMENT_MODE_ORDER.map((nextMode) => (
              <button
                className={mode === nextMode ? "selected" : ""}
                key={nextMode}
                type="button"
                onClick={() => setMode(nextMode)}
              >
                {EQUIPMENT_MODE_LABELS[nextMode]}
              </button>
            ))}
          </div>
        </div>

        <div className="equipment-filter-group">
          <span>部位</span>
          <div className="equipment-part-tabs">
            {EQUIPMENT_SLOT_ORDER.map((slot) => (
              <button
                className={selectedSlot === slot ? "selected" : ""}
                key={slot}
                type="button"
                onClick={() => setSelectedSlot(slot)}
              >
                {EQUIPMENT_SLOT_LABELS[slot]}
              </button>
            ))}
          </div>
        </div>
      </section>

      {craftableEquipmentCount > 0 ? (
        <p className="craftable-summary">作成可能な装備 {craftableEquipmentCount}件</p>
      ) : null}
      {rebirthableWeaponCount > 0 ? (
        <p className="craftable-summary rebirthable-summary">
          武器転生可能な装備 {rebirthableWeaponCount}件
        </p>
      ) : null}
      {upgradeableEquipmentCount > 0 ? (
        <p className="craftable-summary upgradeable-summary">
          強化可能な装備 {upgradeableEquipmentCount}件
        </p>
      ) : null}

      <p className="game-toast" aria-live="polite">{notice}</p>

      <section className="equipment-craft-list" aria-label={`${modeTitle}の対象装備`}>
        <div className="equipment-list-header">
          <div>
            <small>{EQUIPMENT_MODE_LABELS[mode]}</small>
            <h2>{modeTitle}</h2>
          </div>
          <span>{targetEquipment.length}件</span>
        </div>

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

        {isRebirthUnsupportedSlot ? (
          <div className="equipment-empty-state">
            この部位の転生はまだありません
          </div>
        ) : targetEquipment.length === 0 ? (
          <div className="equipment-empty-state">
            {emptyMessage}
          </div>
        ) : (
          targetEquipment.map((equipment) =>
            mode === "craft" ? (
              <CraftEquipmentCard
                equipment={equipment}
                equipmentLevels={equipmentLevels}
                equippedEquipment={equippedEquipment}
                inventory={inventory}
                key={equipment.id}
                ownedEquipment={ownedEquipment}
                onCraftEquipment={onCraftEquipment}
                onEquipEquipment={onEquipEquipment}
                onNotice={setNotice}
              />
            ) : mode === "rebirth" ? (
              <RebirthEquipmentCard
                equipment={equipment}
                equipmentLevels={equipmentLevels}
                equippedEquipment={equippedEquipment}
                inventory={inventory}
                key={equipment.id}
                ownedEquipment={ownedEquipment}
                onEquipEquipment={onEquipEquipment}
                onNotice={setNotice}
                onRebirthWeapon={onRebirthWeapon}
              />
            ) : (
              <UpgradeEquipmentCard
                equipment={equipment}
                equipmentLevels={equipmentLevels}
                equippedEquipment={equippedEquipment}
                inventory={inventory}
                key={equipment.id}
                ownedEquipment={ownedEquipment}
                onEquipEquipment={onEquipEquipment}
                onNotice={setNotice}
                onUpgradeEquipment={onUpgradeEquipment}
              />
            ),
          )
        )}
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
  onGrantDemoMaterials,
  onNavigate,
  onResetInventory,
}: SettingsScreenProps) {
  const [resetNotice, setResetNotice] = useState("デモ確認用の操作結果をここに表示します");

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
        <p className="demo-data-description">
          作成・転生の確認用に素材とコインを追加します。
        </p>
        <button
          className="secondary-button demo-grant-button"
          type="button"
          onClick={() => {
            onGrantDemoMaterials();
            setResetNotice("デモ用素材を付与しました");
          }}
        >
          デモ用素材を付与
        </button>
        <p className="demo-data-description">
          リセットするとコイン・素材・作成済み装備・装備Lv・装備中状態がすべて初期化されます。
        </p>
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
