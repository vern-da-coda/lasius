"""
Unit & Integration Tests for Decentralized Walknet Ganglia & Local Reflexes (`test_walknet.py`).
"""

import math
import pytest

from lasius.core.config import load_config
from lasius.core.hardware import MockPWMDriver
from lasius.core.motion import (
    LegIdentifier,
    LegSensoryFeedback,
    LegState,
    WalknetConfig,
    WalknetGait,
)
from lasius.core.robot import Hexapod


class TestWalknetCoordinationAndReflexes:
    def test_static_stability_invariant_across_speeds(self):
        """
        Walknet must always maintain at least 3 grounded legs (static support polygon)
        and never lift contralateral neighbors simultaneously across slow and fast speeds.
        """
        for speed in (0.35, 0.8, 1.4):
            gait = WalknetGait(
                config=WalknetConfig(min_stance_legs=3, use_foot_switches=False),
                walk_y=1.0,
                gait_speed=speed,
            )
            swings_seen = set()
            for _ in range(250):
                coords = gait.tick()
                assert len(coords) == 6
                grounded = sum(1 for g in gait.ganglia.values() if g.is_grounded)
                assert grounded >= 3, f"Lost static stability at speed={speed}: grounded={grounded}"

                for leg_id, g in gait.ganglia.items():
                    if g.state == LegState.SWING:
                        swings_seen.add(leg_id)

            # All 6 legs must actively step during forward locomotion
            assert len(swings_seen) == 6, f"Only {len(swings_seen)} legs stepped at speed={speed}"

    def test_cruse_rule1_ipsilateral_inhibition(self):
        """
        Cruse Rule 1: While LEFT_FRONT is swinging, LEFT_MIDDLE must be inhibited
        from entering SWING under normal PEP urgency.
        """
        gait = WalknetGait(config=WalknetConfig(rule1_inhibit_ipsilateral=True))
        lf = gait.ganglia[LegIdentifier.LEFT_FRONT]
        lf.start_swing(target_xy=(230.0, 20.0), target_z=-80.0)
        assert not lf.is_grounded

        # Normal urgency (1.05) should be inhibited by swinging anterior neighbor
        assert gait._can_start_swing(LegIdentifier.LEFT_MIDDLE, urgency=1.05, grounded_count=5) is False
        # Unrelated contralateral rear leg may still swing safely
        assert gait._can_start_swing(LegIdentifier.RIGHT_REAR, urgency=1.05, grounded_count=5) is True

    def test_cruse_rule2_touchdown_facilitation(self):
        """
        Cruse Rule 2: Touchdown of LEFT_FRONT excites LEFT_MIDDLE by adding
        a positive PEP advance bonus (`pep_excite_bonus_mm > 0`).
        """
        gait = WalknetGait(config=WalknetConfig(rule2_excite_fraction=0.30), walk_y=1.0)
        lf = gait.ganglia[LegIdentifier.LEFT_FRONT]
        lf.start_swing(target_xy=(230.0, 20.0), target_z=-80.0)
        # Advance LF right to end of swing so it touches down on next tick
        lf.swing_phase = 0.99
        gait.tick()

        assert lf.is_grounded
        lm = gait.ganglia[LegIdentifier.LEFT_MIDDLE]
        assert lm.pep_excite_bonus_mm > 0.0

    def test_cruse_rule4_load_inhibition(self):
        """
        Cruse Rule 4: Heavy stance load on an adjacent leg delays neighbor liftoff.
        """
        gait = WalknetGait(config=WalknetConfig(rule4_load_threshold=0.60))
        gait.update_feedback({
            LegIdentifier.LEFT_FRONT: LegSensoryFeedback(foot_contact=True, load_estimate=0.85),
        })
        assert gait._can_start_swing(LegIdentifier.LEFT_MIDDLE, urgency=1.05, grounded_count=6) is False
        # Emergency excursion still overrides so leg doesn't snap workspace
        assert gait._can_start_swing(LegIdentifier.LEFT_MIDDLE, urgency=1.35, grounded_count=6) is True

    def test_elevator_reflex_triggers_recovery_and_extra_lift(self):
        """
        Local Elevator Reflex (AP 2): Obstruction (stall or high tracking error) during SWING
        must transition immediately to RECOVERY and vault higher than normal step_height.
        """
        cfg = WalknetConfig(
            step_height_mm=28.0,
            elevator_lift_mm=22.0,
            elevator_error_deg=8.0,
            use_foot_switches=False,
        )
        gait = WalknetGait(config=cfg, walk_y=1.0)
        lf = gait.ganglia[LegIdentifier.LEFT_FRONT]
        lf.start_swing(target_xy=(230.0, 20.0), target_z=-80.0)
        lf.swing_phase = 0.35

        # Inject obstacle stall / excessive tracking lag
        gait.update_feedback({
            LegIdentifier.LEFT_FRONT: LegSensoryFeedback(
                foot_contact=False, tracking_error_deg=12.5, is_stalled=True
            )
        })
        gait.tick()

        assert lf.state == LegState.RECOVERY
        assert lf.elevator_triggers == 1

        # Clear obstruction and observe recovery apex exceeding normal swing height (-80 + 28 = -52 mm)
        gait.update_feedback({
            LegIdentifier.LEFT_FRONT: LegSensoryFeedback(foot_contact=False, tracking_error_deg=1.0, is_stalled=False)
        })
        max_z = -999.0
        for _ in range(30):
            coords = gait.tick()
            max_z = max(max_z, coords[LegIdentifier.LEFT_FRONT][2])
            if lf.is_grounded:
                break

        assert max_z > -45.0, f"Expected elevated recovery vault > -45 mm, got {max_z:.1f} mm"
        assert lf.is_grounded

    def test_searching_reflex_probes_down_until_foot_contact(self):
        """
        Local Searching Reflex (AP 2): When `use_foot_switches=True` and the foot reaches
        the end of SWING without ground contact, it enters SEARCH and extends downward
        until the foot switch closes (locking into STANCE at the deeper Z).
        """
        cfg = WalknetConfig(
            body_height_mm=-80.0,
            use_foot_switches=True,
            search_speed_mm_s=100.0,
            max_search_z_mm=-120.0,
        )
        gait = WalknetGait(config=cfg, walk_y=1.0)
        lf = gait.ganglia[LegIdentifier.LEFT_FRONT]
        lf.start_swing(target_xy=(230.0, 20.0), target_z=-80.0)
        lf.swing_phase = 0.99

        # No contact at nominal touchdown -> enters SEARCH
        gait.update_feedback({
            LegIdentifier.LEFT_FRONT: LegSensoryFeedback(foot_contact=False)
        })
        gait.tick()
        assert lf.state == LegState.SEARCH
        assert lf.search_triggers == 1

        # Probe downward for 5 ticks (~10 mm deeper)
        for _ in range(5):
            gait.tick()
        assert lf.state == LegState.SEARCH
        assert lf.pos[2] < -88.0

        # Foot hits ground at deeper step!
        discovered_z = lf.pos[2]
        gait.update_feedback({
            LegIdentifier.LEFT_FRONT: LegSensoryFeedback(foot_contact=True)
        })
        gait.tick()
        assert lf.state == LegState.STANCE
        assert math.isclose(lf.stance_z, discovered_z, abs_tol=1e-3)

    def test_terrain_adaptive_belly_clearance(self):
        """Belly ToF obstacle detection automatically increases body clearance."""
        gait = WalknetGait(config=WalknetConfig(target_belly_clearance_m=0.085, max_clearance_boost_mm=30.0))
        z_nominal = gait._get_leg_stance_z(LegIdentifier.LEFT_MIDDLE)

        # Simulate rock protruding beneath belly at 55 mm distance
        for _ in range(15):
            gait.set_belly_tof_distance_m(0.055)
        z_raised = gait._get_leg_stance_z(LegIdentifier.LEFT_MIDDLE)

        assert z_raised < z_nominal - 20.0, f"Expected deeper stance Z for higher clearance: {z_raised} vs {z_nominal}"

    def test_hexapod_integration_with_closed_loop_walknet(self):
        """WalknetGait works as a drop-in GaitProtocol inside Hexapod with closed-loop feedback."""
        cfg = load_config(apply_overlay=False)
        drivers = {0x40: MockPWMDriver(), 0x42: MockPWMDriver()}
        robot = Hexapod(cfg, drivers)
        gait = WalknetGait(walk_y=1.0, use_foot_switches=False)
        robot.set_gait(gait, engage=True)

        for _ in range(25):
            robot.poll_telemetry(dt=0.02)
            robot.tick()

        diag = gait.get_diagnostics()
        assert diag["tick"] == 25
        assert diag["grounded_count"] >= 3
