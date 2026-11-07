/**
 * Additive Standalone Demo Simulation Composable (`src/demo/useDemoSimulation.ts`).
 *
 * Purpose & Role:
 *   Non-intrusive, purely additive composable that attaches a client-side 50 Hz
 *   gait simulation loop to the dashboard when no physical robot backend is connected
 *   (e.g., static hosting on Plesk / GitHub Pages).
 *
 * Design:
 *   - Strictly additive: Has zero side-effects on core hardware stores or API contracts.
 *   - Completely dormant when `connectionStatus === 'Connected' | 'Live'`.
 *   - When disconnected, transparently calculates forward/inverse kinematics at 50 Hz
 *     from user inputs (D-Pad, keyboard, gamepad, attitude sliders) and streams joint angles
 *     to the Three.js 3D Digital Twin and 2D orthographic canvas views.
 *   - Respects single-joint inspection in the 'Legs' tab when stationary.
 */

import { watch, onMounted, onBeforeUnmount, type ShallowRef } from 'vue';
import type { useDashboardStore } from '../stores/dashboardStore';
import type { LasiusGraphicsEngine } from '../engine/lasiusGraphics';
import { DemoGaitEngine } from './demoGaitEngine';

export function useDemoSimulation(
  store: ReturnType<typeof useDashboardStore>,
  engineRef: ShallowRef<LasiusGraphicsEngine | null>
) {
  const demoEngine = new DemoGaitEngine(store.robotLayout);
  let simTimer: number | null = null;

  function isConnected(): boolean {
    return store.connectionStatus === 'Connected' || store.connectionStatus === 'Live';
  }

  function tickSimulation() {
    // 1. Yield to real robot telemetry when connected
    if (isConnected()) {
      return;
    }

    // 2. Respect pause state
    if (store.isPaused) {
      return;
    }

    // 3. If user is inspecting/calibrating individual joints in the Legs tab and robot is stationary,
    //    do not overwrite manual joint slider values
    const effectiveSpeed = Math.hypot(store.walkX, store.walkY, store.turnZ * 0.75);
    const isMoving = effectiveSpeed > 0.01;
    if (store.activeTab === 'legs' && !isMoving) {
      return;
    }

    // 4. Synchronize parameters from store
    demoEngine.walkX = store.walkX;
    demoEngine.walkY = store.walkY;
    demoEngine.turnZ = store.turnZ;
    demoEngine.gaitSpeed = store.gaitSpeed;
    demoEngine.stepHeight = store.gaitStepHeight;
    demoEngine.stepLength = store.gaitStepLength;
    demoEngine.setGait(store.currentGait);
    demoEngine.setPose(store.attitudeHeight, store.attitudeRoll, store.attitudePitch);

    // 5. Advance kinematics simulation tick (50 Hz)
    const angles = demoEngine.tick();

    // 6. Update 3D digital twin and reactive store state
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
