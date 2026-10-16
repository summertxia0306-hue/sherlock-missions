"""Private speaking drafts remain ordered without blocking child navigation."""
import threading
import time
import unittest
from unittest import mock

from storage import checkpoint_jobs, progress


class SpeakingCheckpointQueueTests(unittest.TestCase):
    def test_failed_private_sync_is_visible_and_next_save_can_recover(self):
        key = "test-lesson-retry"
        checkpoint_jobs.submit(key, {"idx": 6}, lambda _item: False)
        deadline = time.monotonic() + 2
        while checkpoint_jobs.status(key) == "pending" and time.monotonic() < deadline:
            time.sleep(0.01)
        self.assertEqual("failed", checkpoint_jobs.status(key))
        checkpoint_jobs.submit(key, {"idx": 7}, lambda _item: True)
        deadline = time.monotonic() + 2
        while checkpoint_jobs.status(key) == "pending" and time.monotonic() < deadline:
            time.sleep(0.01)
        self.assertEqual("synced", checkpoint_jobs.status(key))

    def test_newer_question_waits_behind_current_write_then_becomes_latest(self):
        key = "test-lesson-coalescing"
        entered = threading.Event()
        release = threading.Event()
        calls = []

        def writer(item):
            calls.append(item["idx"])
            if item["idx"] == 6:
                entered.set()
                release.wait(2)
            return True

        checkpoint_jobs.submit(key, {"idx": 6}, writer)
        self.assertTrue(entered.wait(1))
        checkpoint_jobs.submit(key, {"idx": 7}, writer)
        release.set()
        deadline = time.monotonic() + 2
        while checkpoint_jobs.status(key) == "pending" and time.monotonic() < deadline:
            time.sleep(0.01)
        self.assertEqual([6, 7], calls)
        self.assertEqual("synced", checkpoint_jobs.status(key))

    def test_newer_remote_snapshot_is_never_overwritten(self):
        older = {"attempt": 1, "idx": 6, "q": {"7": {"takes": []}}}
        newer = {"attempt": 1, "idx": 7, "q": {"7": {"takes": [{}]}}}
        import base64
        import json
        remote_reply = {"content": base64.b64encode(
            json.dumps(newer).encode("utf-8")).decode("ascii"), "sha": "new-sha"}
        with mock.patch.object(progress, "_gh_request", return_value=remote_reply) as request:
            self.assertTrue(progress._sync_remote_speaking_checkpoint(
                "drafts/speaking/test.json", older, "token", "private/repo"))
        request.assert_called_once()
        self.assertEqual("GET", request.call_args.args[0])

    def test_same_question_more_takes_ranks_ahead_of_old_draft(self):
        one = {"attempt": 1, "idx": 6, "q": {"7": {"takes": [{}]}}}
        two = {"attempt": 1, "idx": 6, "q": {"7": {"takes": [{}, {}]}}}
        self.assertLess(progress._checkpoint_rank(one), progress._checkpoint_rank(two))


if __name__ == "__main__":
    unittest.main()
