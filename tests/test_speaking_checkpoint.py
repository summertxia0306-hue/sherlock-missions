"""An interrupted long speaking lesson must resume without writing a result."""
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from speaking import models
from speaking import checkpoint
from storage import progress


class SpeakingCheckpointTests(unittest.TestCase):
    def test_snapshot_round_trip_at_question_nine_for_every_long_course(self):
        for course_id, meta in models.all_courses().items():
            if meta.get("publication_status") != "formal" or meta["status"] != "open":
                continue
            course = models.load_course(course_id)
            if len(course["questions"]) < 10:
                continue
            with self.subTest(course_id=course_id):
                state = {
                    "idx": 8, "attempt": 1, "t0": 1000.0, "submitted": False,
                    "q": {qid: {
                        "takes": [{"total": 85, "is_rejected": False, "words": []}],
                        "recordings": [], "recording_records": [], "done": True,
                    } for qid in range(1, 9)},
                }
                snap = checkpoint.snapshot(course, state)
                restored = checkpoint.restore(course, snap)
                self.assertEqual(8, restored["idx"])
                self.assertEqual(set(range(1, 9)), set(restored["q"]))
                self.assertEqual(8, sum(bool(q["done"]) for q in restored["q"].values()))

    def test_course_revision_mismatch_never_applies_old_answers(self):
        course = models.load_course("S4A-T1-W01-D28")
        snap = checkpoint.snapshot(course, {"idx": 8, "attempt": 1,
                                            "t0": 1000.0, "q": {}, "submitted": False})
        modified = dict(course)
        modified["questions"] = [dict(q) for q in course["questions"]]
        modified["questions"][8]["expected"] = "Changed answer."
        self.assertIsNone(checkpoint.restore(modified, snap))

    def test_private_checkpoint_keeps_test_and_formal_separate(self):
        course = models.load_course("S4A-T1-W01-D28")
        payload = checkpoint.snapshot(course, {"idx": 8, "attempt": 1,
                                               "t0": 1000.0, "q": {}, "submitted": False})
        with tempfile.TemporaryDirectory() as directory, \
                mock.patch.object(progress, "_runtime_dir", return_value=directory), \
                mock.patch.object(progress, "_gh_conf", return_value=(None, None)):
            progress.save_speaking_checkpoint("sherlock", course["course_id"],
                                              "formal", payload)
            self.assertEqual(payload, progress.load_speaking_checkpoint(
                "sherlock", course["course_id"], "formal"))
            self.assertIsNone(progress.load_speaking_checkpoint(
                "sherlock", course["course_id"], "test"))
            self.assertEqual([], list(Path(directory).glob("results.json")))

    def test_private_remote_failure_keeps_local_draft_without_forging_result(self):
        course = models.load_course("S4A-T1-W01-D23")
        payload = checkpoint.snapshot(course, {"idx": 0, "attempt": 1,
                                               "t0": 1000.0, "q": {}, "submitted": False})
        with tempfile.TemporaryDirectory() as directory, \
                mock.patch.object(progress, "_runtime_dir", return_value=directory), \
                mock.patch.object(progress, "_gh_conf", return_value=("token", "private/repo")), \
                mock.patch.object(progress, "_remote_read", return_value=(None, None)):
            self.assertFalse(progress.save_speaking_checkpoint(
                "sherlock", course["course_id"], "formal", payload))
            self.assertEqual(payload, progress.load_speaking_checkpoint(
                "sherlock", course["course_id"], "formal"))
            self.assertFalse((Path(directory) / "results.json").exists())

    def test_private_remote_success_writes_draft_only(self):
        course = models.load_course("S4A-T1-W01-D23")
        payload = checkpoint.snapshot(course, {"idx": 0, "attempt": 1,
                                               "t0": 1000.0, "q": {}, "submitted": False})
        with tempfile.TemporaryDirectory() as directory, \
                mock.patch.object(progress, "_runtime_dir", return_value=directory), \
                mock.patch.object(progress, "_gh_conf", return_value=("token", "private/repo")), \
                mock.patch.object(progress, "_remote_read", return_value=({}, None)), \
                mock.patch.object(progress, "_remote_write", return_value=True) as write:
            self.assertTrue(progress.save_speaking_checkpoint(
                "sherlock", course["course_id"], "formal", payload))
            remote_path, remote_payload, sha = write.call_args.args
            self.assertTrue(remote_path.startswith("drafts/speaking/"))
            self.assertEqual(payload, remote_payload)
            self.assertIsNone(sha)
            self.assertFalse((Path(directory) / "results.json").exists())

    def test_private_remote_uses_opaque_name_and_rejects_path_injection(self):
        local, remote = progress._speaking_checkpoint_names(
            "sherlock", "S4A-T1-W01-D23", "formal")
        self.assertNotIn("sherlock", remote)
        self.assertNotIn("D23", remote)
        self.assertTrue(local.startswith("speaking_checkpoint_"))
        with self.assertRaises(ValueError):
            progress._speaking_checkpoint_names("../student", "../bad", "formal")


if __name__ == "__main__":
    unittest.main()
