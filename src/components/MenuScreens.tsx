import type { CSSProperties } from "react";
import { useState } from "react";
import { ATTRIBUTE_BY_ID } from "../game/constants";
import {
  BOSS_OPTIONS,
  DIFFICULTIES,
  EQUIPMENT,
  MAIN_SKILLS,
  MATERIALS,
  SUB_SKILLS,
  type BossDifficulty,
  type BossOption,
  type BossSelection,
  type MainSkillOption,
} from "../game/menu";
import type { AttributeId } from "../types/game";

type NavScreen = "home" | "formation" | "equipment" | "settings";

interface HomeScreenProps {
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
  selection: BossSelection;
  mainSkill: MainSkillOption;
  onBack: () => void;
  onStart: () => void;
}

interface FormationScreenProps {
  mainSkill: MainSkillOption;
  onSave: (skill: MainSkillOption) => void;
  onHome: () => void;
  onNavigate: (screen: NavScreen) => void;
}

interface EquipmentScreenProps {
  onHome: () => void;
  onNavigate: (screen: NavScreen) => void;
}

interface SettingsScreenProps {
  onHome: () => void;
  onNavigate: (screen: NavScreen) => void;
}

const NAV_ITEMS = [
  ["home", "ホーム", "⌂"],
  ["formation", "編成", "✦"],
  ["equipment", "装備", "◆"],
  ["settings", "設定", "⚙"],
] as const;

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
  onNavigate,
}: {
  active?: NavScreen;
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

function EquipmentSlots({ compact = false }: { compact?: boolean }) {
  return (
    <div className={compact ? "slot-grid compact" : "slot-grid"}>
      {EQUIPMENT.map(([slot, item]) => (
        <div className="gear-slot" key={slot}>
          <span className="slot-icon" aria-hidden="true">{slot.slice(0, 1)}</span>
          <small>{slot}</small>
          <strong>{item}</strong>
        </div>
      ))}
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

export function HomeScreen({ mainSkill, onChallenge, onNavigate }: HomeScreenProps) {
  return (
    <main className="screen menu-screen lobby-screen">
      <div className="lobby-topbar">
        <div className="player-chip">
          <span>Lv.1</span>
          <strong>ゲストプレイヤー</strong>
        </div>
        <div className="currency-chip">コイン 0</div>
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
          <strong>初期武器</strong>
        </div>
        <div className="mini-status">
          <span>ARMOR</span>
          <strong>初期装備</strong>
        </div>
      </section>

      <button className="primary-button challenge-button game-cta" type="button" onClick={onChallenge}>
        <span>RAID START</span>
        出撃
      </button>

      <BottomMenu active="home" onNavigate={onNavigate} />
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
  selection,
  mainSkill,
  onBack,
  onStart,
}: SortiePrepScreenProps) {
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
        </div>
      </section>

      <section className="slot-panel">
        <h2>SKILL DECK</h2>
        <SkillSlots mainSkill={mainSkill} />
      </section>

      <section className="slot-panel">
        <h2>EQUIPMENT</h2>
        <EquipmentSlots compact />
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

export function FormationScreen({ mainSkill, onSave, onHome, onNavigate }: FormationScreenProps) {
  const [selectedSkill, setSelectedSkill] = useState(mainSkill);
  const [notice, setNotice] = useState("スキル選択中");

  return (
    <main className="screen menu-screen deck-screen">
      <ScreenHeader title="編成" eyebrow="SKILL DECK" onHome={onHome} />

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

      <BottomMenu active="formation" onNavigate={onNavigate} />
    </main>
  );
}

export function EquipmentScreen({ onHome, onNavigate }: EquipmentScreenProps) {
  const [notice, setNotice] = useState("クラフト素材は仮表示です");

  const showDemoNotice = () => {
    setNotice("デモ版ではクラフト画面の見た目確認のみです");
  };

  return (
    <main className="screen menu-screen forge-screen">
      <ScreenHeader title="装備" eyebrow="FORGE" onHome={onHome} />

      <section className="slot-panel forge-slots">
        <h2>EQUIPMENT SLOT</h2>
        <EquipmentSlots />
      </section>

      <section className="material-chip-panel">
        {MATERIALS.map(([label, value]) => (
          <span className="material-chip" key={label}>
            <i aria-hidden="true" />
            {label} <strong>{value}</strong>
          </span>
        ))}
      </section>

      <p className="game-toast" aria-live="polite">{notice}</p>

      <div className="fixed-action-row">
        <button className="primary-button game-cta" type="button" onClick={showDemoNotice}>
          作成
        </button>
        <button className="secondary-button forge-button" type="button" onClick={showDemoNotice}>
          強化
        </button>
      </div>

      <BottomMenu active="equipment" onNavigate={onNavigate} />
    </main>
  );
}

export function SettingsScreen({ onHome, onNavigate }: SettingsScreenProps) {
  return (
    <main className="screen menu-screen option-screen">
      <ScreenHeader title="設定" eyebrow="OPTIONS" onHome={onHome} />

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

      <div className="fixed-action-row single">
        <button className="primary-button game-cta" type="button" onClick={onHome}>
          ホームへ戻る
        </button>
      </div>

      <BottomMenu active="settings" onNavigate={onNavigate} />
    </main>
  );
}
