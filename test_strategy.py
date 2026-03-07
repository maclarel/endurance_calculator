import unittest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from strategy import calculate_strategy


class TestCalculateStrategy(unittest.TestCase):
    """Unit tests for the pure-Python calculate_strategy function."""

    # ---- helpers -------------------------------------------------------

    def _stops(self, result):
        return [s for s in result if s['type'] == 'stop']

    def _finish(self, result):
        return next(s for s in result if s['type'] == 'finish')

    def _swap_stops(self, result):
        return [s for s in self._stops(result) if s['action'] == 'VE + TIRES']

    def _warning_stops(self, result):
        return [s for s in self._stops(result) if s['danger'] and s['action'] == 'VE ONLY']

    def _max_consecutive(self, actions, value):
        run = best = 0
        for a in actions:
            run = run + 1 if a == value else 0
            best = max(best, run)
        return best

    # ---- distribution tests --------------------------------------------

    def test_default_inputs_exact_tires(self):
        """32 total tires (28 in garage) with 22-lap tire life over 360 min.
        Expects exactly 7 swaps, alternating pattern, no warnings."""
        result = calculate_strategy(
            rem_mins=360, lap_time=125.0, e_per_lap=9.0, t_life=22,
            tires_in_garage=28,
        )
        swaps = self._swap_stops(result)
        warnings = self._warning_stops(result)
        self.assertEqual(len(swaps), 7, "Expected exactly 7 tire swaps")
        self.assertEqual(len(warnings), 0, "Expected no warnings")

        actions = [s['action'] for s in self._stops(result)]
        self.assertEqual(
            self._max_consecutive(actions, 'VE + TIRES'), 1,
            "Swaps must never be back-to-back",
        )

    def test_excess_tires_no_extra_swaps(self):
        """40 total tires (36 in garage) — should still plan exactly 7 swaps.
        Extra tires must not trigger unnecessary swap stops."""
        result = calculate_strategy(
            rem_mins=360, lap_time=125.0, e_per_lap=9.0, t_life=22,
            tires_in_garage=36,
        )
        swaps = self._swap_stops(result)
        finish = self._finish(result)
        self.assertEqual(len(swaps), 7, "Expected exactly 7 swaps even with excess tires")
        self.assertEqual(len(self._warning_stops(result)), 0, "Expected no warnings")
        self.assertGreater(finish['tires_remaining'], 0, "Excess tires should remain unused")

    def test_insufficient_tires_warnings_distributed(self):
        """24 total tires (20 in garage) → 5 available, 7 required.
        Warnings must be distributed through the race (not bunched at the end)
        and must not exceed 2 consecutive (minimum unavoidable with stints_per_set=2)."""
        result = calculate_strategy(
            rem_mins=360, lap_time=125.0, e_per_lap=9.0, t_life=22,
            tires_in_garage=20,
        )
        swaps = self._swap_stops(result)
        stops = self._stops(result)
        self.assertEqual(len(swaps), 5, "Expected exactly 5 swaps (inventory limited)")

        # Last stop must NOT be a warning — warnings must not all be at the end.
        last = stops[-1]
        self.assertFalse(
            last['danger'] and last['action'] == 'VE ONLY',
            "Last stop must not be a warning — warnings should be distributed",
        )

        # At most 2 consecutive warnings (back-to-back is unavoidable when
        # stints_per_set=2 and a required swap is skipped, but 3 in a row is not).
        actions = ['W' if (s['danger'] and s['action'] == 'VE ONLY') else 'O' for s in stops]
        self.assertLessEqual(
            self._max_consecutive(actions, 'W'), 2,
            "No more than 2 consecutive warnings when stints_per_set=2",
        )

    def test_tire_life_example_only_needed_swaps(self):
        """90-lap race at 60 s/lap, tire life 20 laps, 100 tires in garage.
        Only 4 swaps should be planned; many tires remain at the end."""
        # max_stint = floor(90/9) = 10 laps; 9 stops; limit = 20 * 1.15 = 23.0 laps;
        # stints_per_set = floor(23.0/10) = 2; required_positions = [1, 3, 5, 7];
        # planned = min(4, 25) = 4
        result = calculate_strategy(
            rem_mins=90, lap_time=60.0, e_per_lap=9.0, t_life=20,
            tires_in_garage=100, energy_cap=90.0,
        )
        swaps = self._swap_stops(result)
        finish = self._finish(result)
        self.assertEqual(len(swaps), 4, "Expected exactly 4 swaps for 90-lap / 20-lap-tire-life race")
        self.assertEqual(len(self._warning_stops(result)), 0, "Expected no warnings with ample tires")
        self.assertGreater(finish['tires_remaining'], 80, "Most tires should remain unused")

    def test_no_tires_available(self):
        """0 tires in garage → no swaps can occur."""
        result = calculate_strategy(
            rem_mins=360, lap_time=125.0, e_per_lap=9.0, t_life=22,
            tires_in_garage=0,
        )
        self.assertEqual(len(self._swap_stops(result)), 0, "No swaps with empty inventory")

    # ---- pit time tests ------------------------------------------------

    def test_pit_times_affect_display_only(self):
        """Pit stop times must show in display_secs but must not change the number
        of stops or lap counts — the loop is driven by driving time only."""
        result_fast = calculate_strategy(
            rem_mins=360, lap_time=125.0, e_per_lap=9.0, t_life=22,
            tires_in_garage=28, pit_energy_secs=1.0, pit_tires_secs=1.0,
        )
        result_slow = calculate_strategy(
            rem_mins=360, lap_time=125.0, e_per_lap=9.0, t_life=22,
            tires_in_garage=28, pit_energy_secs=600.0, pit_tires_secs=600.0,
        )

        self.assertEqual(len(result_fast), len(result_slow), "Pit time must not affect number of stops")

        for fast, slow in zip(result_fast, result_slow):
            self.assertEqual(fast['type'], slow['type'])
            if fast['type'] == 'stop':
                self.assertEqual(fast['lap'], slow['lap'])
                self.assertEqual(fast['action'], slow['action'])
                self.assertNotEqual(
                    fast['display_secs'], slow['display_secs'],
                    "display_secs must differ when pit times differ",
                )

    def test_default_pit_times_are_60_and_72(self):
        """Default pit times: 60 s for fuel-only, 72 s for fuel + tires."""
        result = calculate_strategy(
            rem_mins=360, lap_time=125.0, e_per_lap=9.0, t_life=22,
            tires_in_garage=28,
        )
        stops = self._stops(result)
        lap_contrib = 11 * 125.0  # max_stint_laps * lap_time = 1375 s

        for i, s in enumerate(stops):
            delta = s['display_secs'] if i == 0 else s['display_secs'] - stops[i - 1]['display_secs']
            pit_applied = delta - lap_contrib
            expected = 72.0 if s['action'] == 'VE + TIRES' else 60.0
            self.assertAlmostEqual(
                pit_applied, expected, places=1,
                msg=f"Stop {i}: expected pit time {expected}s for {s['action']}, got {pit_applied}s",
            )

    # ---- mode and miscellaneous tests ----------------------------------

    def test_strict_mode_same_swap_count(self):
        """With strict mode, limit = t_life exactly (no 15% margin).
        floor(22/11)=2 == floor(25.3/11)=2, so swap count is identical."""
        result_strict = calculate_strategy(
            rem_mins=360, lap_time=125.0, e_per_lap=9.0, t_life=22,
            tires_in_garage=28, strict=True,
        )
        result_normal = calculate_strategy(
            rem_mins=360, lap_time=125.0, e_per_lap=9.0, t_life=22,
            tires_in_garage=28, strict=False,
        )
        self.assertEqual(len(self._swap_stops(result_strict)), len(self._swap_stops(result_normal)))

    def test_finish_entry_present(self):
        """Result must always include a 'finish' entry."""
        result = calculate_strategy(
            rem_mins=360, lap_time=125.0, e_per_lap=9.0, t_life=22,
            tires_in_garage=28,
        )
        finish_entries = [s for s in result if s['type'] == 'finish']
        self.assertEqual(len(finish_entries), 1, "Expected exactly one finish entry")

    def test_energy_cap_guard(self):
        """energy_cap < e_per_lap must not raise (max_stint_laps is clamped to 1)."""
        try:
            calculate_strategy(
                rem_mins=60, lap_time=60.0, e_per_lap=9.0, t_life=10,
                tires_in_garage=20, energy_cap=5.0,
            )
        except ZeroDivisionError:
            self.fail("ZeroDivisionError raised when energy_cap < e_per_lap")


if __name__ == '__main__':
    unittest.main()
