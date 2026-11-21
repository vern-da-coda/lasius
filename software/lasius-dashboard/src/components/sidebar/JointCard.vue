<script setup lang="ts">
/**
 * Reusable Single-Joint Control & Closed-Loop Calibration Card (`lasius-dashboard/src/components/sidebar/JointCard.vue`).
 *
 * Purpose & Role:
 *   Encapsulates the UI and interaction logic for a single leg joint (`coxa`,
 *   `femur`, or `tibia`):
 *     - Live Angle Direct Drive Slider with integrated Closed-Loop feedback (AP 5):
 *       * Target position (`Soll` / `currentAngle`) controlled by the interactive slider thumb.
 *       * Actual position (`Ist` / `actualAngle`) rendered as a distinct visual marker
 *         and deviation bridge bar directly on the same slider rail within `[minLimit, maxLimit]`.
 *       * Simultaneous numerical badges for `Soll`, `Ist`, and deviation (`Δ°` / `STALL` alert),
 *         with clean dimmed Open-Loop fallback when no valid ADC feedback is present.
 *     - Dual-thumb min/max angle limit range slider, microsecond pulse center-trim steppers,
 *       orientation inversion toggle (`+1` / `-1`), and a joint range sweep button.
 */
import { computed } from 'vue';
import { useDashboardStore } from '../../stores/dashboardStore';
import type { JointName } from '../../types';

const props = defineProps<{
  jointType: JointName;
  title: string;
  subtitle: string;
}>();

const store = useDashboardStore();

const legNames = computed(() => store.getLegServoNames(store.selectedLegKey));
const servoName = computed(() => legNames.value[props.jointType]);

const servoData = computed(() => {
  return store.calibrationData[servoName.value] || {
    name: servoName.value,
    channel: '-',
    board_address: 0x40,
    center_offset_pulse: 0,
    orientation: 1,
    min_angle: props.jointType === 'tibia' ? -68 : (props.jointType === 'coxa' ? -25 : -90),
    max_angle: props.jointType === 'tibia' ? 29 : (props.jointType === 'coxa' ? 25 : 90),
    is_overridden: false
  };
});

// Commanded Target Angle (Soll)
const currentAngle = computed(() => {
  return store.jointAngles[servoName.value] !== undefined ? store.jointAngles[servoName.value] : 0;
});

// Measured Actual Angle (Ist) & Closed-Loop Validity
const isActualValid = computed(() => {
  return Boolean(
    store.actualJointValid[servoName.value] &&
    store.actualJointAngles[servoName.value] !== null &&
    store.actualJointAngles[servoName.value] !== undefined
  );
});

const actualAngle = computed<number | null>(() => {
  if (!isActualValid.value) return null;
  const val = store.actualJointAngles[servoName.value];
  return typeof val === 'number' ? val : null;
});

const angleDelta = computed<number>(() => {
  if (actualAngle.value === null) return 0;
  return actualAngle.value - currentAngle.value;
});

const isStalled = computed<boolean>(() => {
  return Boolean(store.jointStalled[servoName.value]);
});

const isWarningDeviation = computed<boolean>(() => {
  if (!isActualValid.value) return false;
  return isStalled.value || Math.abs(angleDelta.value) >= 5.0;
});

const formattedActualAngle = computed(() => {
  if (actualAngle.value === null) return '--';
  return actualAngle.value.toFixed(1);
});

const formattedDelta = computed(() => {
  const d = angleDelta.value;
  const sign = d > 0.05 ? '+' : '';
  return `${sign}${d.toFixed(1)}`;
});

const minLimit = computed(() => {
  return servoData.value.min_angle !== undefined
    ? servoData.value.min_angle
    : (props.jointType === 'tibia' ? -68 : (props.jointType === 'coxa' ? -25 : -90));
});

const maxLimit = computed(() => {
  return servoData.value.max_angle !== undefined
    ? servoData.value.max_angle
    : (props.jointType === 'tibia' ? 29 : (props.jointType === 'coxa' ? 25 : 90));
});

// Normalized [0..100] percentages along the Live Angle slider track [minLimit, maxLimit]
function angleToTrackPct(angleDeg: number): number {
  const span = maxLimit.value - minLimit.value;
  if (span <= 0) return 50;
  const raw = ((angleDeg - minLimit.value) / span) * 100;
  return Math.max(0, Math.min(100, raw));
}

const targetTrackPct = computed(() => angleToTrackPct(currentAngle.value));
const actualTrackPct = computed(() => {
  if (actualAngle.value === null) return targetTrackPct.value;
  return angleToTrackPct(actualAngle.value);
});

// Pixel-aligned left position accounting for the 15px range thumb width (7.5px half-thumb inset)
const actualMarkerStyle = computed(() => {
  const ratio = actualTrackPct.value / 100;
  return {
    left: `calc(7.5px + (100% - 15px) * ${ratio.toFixed(4)})`
  };
});

// Deviation bridge bar between Soll and Ist on the slider rail
const deltaBarStyle = computed(() => {
  const p1 = targetTrackPct.value / 100;
  const p2 = actualTrackPct.value / 100;
  const minR = Math.min(p1, p2);
  const spanR = Math.abs(p2 - p1);
  return {
    left: `calc(7.5px + (100% - 15px) * ${minR.toFixed(4)})`,
    width: `calc((100% - 15px) * ${spanR.toFixed(4)})`
  };
});

const centerTrim = computed(() => {
  return servoData.value.center_offset_pulse || 0;
});

const orientation = computed(() => {
  return servoData.value.orientation !== undefined ? servoData.value.orientation : 1;
});

const cleanSubtitle = computed(() => props.subtitle.replace(/^\(|\)$/g, '').trim());

const servoMetaText = computed(() => {
  const ch = servoData.value.channel !== undefined ? servoData.value.channel : '-';
  const addr = servoData.value.board_address ? ` @ 0x${servoData.value.board_address.toString(16)}` : '';
  return `${servoName.value} • Ch ${ch}${addr}`;
});

// Dual range percentage calculations
const leftPct = computed(() => {
  const totalMin = -90;
  const totalMax = 90;
  return Math.max(0, Math.min(100, ((minLimit.value - totalMin) / (totalMax - totalMin)) * 100));
});

const widthPct = computed(() => {
  const totalMin = -90;
  const totalMax = 90;
  const right = Math.max(0, Math.min(100, ((maxLimit.value - totalMin) / (totalMax - totalMin)) * 100));
  return Math.max(0, right - leftPct.value);
});

// Trim slider fill
const trimFillStyle = computed(() => {
  const maxBound = 600;
  const clamped = Math.max(-maxBound, Math.min(maxBound, centerTrim.value));
  const pct = (Math.abs(clamped) / maxBound) * 50;
  if (clamped >= 0) {
    return { left: '50%', width: `${pct}%` };
  } else {
    return { left: `${50 - pct}%`, width: `${pct}%` };
  }
});

const trimSign = computed(() => (centerTrim.value > 0 ? '+' : ''));
const degEst = computed(() => (centerTrim.value / 10.0).toFixed(1));

function handleAngleInput(e: Event) {
  const target = e.target as HTMLInputElement;
  const val = parseFloat(target.value);
  store.setJointAngle(servoName.value, val);
}

function handleMinLimitInput(e: Event) {
  const target = e.target as HTMLInputElement;
  let val = parseInt(target.value, 10);
  if (val >= maxLimit.value) {
    val = maxLimit.value - 1;
    target.value = val.toString();
  }
  store.applyLiveLimits(props.jointType, val, maxLimit.value);
}

function handleMaxLimitInput(e: Event) {
  const target = e.target as HTMLInputElement;
  let val = parseInt(target.value, 10);
  if (val <= minLimit.value) {
    val = minLimit.value + 1;
    target.value = val.toString();
  }
  store.applyLiveLimits(props.jointType, minLimit.value, val);
}

function handleTrimInput(e: Event) {
  const target = e.target as HTMLInputElement;
  let val = parseInt(target.value, 10);
  if (Math.abs(val) <= 2) val = 0;
  store.applyLiveTrimAbsolute(props.jointType, val, false);
}

function handleTrimChange(e: Event) {
  const target = e.target as HTMLInputElement;
  let val = parseInt(target.value, 10);
  if (Math.abs(val) <= 2) val = 0;
  store.applyLiveTrimAbsolute(props.jointType, val, true);
}

function nudgeTrim(step: number, e: MouseEvent) {
  const mult = e.shiftKey ? 10 : 1;
  store.applyLiveTrimStep(props.jointType, step * mult);
}

function resetTrim() {
  store.applyLiveTrimAbsolute(props.jointType, 0, true);
}

function handleOrientationToggle(e: Event) {
  const target = e.target as HTMLInputElement;
  store.applyLiveOrientation(props.jointType, target.checked);
}
</script>

<template>
  <div
    class="joint-control-card"
    :class="[`joint-${jointType}`, { 'joint-card-stalled': isStalled }]"
    @mouseenter="store.hoveredJoint = jointType"
    @mouseleave="if (store.hoveredJoint === jointType) store.hoveredJoint = null;"
  >
    <div class="joint-header">
      <div class="joint-title">
        <span>
          {{ title }}
          <span class="joint-sub" :id="`id-joint-${jointType}`">
            ({{ cleanSubtitle }} - {{ servoMetaText }})
          </span>
        </span>
      </div>
      <div class="joint-badges-row">
        <!-- Commanded Target Angle Badge (Soll) -->
        <span
          :id="`val-joint-${jointType}`"
          class="val-badge joint-badge"
          title="Commanded Target Angle (Soll)"
        >
          {{ Math.round(currentAngle) }}&deg;
        </span>

        <!-- Measured Actual Angle Badge (Ist / Open-Loop Fallback) -->
        <span
          :id="`val-actual-${jointType}`"
          class="val-badge joint-actual-badge"
          :class="{
            'open-loop': !isActualValid,
            'warn': isActualValid && isWarningDeviation && !isStalled,
            'stall': isStalled
          }"
          :title="isActualValid ? `Measured Potentiometer Angle (Ist: ${formattedActualAngle}°, Δ: ${formattedDelta}°)` : 'No valid ADC feedback (Open-Loop)'"
        >
          <template v-if="isActualValid">
            Ist {{ formattedActualAngle }}&deg;
          </template>
          <template v-else>
            Open-Loop
          </template>
        </span>

        <!-- Tracking Deviation / Stall Alert Badge -->
        <span
          v-if="isActualValid"
          :id="`val-delta-${jointType}`"
          class="val-badge joint-delta-badge"
          :class="{
            'ok': !isWarningDeviation && !isStalled,
            'warn': isWarningDeviation && !isStalled,
            'stall': isStalled
          }"
          :title="isStalled ? 'Persistent tracking deviation detected (Stall / Obstacle)' : 'Instantaneous deviation (Ist - Soll)'"
        >
          <template v-if="isStalled">
            ⚠ STALL ({{ formattedDelta }}&deg;)
          </template>
          <template v-else>
            &Delta; {{ formattedDelta }}&deg;
          </template>
        </span>
      </div>
    </div>

    <!-- Live Angle Direct Drive Slider with Integrated Closed-Loop Ist-Indicator -->
    <div class="joint-slider-wrap">
      <div class="slider-label-row">
        <span class="param-sublabel">Live Angle</span>
        <span class="slider-closed-loop-legend">
          <span class="legend-item" title="Commanded Target Position (Soll)">
            <span class="legend-dot soll"></span>Soll
          </span>
          <span
            class="legend-item"
            :class="{ 'is-open-loop': !isActualValid }"
            :title="isActualValid ? 'Measured Actual Position (ADS1115 Ist)' : 'Actual Feedback Inactive (Open-Loop)'"
          >
            <span
              class="legend-dot ist"
              :class="{ 'open-loop': !isActualValid, 'warn': isWarningDeviation, 'stall': isStalled }"
            ></span>Ist
          </span>
        </span>
      </div>

      <div class="joint-slider-track-container">
        <div class="joint-slider-rail"></div>

        <!-- Deviation Bridge Bar between Soll and Ist -->
        <div
          v-if="isActualValid"
          :id="`delta-bar-${jointType}`"
          class="joint-actual-delta-bar"
          :class="{ 'warn': isWarningDeviation && !isStalled, 'stall': isStalled }"
          :style="deltaBarStyle"
        ></div>

        <!-- Actual Angle (Ist) Indicator Marker on the Slider Track -->
        <div
          :id="`marker-actual-${jointType}`"
          class="joint-actual-marker"
          :class="{
            'open-loop': !isActualValid,
            'warn': isActualValid && isWarningDeviation && !isStalled,
            'stall': isStalled
          }"
          :style="actualMarkerStyle"
          :title="isActualValid ? `Ist: ${formattedActualAngle}° (Δ ${formattedDelta}°)` : 'Open-Loop (no valid ADC feedback)'"
        ></div>

        <!-- Interactive Target (Soll) Range Input -->
        <input
          type="range"
          class="joint-live-slider-input"
          :id="`slider-joint-${jointType}`"
          :min="minLimit"
          :max="maxLimit"
          step="1"
          :value="Math.round(currentAngle)"
          @input="handleAngleInput"
        />
      </div>

      <div class="slider-ticks">
        <span :id="`tick-min-${jointType}`">{{ minLimit }}&deg;</span>
        <span>0&deg;</span>
        <span :id="`tick-max-${jointType}`">{{ maxLimit > 0 ? '+' : '' }}{{ maxLimit }}&deg;</span>
      </div>
    </div>

    <!-- Dual-Thumb Angle Limits Slider -->
    <div class="dual-range-container">
      <div class="dual-range-labels">
        <span class="range-label-title">Angle Limits (Min / Max)</span>
        <div class="range-readout-wrap">
          <span class="range-label-val" :id="`lbl-min-${jointType}`">{{ minLimit }}&deg;</span>
          <span class="range-label-sep">to</span>
          <span class="range-label-val" :id="`lbl-max-${jointType}`">{{ maxLimit > 0 ? '+' : '' }}{{ maxLimit }}&deg;</span>
        </div>
      </div>
      <div class="dual-range-wrapper">
        <div class="dual-range-track"></div>
        <div class="dual-range-highlight" :id="`highlight-${jointType}`" :style="{ left: `${leftPct}%`, width: `${widthPct}%` }"></div>
        <input
          type="range"
          class="dual-range-input dual-range-min"
          :id="`range-min-${jointType}`"
          min="-90"
          max="90"
          step="1"
          :value="minLimit"
          @input="handleMinLimitInput"
          :aria-label="`${title} Min Angle Limit`"
        />
        <input
          type="range"
          class="dual-range-input dual-range-max"
          :id="`range-max-${jointType}`"
          min="-90"
          max="90"
          step="1"
          :value="maxLimit"
          @input="handleMaxLimitInput"
          :aria-label="`${title} Max Angle Limit`"
        />
      </div>
    </div>

    <!-- Center Trim Offset Slider & Fine Nudge -->
    <div class="calib-param-group">
      <div class="calib-param-label">
        <span>Center Trim</span>
        <button
          type="button"
          class="calib-val-readout trim-readout-btn"
          :id="`calib-val-trim-${jointType}`"
          @click="resetTrim"
          title="Click to reset trim to 0 µs"
        >
          {{ trimSign }}{{ centerTrim }} µs (~ {{ trimSign }}{{ degEst }}°)
        </button>
      </div>
      <div class="trim-slider-row">
        <button
          type="button"
          class="btn-trim-nudge"
          :data-joint="jointType"
          data-step="-1"
          @click="nudgeTrim(-1, $event)"
          title="Nudge -1 µs (Shift+Click: -10 µs)"
        >-1µs</button>
        <div class="trim-slider-track-wrap">
          <div class="trim-slider-track"></div>
          <div class="trim-slider-center-line"></div>
          <div class="trim-slider-fill" :id="`trim-fill-${jointType}`" :style="trimFillStyle"></div>
          <input
            type="range"
            class="trim-slider-input"
            :id="`slider-trim-${jointType}`"
            :data-joint="jointType"
            min="-600"
            max="600"
            step="5"
            :value="centerTrim"
            @input="handleTrimInput"
            @change="handleTrimChange"
            @dblclick="resetTrim"
            :aria-label="`Center Trim Offset ${title}`"
          />
        </div>
        <button
          type="button"
          class="btn-trim-nudge"
          :data-joint="jointType"
          data-step="+1"
          @click="nudgeTrim(1, $event)"
          title="Nudge +1 µs (Shift+Click: +10 µs)"
        >+1µs</button>
      </div>
    </div>

    <!-- Card Bottom Row: Invert & Sweep Test -->
    <div class="joint-card-footer">
      <label class="calib-toggle-label">
        <input
          type="checkbox"
          :id="`calib-invert-${jointType}`"
          class="calib-invert-chk"
          :data-joint="jointType"
          :checked="orientation === -1"
          @change="handleOrientationToggle"
        />
        <span class="calib-chk-custom"></span>
        <span class="calib-toggle-text" :id="`calib-invert-text-${jointType}`">
          {{ orientation === -1 ? 'Inverted (-1)' : 'Normal (+1)' }}
        </span>
      </label>
      <button
        type="button"
        class="btn btn-secondary btn-calib-sweep"
        :data-joint="jointType"
        @click="store.testJointRange(jointType)"
        title="Test motion range between calibrated limits"
      >
        Test Range
      </button>
    </div>
  </div>
</template>
