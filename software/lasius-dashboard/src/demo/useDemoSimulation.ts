/**
 * Additive Standalone Demo Simulation Composable (`src/demo/useDemoSimulation.ts`).
 *
 * Purpose & Role:
 *   Non-intrusive, purely additive composable that attaches a client-side 50 Hz
 *   gait & closed-loop servo physics simulation loop to the dashboard when no
 *   physical robot backend is connected (e.g., static demo hosting / GitHub Pages).
 *
 * Design:
 *   - Strictly additive: Has zero side-effects on core hardware stores or API contracts.
 *   - Completely dormant when `connectionStatus === 'Connected' | 'Live'`.
 *   - When disconnected, transparently calculates forward/inverse kinematics at 50 Hz
 *     from user inputs (D-Pad, keyboard, gamepad, attitude sliders) and streams joint angles
 *     to the Three.js 3D Digital Twin and 2D orthographic canvas views.
 *   - Also runs a first-order physical servo follower (`tau = 0.075 s`, `maxSpeed = 350 deg/s`)
 *     for `actualJointAngles` across all 18 joints so the closed-loop Soll/Ist slider
 *     indicators exhibit realistic transit lag both during walking gaits and manual slider drags.
 */

import { watch, onMounted, onBeforeUnmount, type ShallowRef } from 'vue';
import type { useDashboardStore } from '../stores/dashboardStore';
import type { LasiusGraphicsEngine } from '../engine/lasiusGraphics';
import { DemoGaitEngine } from './demoGaitEngine';

const DEMO_DT_S = 0.020;
const DEMO_TAU_LAG_S = 0.075;
const DEMO_MAX_SPEED_DEG_S = 350.0;

export function useDemoSimulation(
  store: ReturnType<typeof useDashboardStore>,
  engineRef: ShallowRef<LasiusGraphicsEngine | null>
) {
  const demoEngine = new DemoGaitEngine(store.robotLayout);
  let simTimer: number | null = null;

  function isConnected(): boolean {
    return store.connectionStatus === 'Connected' || store.connectionStatus === 'Live';
  }

  function stepActualServoFollower() {
    const alpha = 1.0 - Math.exp(-DEMO_DT_S / DEMO_TAU_LAG_S);
    const maxStep = DEMO_MAX_SPEED_DEG_S * DEMO_DT_S;

    for (const [servoName, targetDeg] of Object.entries(store.jointAngles)) {
      const prev = store.actualJointAngles[servoName];
      const cur = prev !== undefined && prev !== null ? prev : targetDeg;
      const idealStep = (targetDeg - cur) * alpha;
      const clampedStep = Math.max(-maxStep, Math.min(maxStep, idealStep));
      const next = Math.abs(targetDeg - (cur + clampedStep)) < 0.02 ? targetDeg : cur + clampedStep;

      store.actualJointAngles[servoName] = Number(next.toFixed(2));
      store.actualJointValid[servoName] = true;
      store.jointTrackingErrors[servoName] = 0.0;
      store.jointStalled[servoName] = false;
    }
  }

  function tickSimulation() {
    // 1. Yield to real robot telemetry when connected
    if (isConnected()) {
      return;
    }

    // 2. Always step the physical first-order actual-angle follower so manual slider
    //    changes in the Legs tab also show realistic physical servo follow behavior
    stepActualServoFollower();

    // 3. Respect pause state for gait progression
    if (store.isPaused) {
      return;
    }

    // 4. If user is inspecting/calibrating individual joints in the Legs tab and robot is stationary,
    //    do not overwrite manual joint slider values
    const effectiveSpeed = Math.hypot(store.walkX, store.walkY, store.turnZ * 0.75);
    const isMoving = effectiveSpeed > 0.01;
    if (store.activeTab === 'legs' && !isMoving) {
      return;
    }

    // 5. Synchronize parameters from store
    demoEngine.walkX = store.walkX;
    demoEngine.walkY = store.walkY;
    demoEngine.turnZ = store.turnZ;
    demoEngine.gaitSpeed = store.gaitSpeed;
    demoEngine.stepHeight = store.gaitStepHeight;
    demoEngine.stepLength = store.gaitStepLength;
    demoEngine.setGait(store.currentGait);
    demoEngine.setPose(store.attitudeHeight, store.attitudeRoll, store.attitudePitch);

    // 6. Advance kinematics simulation tick (50 Hz)
    const angles = demoEngine.tick();

    // 7. Update 3D digital twin and reactive store state
    Object.assign(store.jointAngles, angles);
    engineRef.value?.setJointAngles(angles);
  }

  // Update simulation geometry whenever robot layout updates
  watch(
    () => store.robotLayout,
    (layout) => {
      demoEngine.applyLayout(layout);
    },
    { deep: true }
  );

  onMounted(() => {
    // If starting in disconnected standalone mode, initialize robot in standing pose
    if (!isConnected()) {
      const initialAngles = demoEngine.getInitialStanceAngles();
      Object.assign(store.jointAngles, initialAngles);
      for (const [sName, deg] of Object.entries(initialAngles)) {
        store.actualJointAngles[sName] = Number(deg.toFixed(2));
        store.actualJointValid[sName] = true;
        store.jointTrackingErrors[sName] = 0.0;
        store.jointStalled[sName] = false;
      }
      engineRef.value?.setJointAngles(initialAngles);
    }

    // Start 50 Hz simulation interval (20 ms)
    simTimer = window.setInterval(tickSimulation, 20);
  });

  onBeforeUnmount(() => {
    if (simTimer !== null) {
      clearInterval(simTimer);
      simTimer = null;
    }
  });

  return {
    demoEngine,
    tickSimulation
  };
}
