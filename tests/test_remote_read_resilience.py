"""A slow private host must not turn one rerun into dozens of network reads."""
import base64
import importlib
import json
import unittest
from unittest import mock

from speaking import models
from storage import progress


class RemoteReadResilienceTests(unittest.TestCase):
    def setUp(self):
        progress._cache.clear()
        if hasattr(progress, "_read_failures"):
            progress._read_failures.clear()

    def test_successful_cache_survives_streamlit_module_reload(self):
        data = {"course": "open"}
        with mock.patch.object(progress, "_gh_conf", return_value=("token", "test/cache")), \
                mock.patch.object(progress, "_gh_request", return_value={
                    "content": base64.b64encode(json.dumps(data).encode()).decode(),
                    "sha": "version",
                }):
            self.assertEqual(data, progress._remote_read("course_status.json", {})[0])
        importlib.reload(progress)
        with mock.patch.object(progress, "_gh_conf", return_value=("token", "test/cache")), \
                mock.patch.object(progress, "_gh_request", side_effect=AssertionError("unneeded GET")):
            self.assertEqual(data, progress._remote_read("course_status.json", {})[0])

    def test_failed_reads_have_short_backoff_but_fresh_writes_can_still_read(self):
        with mock.patch.object(progress, "_gh_conf", return_value=("token", "test/failure")), \
                mock.patch.object(progress, "_gh_request", side_effect=TimeoutError) as request:
            for _ in range(20):
                self.assertEqual((None, None), progress._remote_read("results.json", []))
            self.assertEqual(1, request.call_count)
            progress._remote_read("results.json", [], use_cache=False)
            self.assertEqual(2, request.call_count)

    def test_speaking_catalog_takes_one_status_snapshot_even_during_outage(self):
        with mock.patch.object(progress, "_gh_conf", return_value=("token", "test/catalog")), \
                mock.patch.object(progress, "_gh_request", side_effect=TimeoutError) as request:
            self.assertGreater(len(models.all_courses()), 30)
            self.assertEqual(1, request.call_count)

    def test_cache_does_not_cross_private_repositories(self):
        response = {"content": base64.b64encode(b'["private-one"]').decode(), "sha": "one"}
        with mock.patch.object(progress, "_gh_conf", return_value=("token", "test/one")), \
                mock.patch.object(progress, "_gh_request", return_value=response):
            progress._remote_read("results.json", [])
        with mock.patch.object(progress, "_gh_conf", return_value=("token", "test/two")), \
                mock.patch.object(progress, "_gh_request", side_effect=TimeoutError):
            self.assertEqual((None, None), progress._remote_read("results.json", []))


if __name__ == "__main__":
    unittest.main()
