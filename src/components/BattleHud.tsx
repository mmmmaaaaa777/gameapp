import type { CSSProperties, MouseEvent, PointerEvent } from "react";
import { ATTRIBUTES, ATTRIBUTE_BY_ID, SKILLS } from "../game/constants";
import type { AttributeId, BattleUiSnapshot, SkillId } from "../types/game";

interface BattleHudProps {
  snapshot: BattleUiSnapshot;
  onSkill: (skillId: SkillId) => void;
  onAttribute: (attributeId: AttributeId) => void;
}

function stopControlEvent(event: PointerEvent<HTMLElement> | MouseEvent<HTMLElement>): void {
  event.preventDefault();
  event.stopPropagation();
}

function formatCooldown(ms: number): string {
  if (ms <= 0) {
    return "";
  }

  return `${Math.ceil(ms / 1000)}s`;
}

function HpBar({
  label,
  value,
  max,
  variant,
}: {
  label: string;
  value: number;
  max: number;
  variant: "player" | "boss";
}) {
  const ratio = Math.max(0, Math.min(value / max, 1));

  return (
    <div className={`hp-row ${variant}`}>
      <span>{label}</span>
      <div className="hp-track" aria-hidden="true">
        <div className="hp-fill" style={{ width: `${ratio * 100}%` }} />
      </div>
      <strong>
        {Math.ceil(value)}/{max}
      </strong>
    </div>
  );
}

export function BattleHud({ snapshot, onSkill, onAttribute }: BattleHudProps) {
  const activeAttribute = ATTRIBUTE_BY_ID[snapshot.activeAttribute];

  return (
    <div
      className="battle-hud"
      data-ui-control="true"
      onPointerDown={stopControlEvent}
      onPointerMove={stopControlEvent}
      onPointerUp={stopControlEvent}
    >
      <div className="hud-top">
        <HpBar label="BOSS" value={snapshot.bossHp} max={300} variant="boss" />
        <HpBar label="PLAYER" value={snapshot.playerHp} max={100} variant="player" />
      </div>

      <div className="hud-info">
        <span>時間 {snapshot.elapsedSeconds.toFixed(1)}秒</span>
        <span>与 {snapshot.dealtDamage}</span>
        <span>被 {snapshot.takenDamage}</span>
        <span className="active-attribute" style={{ borderColor: activeAttribute.cssColor }}>
          {activeAttribute.label} {activeAttribute.description}
        </span>
      </div>

      <div className="battle-notice" aria-live="polite">
        {snapshot.notice}
      </div>

      <div className="hud-bottom">
        <div className="skill-row" aria-label="スキル">
          {SKILLS.map((skill) => {
            const cooldown = snapshot.skillCooldowns[skill.id];
            const disabled = cooldown > 0;

            return (
              <button
                className="skill-button"
                data-ui-control="true"
                disabled={disabled}
                key={skill.id}
                type="button"
                onClick={(event) => {
                  stopControlEvent(event);
                  onSkill(skill.id);
                }}
                onPointerDown={stopControlEvent}
              >
                <span className="skill-short">{skill.shortLabel}</span>
                <span className="skill-label">{skill.label}</span>
                <span className="skill-meta">
                  {disabled ? formatCooldown(cooldown) : `${skill.damage} dmg`}
                </span>
              </button>
            );
          })}
        </div>

        <div className="attribute-row" aria-label="属性切り替え">
          {ATTRIBUTES.map((attribute) => {
            const active = attribute.id === snapshot.activeAttribute;

            return (
              <button
                aria-pressed={active}
                className={`attribute-button ${active ? "active" : ""}`}
                data-ui-control="true"
                key={attribute.id}
                style={
                  {
                    "--attribute-color": attribute.cssColor,
                    "--attribute-accent": attribute.cssAccent,
                  } as CSSProperties
                }
                type="button"
                onClick={(event) => {
                  stopControlEvent(event);
                  onAttribute(attribute.id);
                }}
                onPointerDown={stopControlEvent}
              >
                {attribute.label}
              </button>
            );
          })}
        </div>
      </div>

      <p className="operation-hint">
        スワイプで移動 / タップで攻撃 / 素早いフリックで回避
      </p>
    </div>
  );
}
