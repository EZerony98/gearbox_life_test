import unittest

from models.station_state import StationState


class StationStateTests(unittest.TestCase):
    def test_running_station_records_samples(self) -> None:
        state = StationState(1, "TEST-001", running=True)
        state.simulate_tick()
        self.assertEqual(state.sample_count, 1)
        self.assertGreater(state.realtime.speed_rpm, 0)
        self.assertEqual(len(state.history["minutes"]), 1)

    def test_warning_uses_temperature_limit(self) -> None:
        state = StationState(5, "TEST-005", running=True, demo_warning=True)
        state.parameters.temperature_high = 60.0
        state.simulate_tick()
        self.assertTrue(state.warning)

    def test_chart_history_is_compacted_but_samples_continue(self) -> None:
        state = StationState(1, "TEST-001", running=True)
        state.MAX_HISTORY_POINTS = 4
        for _ in range(12):
            state.simulate_tick()
        self.assertEqual(state.sample_count, 12)
        self.assertLessEqual(len(state.history["minutes"]), 4)


if __name__ == "__main__":
    unittest.main()
