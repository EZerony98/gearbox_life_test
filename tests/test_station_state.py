import unittest

from models.station_state import StationState


def plc_snapshot(**overrides: object) -> dict:
    snapshot = {
        "enabled": True,
        "running": True,
        "elapsed_seconds": 1,
        "speed_rpm": 1480.0,
        "current_a": 1.92,
        "pressure": 112.4,
        "torque_nm": 3.96,
        "temperature_1": 41.2,
        "temperature_2": 39.8,
        "temperature_3": 38.6,
        "parameters": {
            "speed_rpm": 1500,
            "torque_target": 4.0,
            "pressure_compensation": 0.0,
            "temperature_high": 85.0,
            "temperature_low": 5.0,
        },
    }
    snapshot.update(overrides)
    return snapshot


class StationStateTests(unittest.TestCase):
    def test_real_plc_snapshot_records_sample(self) -> None:
        state = StationState(1, "TEST-001")
        state.apply_plc_snapshot(plc_snapshot())
        self.assertTrue(state.connected)
        self.assertEqual(state.sample_count, 1)
        self.assertEqual(state.realtime.speed_rpm, 1480.0)
        self.assertEqual(len(state.history["minutes"]), 1)

    def test_warning_uses_temperature_limit(self) -> None:
        state = StationState(5, "TEST-005")
        state.apply_plc_snapshot(plc_snapshot(temperature_1=90.0))
        self.assertTrue(state.warning)

    def test_disconnection_clears_running_state(self) -> None:
        state = StationState(1, "TEST-001")
        state.apply_plc_snapshot(plc_snapshot())
        state.mark_disconnected()
        self.assertFalse(state.connected)
        self.assertFalse(state.running)
        self.assertEqual(state.status_text, "PLC 未连接")

    def test_chart_history_is_compacted_but_samples_continue(self) -> None:
        state = StationState(1, "TEST-001")
        state.MAX_HISTORY_POINTS = 4
        for second in range(1, 13):
            state.apply_plc_snapshot(plc_snapshot(elapsed_seconds=second))
        self.assertEqual(state.sample_count, 12)
        self.assertLessEqual(len(state.history["minutes"]), 4)


if __name__ == "__main__":
    unittest.main()
