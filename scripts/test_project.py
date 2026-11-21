"""Regression checks for portable route planning and design history."""
import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import tempfile
import unittest

from project import check, history, record, relative_example, starter, write_new


SAMPLE = Path(__file__).resolve().parents[1] / "examples/weather-project/site-plan.json"


class ProjectTests(unittest.TestCase):
    def setUp(self):
        self.data = json.loads(SAMPLE.read_text(encoding="utf-8"))

    def test_one_family_can_serve_many_objects(self):
        self.data["routes"][2]["examples"] = [f"objects/{i}.html" for i in range(600)]
        self.assertEqual(check(self.data), ([], []))

    def test_repeated_composition_is_a_review_prompt(self):
        self.data["routes"][1]["composition"] = self.data["routes"][0]["composition"]
        errors, advice = check(self.data)
        self.assertFalse(errors)
        self.assertEqual(len(advice), 1)

    def test_journey_coverage_and_unknown_route(self):
        self.data["journeys"][-1]["through"] = ["missing-route"]
        errors, _ = check(self.data)
        self.assertTrue(any("unknown route" in s for s in errors))
        self.assertTrue(any("recovery: include" in s for s in errors))

    def test_safe_relative_paths(self):
        for bad in ("/elsewhere", "https://example.org/a", "../escape", "%2e%2e/escape", "//other/a", "#"):
            self.assertFalse(relative_example(bad), bad)
        for good in ("films/today.html?slot=2#evening", "archive/", "café.html", "shows/an%20evening.html"):
            self.assertTrue(relative_example(good), good)

    def test_file_check_under_root_and_missing_document(self):
        with tempfile.TemporaryDirectory() as directory:
            site = Path(directory)
            for row in self.data["routes"]:
                for link in row["examples"]:
                    filename = site / link.split("?")[0]
                    filename.parent.mkdir(parents=True, exist_ok=True)
                    filename.touch()
            self.assertEqual(check(self.data, site), ([], []))
            (site / "notes.html").unlink()
            self.assertIn("notes: missing local route notes.html", check(self.data, site)[0])

    def test_empty_plan_and_non_overwriting_init(self):
        self.assertTrue(check(starter())[0])
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "site-plan.json"
            write_new(path, {"version": 1})
            with self.assertRaises(FileExistsError):
                write_new(path, {})
            self.assertEqual(json.loads(path.read_text()), {"version": 1})

    def test_private_history_concurrent_and_separate(self):
        with tempfile.TemporaryDirectory() as first, tempfile.TemporaryDirectory() as other:
            workspace = Path(first)
            with ThreadPoolExecutor(max_workers=6) as workers:
                list(workers.map(lambda n: record(workspace, f"decision {n}", "specific to this site"), range(15)))
            self.assertEqual(len(history(workspace)), 15)
            self.assertEqual(history(Path(other)), [])
            with self.assertRaises(ValueError):
                record(workspace, "", "reason")


if __name__ == "__main__":
    unittest.main()
