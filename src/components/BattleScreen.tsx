import { useCallback, useEffect, useRef, useState } from "react";
import type { PointerEvent as ReactPointerEvent } from "react";
import { BattleHud } from "./BattleHud";
import {
  ATTACK_COOLDOWN_MS,
  ATTACK_DAMAGE,
  ATTACK_RANGE,
  BEAM_DAMAGE,
  BEAM_INTERVAL_MS,
  BEAM_WARNING_MS,
  BEAM_WIDTH,
  DODGE_COOLDOWN_MS,
  DODGE_DISTANCE,
  DODGE_DURATION_MS,
  DODGE_INVULNERABLE_MS,
  EMPTY_COOLDOWNS,
  FIELD_RADIUS,
  INITIAL_ATTRIBUTE,
  PLAYER_BASE_ATTACK,
  PLAYER_BASE_DEFENSE,
  PLAYER_CRITICAL_MULTIPLIER,
  PLAYER_CRITICAL_RATE,
  PLAYER_MAX_HP,
  PLAYER_SPEED_UNITS_PER_SEC,
  SHOCKWAVE_DAMAGE,
  SHOCKWAVE_INTERVAL_MS,
  SHOCKWAVE_RANGE,
  SHOCKWAVE_WARNING_MS,
  SKILL_BY_ID,
  UI_SYNC_INTERVAL_MS,
} from "../game/constants";
import {
  applyDamage,
  applyIncomingDamage,
  calculateDamage,
  canUseSkill,
  getCriticalMultiplier,
  getBattleResult,
  rollCritical,
  setSkillCooldown,
  tickCooldowns,
} from "../game/combat";
import { getBossStatsForSelection } from "../game/difficulty";
import { classifyGesture, hasSwipeMovement, shouldHandleCanvasPointer } from "../game/gesture";
import {
  addScaled,
  angleFromDirection,
  clamp,
  clampToCircle,
  distance2d,
  normalize2d,
  pointLineDistance,
  screenDeltaToWorldDirection,
  smoothStep,
} from "../game/math";
import { getAttackElement, getDefenseElement, getElementMultiplier } from "../game/elements";
import { createBattleScene, type BattleScene } from "../three/createBattleScene";
import { EQUIPMENT_BY_ID } from "../game/equipment";
import type {
  AttributeId,
  BattleEquipmentBonus,
  BattleResult,
  BattleUiSnapshot,
  CooldownMap,
  EquipmentId,
  SceneSnapshot,
  SkillId,
  Vec3XZ,
} from "../types/game";
import type { BossSelection } from "../game/menu";

interface BattleScreenProps {
  equipmentBonus?: BattleEquipmentBonus;
  selection: BossSelection;
  equippedWeaponId?: EquipmentId | null;
  onComplete: (result: BattleResult) => void;
}

interface PointerRuntime {
  active: boolean;
  startX: number;
  startY: number;
  currentX: number;
  currentY: number;
  startAtMs: number;
}

interface TimedWarning {
  ageMs: number;
  durationMs: number;
}

interface BeamWarning extends TimedWarning {
  direction: Vec3XZ;
}

interface DodgeRuntime {
  remainingMs: number;
  start: Vec3XZ;
  end: Vec3XZ;
}

interface BattleRuntime {
  playerPosition: Vec3XZ;
  playerAngle: number;
  playerHp: number;
  playerMaxHp: number;
  playerAttackPower: number;
  playerDefense: number;
  playerSpeed: number;
  bossPosition: Vec3XZ;
  bossHp: number;
  bossMaxHp: number;
  bossDefense: number;
  bossAttribute: AttributeId;
  activeAttribute: AttributeId;
  equippedWeaponId: EquipmentId | null;
  attackElement: AttributeId;
  defenseElement: AttributeId;
  movement: Vec3XZ;
  pointer: PointerRuntime;
  cooldowns: CooldownMap;
  attackCooldownMs: number;
  dodgeCooldownMs: number;
  dodgeInvulnerableMs: number;
  dodge: DodgeRuntime | null;
  playerAttackMs: number;
  elapsedMs: number;
  dealtDamage: number;
  takenDamage: number;
  dodgeSuccessCount: number;
  breakCount: number;
  notice: string;
  bossHurtMs: number;
  shockwaveCountdownMs: number;
  beamCountdownMs: number;
  shockwaveWarning: TimedWarning | null;
  beamWarning: BeamWarning | null;
  syncAccumulatorMs: number;
  finished: boolean;
}

const DEFAULT_EQUIPMENT_BONUS: BattleEquipmentBonus = {
  attackBonus: 0,
  maxHpBonus: 0,
  moveSpeedMultiplier: 1,
};

function getSkillDamageMultiplier(skillId: SkillId): number {
  return SKILL_BY_ID[skillId].damage / ATTACK_DAMAGE;
}

function calculatePlayerDamage(
  runtime: BattleRuntime,
  skillDamageMultiplier = 1,
  criticalMultiplier = 1,
) {
  return calculateDamage({
    attackPower: runtime.playerAttackPower,
    defense: runtime.bossDefense,
    elementMultiplier: getElementMultiplier(runtime.attackElement, runtime.bossAttribute),
    criticalMultiplier,
    skillDamageMultiplier,
  });
}

function getRuntimeAttackElement(
  weaponId: EquipmentId | null,
  selectedAttribute: AttributeId,
): AttributeId {
  const weapon = weaponId ? EQUIPMENT_BY_ID[weaponId] : null;

  return getAttackElement(weapon, selectedAttribute);
}

function createInitialRuntime(
  equipmentBonus: BattleEquipmentBonus,
  selection: BossSelection,
  equippedWeaponId: EquipmentId | null,
): BattleRuntime {
  const playerMaxHp = PLAYER_MAX_HP + equipmentBonus.maxHpBonus;
  const bossStats = getBossStatsForSelection(selection);
  const activeAttribute = INITIAL_ATTRIBUTE;

  return {
    playerPosition: { x: 0, z: 2.2 },
    playerAngle: angleFromDirection({ x: 0, z: -1 }),
    playerHp: playerMaxHp,
    playerMaxHp,
    playerAttackPower: PLAYER_BASE_ATTACK + equipmentBonus.attackBonus,
    playerDefense: PLAYER_BASE_DEFENSE,
    playerSpeed: PLAYER_SPEED_UNITS_PER_SEC * equipmentBonus.moveSpeedMultiplier,
    bossPosition: { x: 0, z: -1.3 },
    bossHp: bossStats.maxHp,
    bossMaxHp: bossStats.maxHp,
    bossDefense: bossStats.defense,
    bossAttribute: selection.boss.attributeId,
    activeAttribute,
    equippedWeaponId,
    attackElement: getRuntimeAttackElement(equippedWeaponId, activeAttribute),
    defenseElement: getDefenseElement(activeAttribute),
    movement: { x: 0, z: 0 },
    pointer: {
      active: false,
      startX: 0,
      startY: 0,
      currentX: 0,
      currentY: 0,
      startAtMs: 0,
    },
    cooldowns: { ...EMPTY_COOLDOWNS },
    attackCooldownMs: 0,
    dodgeCooldownMs: 0,
    dodgeInvulnerableMs: 0,
    dodge: null,
    playerAttackMs: 0,
    elapsedMs: 0,
    dealtDamage: 0,
    takenDamage: 0,
    dodgeSuccessCount: 0,
    breakCount: 0,
    notice: "ボスに近づいてタップ攻撃",
    bossHurtMs: 0,
    shockwaveCountdownMs: 1650,
    beamCountdownMs: 2800,
    shockwaveWarning: null,
    beamWarning: null,
    syncAccumulatorMs: 0,
    finished: false,
  };
}

function makeUiSnapshot(runtime: BattleRuntime): BattleUiSnapshot {
  return {
    playerHp: runtime.playerHp,
    playerMaxHp: runtime.playerMaxHp,
    playerAttackPower: runtime.playerAttackPower,
    playerDefense: runtime.playerDefense,
    bossHp: runtime.bossHp,
    bossMaxHp: runtime.bossMaxHp,
    elapsedSeconds: runtime.elapsedMs / 1000,
    dealtDamage: runtime.dealtDamage,
    takenDamage: runtime.takenDamage,
    activeAttribute: runtime.activeAttribute,
    normalAttackDamage: calculatePlayerDamage(runtime).damage,
    skillDamagePreview: {
      quickSlash: calculatePlayerDamage(runtime, getSkillDamageMultiplier("quickSlash")).damage,
      attributeBurst: calculatePlayerDamage(
        runtime,
        getSkillDamageMultiplier("attributeBurst"),
      ).damage,
      breakArts: calculatePlayerDamage(runtime, getSkillDamageMultiplier("breakArts")).damage,
    },
    skillCooldowns: runtime.cooldowns,
    attackReady: runtime.attackCooldownMs <= 0,
    dodgeReady: runtime.dodgeCooldownMs <= 0,
    notice: runtime.notice,
  };
}

function makeSceneSnapshot(runtime: BattleRuntime): SceneSnapshot {
  return {
    playerPosition: runtime.playerPosition,
    playerAngle: runtime.playerAngle,
    bossPosition: runtime.bossPosition,
    playerHpRatio: runtime.playerHp / runtime.playerMaxHp,
    bossHpRatio: runtime.bossHp / runtime.bossMaxHp,
    activeAttribute: runtime.activeAttribute,
    isDodging: runtime.dodgeInvulnerableMs > 0,
    playerAttackPulse: clamp(runtime.playerAttackMs / 360, 0, 1),
    playerMoveIntensity:
      runtime.dodge || Math.hypot(runtime.movement.x, runtime.movement.z) > 0.01 ? 1 : 0,
    bossHurt: runtime.bossHurtMs > 0,
    shockwaveWarning: runtime.shockwaveWarning
      ? {
          radius: SHOCKWAVE_RANGE,
          progress: clamp(runtime.shockwaveWarning.ageMs / runtime.shockwaveWarning.durationMs, 0, 1),
        }
      : undefined,
    beamWarning: runtime.beamWarning
      ? {
          direction: runtime.beamWarning.direction,
          progress: clamp(runtime.beamWarning.ageMs / runtime.beamWarning.durationMs, 0, 1),
        }
      : undefined,
  };
}

function isUiControlTarget(target: EventTarget | null): boolean {
  return target instanceof Element && Boolean(target.closest("[data-ui-control='true']"));
}

export function BattleScreen({
  equipmentBonus = DEFAULT_EQUIPMENT_BONUS,
  selection,
  equippedWeaponId = null,
  onComplete,
}: BattleScreenProps) {
  const mountRef = useRef<HTMLDivElement | null>(null);
  const sceneRef = useRef<BattleScene | null>(null);
  const runtimeRef = useRef<BattleRuntime>(
    createInitialRuntime(equipmentBonus, selection, equippedWeaponId),
  );
  const [uiSnapshot, setUiSnapshot] = useState<BattleUiSnapshot>(() =>
    makeUiSnapshot(runtimeRef.current),
  );

  const finishBattle = useCallback(
    (kind: "CLEAR" | "FAILED") => {
      const runtime = runtimeRef.current;

      if (runtime.finished) {
        return;
      }

      runtime.finished = true;
      runtime.movement = { x: 0, z: 0 };
      onComplete({
        kind,
        stats: {
          elapsedSeconds: Math.round((runtime.elapsedMs / 1000) * 10) / 10,
          dealtDamage: runtime.dealtDamage,
          takenDamage: runtime.takenDamage,
          dodgeSuccessCount: runtime.dodgeSuccessCount,
          breakCount: runtime.breakCount,
        },
      });
    },
    [onComplete],
  );

  const dealBossDamage = useCallback(
    (
      skillDamageMultiplier: number,
      range: number,
      effectScale: number,
      sourceLabel: string,
      countBreak = false,
    ) => {
      const runtime = runtimeRef.current;

      if (runtime.finished) {
        return;
      }

      const directionToBoss = normalize2d({
        x: runtime.bossPosition.x - runtime.playerPosition.x,
        z: runtime.bossPosition.z - runtime.playerPosition.z,
      });
      runtime.playerAttackMs = Math.max(runtime.playerAttackMs, 230 + effectScale * 90);
      runtime.playerAngle = angleFromDirection(directionToBoss);
      sceneRef.current?.spawnAttackFlash(runtime.attackElement, runtime.playerPosition, runtime.playerAngle);

      if (distance2d(runtime.playerPosition, runtime.bossPosition) > range) {
        runtime.notice = `${sourceLabel}: 距離が遠い`;
        setUiSnapshot(makeUiSnapshot(runtime));
        return;
      }

      const critical = rollCritical(PLAYER_CRITICAL_RATE);
      const damageResult = calculatePlayerDamage(
        runtime,
        skillDamageMultiplier,
        getCriticalMultiplier(critical, PLAYER_CRITICAL_MULTIPLIER),
      );
      const beforeHp = runtime.bossHp;
      runtime.bossHp = applyDamage(runtime.bossHp, damageResult.damage, runtime.bossMaxHp);
      const appliedDamage = beforeHp - runtime.bossHp;
      runtime.dealtDamage += appliedDamage;
      if (appliedDamage > 0 && countBreak) {
        runtime.breakCount += 1;
      }
      runtime.bossHurtMs = 220;
      runtime.notice = `${sourceLabel}: ${appliedDamage}ダメージ${critical ? " CRITICAL" : ""}`;
      sceneRef.current?.spawnHitEffect(runtime.attackElement, runtime.bossPosition, effectScale);

      const result = getBattleResult(runtime.playerHp, runtime.bossHp);
      setUiSnapshot(makeUiSnapshot(runtime));

      if (result) {
        finishBattle(result);
      }
    },
    [finishBattle],
  );

  const performAttack = useCallback(() => {
    const runtime = runtimeRef.current;

    if (runtime.attackCooldownMs > 0 || runtime.finished) {
      return;
    }

    runtime.attackCooldownMs = ATTACK_COOLDOWN_MS;
    dealBossDamage(1, ATTACK_RANGE, 0.85, "通常攻撃");
  }, [dealBossDamage]);

  const startDodge = useCallback((dx: number, dy: number) => {
    const runtime = runtimeRef.current;

    if (runtime.dodgeCooldownMs > 0 || runtime.finished) {
      runtime.notice = "回避クールダウン中";
      setUiSnapshot(makeUiSnapshot(runtime));
      return;
    }

    const direction = screenDeltaToWorldDirection({ x: dx, y: dy });
    const start = runtime.playerPosition;
    const end = clampToCircle(addScaled(start, direction, DODGE_DISTANCE), FIELD_RADIUS - 0.45);
    runtime.dodge = {
      remainingMs: DODGE_DURATION_MS,
      start,
      end,
    };
    runtime.dodgeCooldownMs = DODGE_COOLDOWN_MS;
    runtime.dodgeInvulnerableMs = DODGE_INVULNERABLE_MS;
    runtime.movement = { x: 0, z: 0 };
    runtime.playerAngle = angleFromDirection(direction);
    runtime.notice = "フリック回避";
    setUiSnapshot(makeUiSnapshot(runtime));
  }, []);

  const useSkill = useCallback(
    (skillId: SkillId) => {
      const runtime = runtimeRef.current;
      const skill = SKILL_BY_ID[skillId];

      if (runtime.finished || !canUseSkill(runtime.cooldowns, skillId)) {
        return;
      }

      runtime.cooldowns = setSkillCooldown(runtime.cooldowns, skillId, skill.cooldownMs);
      dealBossDamage(
        getSkillDamageMultiplier(skillId),
        skill.range,
        skill.effectScale,
        skill.label,
        skillId === "breakArts",
      );
    },
    [dealBossDamage],
  );

  const changeAttribute = useCallback((attributeId: AttributeId) => {
    const runtime = runtimeRef.current;
    runtime.activeAttribute = attributeId;
    runtime.attackElement = getRuntimeAttackElement(runtime.equippedWeaponId, attributeId);
    runtime.defenseElement = getDefenseElement(attributeId);
    runtime.notice = `属性を${attributeId}に変更`;
    setUiSnapshot(makeUiSnapshot(runtime));
  }, []);

  const takePlayerDamage = useCallback((attackPower: number, label: string) => {
    const runtime = runtimeRef.current;
    const damageResult = calculateDamage({
      attackPower,
      defense: runtime.playerDefense,
      elementMultiplier: getElementMultiplier(runtime.bossAttribute, runtime.defenseElement),
      criticalMultiplier: 1,
    });
    const { nextHp, appliedDamage } = applyIncomingDamage(
      runtime.playerHp,
      damageResult.damage,
      runtime.playerMaxHp,
      runtime.dodgeInvulnerableMs > 0,
    );

    if (appliedDamage <= 0) {
      if (runtime.dodgeInvulnerableMs > 0) {
        runtime.dodgeSuccessCount += 1;
      }
      runtime.notice = `${label}: 回避成功`;
      return;
    }

    runtime.playerHp = nextHp;
    runtime.takenDamage += appliedDamage;
    runtime.notice = `${label}: ${appliedDamage}ダメージ`;

    const result = getBattleResult(runtime.playerHp, runtime.bossHp);

    if (result) {
      finishBattle(result);
    }
  }, [finishBattle]);

  useEffect(() => {
    const mount = mountRef.current;

    if (!mount) {
      return undefined;
    }

    const runtime = runtimeRef.current;
    const scene = createBattleScene(mount);
    sceneRef.current = scene;

    let animationFrame = 0;
    let lastTime = performance.now();

    const step = (deltaMs: number) => {
      if (runtime.finished) {
        return;
      }

      runtime.elapsedMs += deltaMs;
      runtime.attackCooldownMs = Math.max(0, runtime.attackCooldownMs - deltaMs);
      runtime.dodgeCooldownMs = Math.max(0, runtime.dodgeCooldownMs - deltaMs);
      runtime.dodgeInvulnerableMs = Math.max(0, runtime.dodgeInvulnerableMs - deltaMs);
      runtime.playerAttackMs = Math.max(0, runtime.playerAttackMs - deltaMs);
      runtime.cooldowns = tickCooldowns(runtime.cooldowns, deltaMs);
      runtime.bossHurtMs = Math.max(0, runtime.bossHurtMs - deltaMs);

      if (runtime.dodge) {
        runtime.dodge.remainingMs = Math.max(0, runtime.dodge.remainingMs - deltaMs);
        const progress = 1 - runtime.dodge.remainingMs / DODGE_DURATION_MS;
        const eased = smoothStep(progress);
        runtime.playerPosition = {
          x: runtime.dodge.start.x + (runtime.dodge.end.x - runtime.dodge.start.x) * eased,
          z: runtime.dodge.start.z + (runtime.dodge.end.z - runtime.dodge.start.z) * eased,
        };

        if (runtime.dodge.remainingMs <= 0) {
          runtime.playerPosition = runtime.dodge.end;
          runtime.dodge = null;
        }
      } else if (Math.hypot(runtime.movement.x, runtime.movement.z) > 0.01) {
        runtime.playerPosition = clampToCircle(
          addScaled(
            runtime.playerPosition,
            runtime.movement,
            runtime.playerSpeed * (deltaMs / 1000),
          ),
          FIELD_RADIUS - 0.45,
        );
        runtime.playerAngle = angleFromDirection(runtime.movement);
      }

      if (!runtime.shockwaveWarning) {
        runtime.shockwaveCountdownMs -= deltaMs;

        if (runtime.shockwaveCountdownMs <= 0) {
          runtime.shockwaveWarning = {
            ageMs: 0,
            durationMs: SHOCKWAVE_WARNING_MS,
          };
          runtime.shockwaveCountdownMs = SHOCKWAVE_INTERVAL_MS;
          runtime.notice = "ボス攻撃予告: 衝撃波";
        }
      } else {
        runtime.shockwaveWarning.ageMs += deltaMs;

        if (runtime.shockwaveWarning.ageMs >= runtime.shockwaveWarning.durationMs) {
          if (distance2d(runtime.playerPosition, runtime.bossPosition) <= SHOCKWAVE_RANGE) {
            takePlayerDamage(SHOCKWAVE_DAMAGE, "近距離衝撃波");
          }
          runtime.shockwaveWarning = null;
        }
      }

      if (!runtime.beamWarning) {
        runtime.beamCountdownMs -= deltaMs;

        if (runtime.beamCountdownMs <= 0) {
          runtime.beamWarning = {
            ageMs: 0,
            durationMs: BEAM_WARNING_MS,
            direction: normalize2d({
              x: runtime.playerPosition.x - runtime.bossPosition.x,
              z: runtime.playerPosition.z - runtime.bossPosition.z,
            }),
          };
          runtime.beamCountdownMs = BEAM_INTERVAL_MS;
          runtime.notice = "ボス攻撃予告: 直線攻撃";
        }
      } else {
        runtime.beamWarning.ageMs += deltaMs;

        if (runtime.beamWarning.ageMs >= runtime.beamWarning.durationMs) {
          if (
            pointLineDistance(
              runtime.playerPosition,
              runtime.bossPosition,
              runtime.beamWarning.direction,
            ) <= BEAM_WIDTH
          ) {
            takePlayerDamage(BEAM_DAMAGE, "直線攻撃");
          }
          runtime.beamWarning = null;
        }
      }

      runtime.syncAccumulatorMs += deltaMs;

      if (runtime.syncAccumulatorMs >= UI_SYNC_INTERVAL_MS) {
        runtime.syncAccumulatorMs = 0;
        setUiSnapshot(makeUiSnapshot(runtime));
      }
    };

    const animate = (time: number) => {
      const deltaMs = Math.min(time - lastTime, 50);
      lastTime = time;
      step(deltaMs);
      scene.update(makeSceneSnapshot(runtime), deltaMs);
      animationFrame = window.requestAnimationFrame(animate);
    };

    const handleResize = () => {
      scene.resize();
    };

    window.addEventListener("resize", handleResize);
    animationFrame = window.requestAnimationFrame(animate);

    return () => {
      window.cancelAnimationFrame(animationFrame);
      window.removeEventListener("resize", handleResize);
      scene.dispose();
      sceneRef.current = null;
    };
  }, [takePlayerDamage]);

  const handlePointerDown = (event: ReactPointerEvent<HTMLDivElement>) => {
    const isUiControl = isUiControlTarget(event.target);

    if (!shouldHandleCanvasPointer(isUiControl)) {
      return;
    }

    event.preventDefault();
    event.currentTarget.setPointerCapture(event.pointerId);
    const runtime = runtimeRef.current;
    runtime.pointer = {
      active: true,
      startX: event.clientX,
      startY: event.clientY,
      currentX: event.clientX,
      currentY: event.clientY,
      startAtMs: performance.now(),
    };
    runtime.movement = { x: 0, z: 0 };
  };

  const handlePointerMove = (event: ReactPointerEvent<HTMLDivElement>) => {
    const runtime = runtimeRef.current;

    if (!runtime.pointer.active) {
      return;
    }

    event.preventDefault();
    runtime.pointer.currentX = event.clientX;
    runtime.pointer.currentY = event.clientY;

    if (
      hasSwipeMovement(
        runtime.pointer.startX,
        runtime.pointer.startY,
        event.clientX,
        event.clientY,
      )
    ) {
      runtime.movement = screenDeltaToWorldDirection({
        x: event.clientX - runtime.pointer.startX,
        y: event.clientY - runtime.pointer.startY,
      });
    }
  };

  const endPointer = (event: ReactPointerEvent<HTMLDivElement>) => {
    const runtime = runtimeRef.current;

    if (!runtime.pointer.active) {
      return;
    }

    event.preventDefault();
    const gesture = classifyGesture({
      startX: runtime.pointer.startX,
      startY: runtime.pointer.startY,
      endX: event.clientX,
      endY: event.clientY,
      durationMs: performance.now() - runtime.pointer.startAtMs,
    });

    runtime.pointer.active = false;
    runtime.movement = { x: 0, z: 0 };

    if (gesture.kind === "flick") {
      startDodge(gesture.dx, gesture.dy);
    } else if (gesture.kind === "tap") {
      performAttack();
    }
  };

  const cancelPointer = (event: ReactPointerEvent<HTMLDivElement>) => {
    event.preventDefault();
    const runtime = runtimeRef.current;
    runtime.pointer.active = false;
    runtime.movement = { x: 0, z: 0 };
  };

  return (
    <main className="battle-screen">
      <div
        className="battle-stage"
        onPointerCancel={cancelPointer}
        onPointerDown={handlePointerDown}
        onPointerMove={handlePointerMove}
        onPointerUp={endPointer}
      >
        <div className="three-mount" ref={mountRef} />
        <BattleHud
          snapshot={uiSnapshot}
          onSkill={useSkill}
          onAttribute={changeAttribute}
        />
      </div>
    </main>
  );
}

