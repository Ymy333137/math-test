"""Small, isolated regression checks for the transfer helper."""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).with_name("transfer.py")
KEY = "workbook_880:q1"


class TransferTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.pending = {"items": [{"question_id": "q1", "display_id": "P1-(1)",
                                   "display_label": "基础题 · 选择题 · P1-(1)",
                                   "page": 1, "record_order": 1, "error_level": "B"}]}
        self.record = {"records": [{**self.pending["items"][0],
                                    "section": "基础题", "question_type": "选择题",
                                    "target_score_tier": "120以下",
                                    "required_for_scores": ["120以下", "120+"],
                                    "mastery": 0.5, "performance_level": "合格",
                                    "question_md": "A question", "unit": "workbook_880",
                                    "curriculum_unit": "unit_unassigned"}], "history": []}
        self.schedule = {"buckets": {"2026-09-28": ["existing"]},
                         "daily_plans": {"2026-09-28": ["existing"]},
                         "release_buffer": {}, "backlog": [], "updated_at": "old"}
        self.save()

    def save(self):
        for name, value in (("workbook_880_unscheduled.json", self.pending),
                            ("880-record.json", self.record),
                            ("review_schedule.json", self.schedule)):
            (self.root / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    def run_helper(self, action, *extra):
        return subprocess.run([sys.executable, str(SCRIPT), action, "--root", str(self.root),
                               "--date", "2026-09-28", "--count", "1", *extra],
                              text=True, capture_output=True)

    def test_plan_apply_and_stale_token(self):
        planned = self.run_helper("plan")
        self.assertEqual(planned.returncode, 0, planned.stderr)
        token = json.loads(planned.stdout)["token"]
        applied = self.run_helper("apply", "--token", token)
        self.assertEqual(applied.returncode, 0, applied.stderr)
        pending = json.loads((self.root / "workbook_880_unscheduled.json").read_text())
        record = json.loads((self.root / "880-record.json").read_text())
        schedule = json.loads((self.root / "review_schedule.json").read_text())
        self.assertEqual(pending["items"], [])
        self.assertEqual(record["history"][0]["question_id"], "q1")
        self.assertEqual(record["records"], self.record["records"])
        self.assertEqual(schedule["buckets"]["2026-09-28"], [KEY, "existing"])
        self.assertEqual(schedule["daily_plans"]["2026-09-28"], [KEY, "existing"])
        self.assertNotEqual(self.run_helper("apply", "--token", token).returncode, 0)

    def test_rejects_scheduled_collision(self):
        self.schedule["backlog"].append(KEY)
        self.save()
        result = self.run_helper("plan")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Already scheduled", result.stderr)

    def test_rejects_changed_files_after_plan(self):
        token = json.loads(self.run_helper("plan").stdout)["token"]
        self.schedule["updated_at"] = "changed"
        self.save()
        result = self.run_helper("apply", "--token", token)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Stale", result.stderr)
        self.assertEqual(json.loads((self.root / "workbook_880_unscheduled.json").read_text())["items"],
                         self.pending["items"])

    def test_creates_new_date(self):
        self.schedule["buckets"] = {}
        self.schedule["daily_plans"] = {}
        self.save()
        token = json.loads(self.run_helper("plan").stdout)["token"]
        applied = self.run_helper("apply", "--token", token)
        self.assertEqual(applied.returncode, 0, applied.stderr)
        schedule = json.loads((self.root / "review_schedule.json").read_text())
        self.assertEqual(schedule["buckets"]["2026-09-28"], [KEY])

    def test_index_only_item_creates_metadata_not_problem_text(self):
        self.record["records"] = []
        self.save()
        planned = self.run_helper("plan")
        self.assertEqual(json.loads(planned.stdout)["metadata_records_to_create"], 1)
        applied = self.run_helper("apply", "--token", json.loads(planned.stdout)["token"])
        self.assertEqual(applied.returncode, 0, applied.stderr)
        record = json.loads((self.root / "880-record.json").read_text())["records"][0]
        self.assertEqual(record["question_md"], "### P1-(1)")
        self.assertEqual(record["error_level"], "B")


if __name__ == "__main__":
    unittest.main()
