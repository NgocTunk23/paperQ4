import json
import os
import tempfile
import unittest
from pathlib import Path

from scenario_config import load_scenario, normalize_scenario


class ScenarioConfigTests(unittest.TestCase):
    def test_load_scenario_with_defaults(self):
        sample = {
            "id": "area_school",
            "name": "Trường học",
            "area_types": ["school"],
            "flow": {"base_interval": 12.5},
            "road_closures": [
                {"road_id": "road_1", "start_time": 100, "end_time": 300}
            ],
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "scenario.json"
            path.write_text(json.dumps(sample), encoding="utf-8")
            scenario = load_scenario(path)

        self.assertEqual(scenario["id"], "area_school")
        self.assertEqual(scenario["area_types"], ["school"])
        self.assertEqual(scenario["flow"]["base_interval"], 12.5)
        self.assertEqual(scenario["road_closures"][0]["road_id"], "road_1")

    def test_normalize_scenario_filters_invalid_area_types(self):
        scenario = normalize_scenario(
            {
                "id": "demo",
                "area_types": ["school", "unknown"],
                "road_closures": [{"road_id": "r1", "reason": "accident"}],
            },
            Path("demo.json"),
        )
        self.assertEqual(scenario["area_types"], ["school"])
        self.assertEqual(scenario["road_closures"][0]["reason"], "accident")


if __name__ == "__main__":
    unittest.main()
