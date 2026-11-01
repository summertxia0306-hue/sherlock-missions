"""Large private results must preserve recommendations and safe write reads."""
import base64
import hashlib
import json
import tempfile
import unittest
from unittest import mock
from pathlib import Path

from streamlit.testing.v1 import AppTest
from storage import progress


class LargeProgressReadTests(unittest.TestCase):
    def setUp(self):
        progress._cache.clear()
        progress._read_failures.clear()
        if hasattr(progress, "_read_errors"):
            progress._read_errors.clear()

    def fixture(self):
        rows = [{"course_id": prefix + f"4A-T1-W01-D{day:02}",
                 "student_id": "sherlock", "data_kind": "formal"}
                for prefix in ("L", "S") for day in range(1, 30)]
        rows.append({"course_id": "L4A-T1-W01-D30", "student_id": "sherlock",
                     "data_kind": "test", "padding": "x" * 1_050_000})
        for prefix in ("W", "S"):
            rows.extend({"course_id": prefix + f"01D{day}", "student_id": "sherlock",
                         "data_kind": "formal"} for day in range(39, 51))
        raw = json.dumps(rows).encode()
        sha = hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()
        metadata = {"encoding": "none", "content": "", "sha": sha, "size": len(raw)}
        blob = {"encoding": "base64", "content": base64.b64encode(raw).decode(), "sha": sha}
        return rows, metadata, blob

    def test_large_result_metadata_loads_the_same_immutable_blob(self):
        rows, metadata, blob = self.fixture()
        with mock.patch.object(progress, "_gh_conf", return_value=("token", "test/private")), \
                mock.patch.object(progress, "_gh_request", side_effect=[metadata, blob]) as get:
            actual, sha = progress._remote_read("results.json", [])
        self.assertEqual(rows, actual)
        self.assertEqual(metadata["sha"], sha)
        self.assertEqual("https://api.github.com/repos/test/private/git/blobs/" + sha, get.call_args.args[1])

    def test_large_result_still_appends_without_losing_prior_rows(self):
        rows, metadata, blob = self.fixture()
        result = {"course_id": "L4A-T1-W01-D30", "data_kind": "formal"}
        with mock.patch.object(progress, "_gh_conf", return_value=("token", "test/private")), \
                mock.patch.object(progress, "_gh_request", side_effect=[metadata, blob]), \
                mock.patch.object(progress, "_remote_write", return_value=True) as write:
            self.assertTrue(progress._remote_append_result(result))
        self.assertEqual(rows + [result], write.call_args.args[1])
        self.assertEqual(metadata["sha"], write.call_args.args[2])

    def test_cached_progress_survives_outage_but_cas_never_uses_stale_data(self):
        rows, metadata, blob = self.fixture()
        with mock.patch.object(progress, "_gh_conf", return_value=("token", "test/private")), \
                mock.patch.object(progress, "_gh_request", side_effect=[metadata, blob]):
            self.assertEqual(rows, progress._remote_read("results.json", [])[0])
        for key, (_expiry, data, sha) in list(progress._cache.items()):
            progress._cache[key] = (0, data, sha)
        with mock.patch.object(progress, "_gh_conf", return_value=("token", "test/private")), \
                mock.patch.object(progress, "_gh_request", side_effect=TimeoutError):
            self.assertEqual(rows, progress._remote_read("results.json", [])[0])
            self.assertEqual("stale", progress.completion_read_state())
            self.assertEqual((None, None), progress._remote_read("results.json", [], use_cache=False))
            self.assertEqual(rows, progress._remote_read("results.json", [])[0])

    def test_invalid_or_unavailable_blob_is_never_used_for_a_write(self):
        _rows, metadata, blob = self.fixture()
        invalid = dict(blob, content=base64.b64encode(b'[]').decode())
        for failure in (invalid, TimeoutError()):
            with self.subTest(failure=type(failure).__name__):
                self.setUp()
                with mock.patch.object(progress, "_gh_conf", return_value=("token", "test/private")), \
                        mock.patch.object(progress, "_gh_request", side_effect=[metadata, failure, metadata, failure]), \
                        mock.patch.object(progress, "_remote_write") as write:
                    self.assertEqual((None, None), progress._remote_read("results.json", []))
                    self.assertEqual("unavailable", progress.completion_read_state())
                    self.assertFalse(progress._remote_append_result({"data_kind": "test"}))
                    write.assert_not_called()

    def test_retry_keeps_last_good_snapshot_and_clears_only_completion_backoff(self):
        rows, metadata, blob = self.fixture()
        with mock.patch.object(progress, "_gh_conf", return_value=("token", "test/private")), \
                mock.patch.object(progress, "_gh_request", side_effect=[metadata, blob]):
            progress._remote_read("results.json", [])
        key = next(iter(progress._cache))
        progress._read_failures[key] = float("inf")
        progress._read_errors.add(key)
        with mock.patch.object(progress, "_gh_conf", return_value=("token", "test/private")):
            progress.retry_completion_reads()
            self.assertEqual(rows, progress._cache[key][1])
            self.assertEqual(0, progress._cache[key][0])
            self.assertNotIn(key, progress._read_failures)
            self.assertEqual("stale", progress.completion_read_state())

    def test_both_homes_keep_last_good_recommendation_during_outage(self):
        _rows, metadata, blob = self.fixture()
        for module, prefix in (("listening", "L"), ("speaking", "S")):
            with self.subTest(module=module), tempfile.TemporaryDirectory() as runtime:
                self.setUp()
                with mock.patch.object(progress, "_gh_conf", return_value=("token", "test/private")), \
                        mock.patch.object(progress, "_gh_request", side_effect=[metadata, blob,
                            {"content": base64.b64encode(b'[]').decode(), "sha": "optional"}]):
                    progress._remote_read("results.json", [])
                    progress._remote_read("completion_reconciliations.json", [])
                for key, (_expiry, data, sha) in list(progress._cache.items()):
                    progress._cache[key] = (0, data, sha)
                with mock.patch.dict("os.environ", {"SHERLOCK_RUNTIME_DIR": runtime,
                        "RESULTS_TOKEN": "token", "RESULTS_REPO": "test/private"}), \
                        mock.patch("urllib.request.urlopen", side_effect=TimeoutError):
                    app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / "app.py"), default_timeout=20)
                    app.query_params["module"] = module
                    app.run()
                    self.assertEqual(0, len(app.exception))
                    self.assertTrue(any("最近同步" in x.value for x in app.warning))
                    self.assertTrue(any(prefix + "4A-T1-W01-D30" in x.value for x in app.info))

    def test_failed_initial_read_hides_false_old_recommendations_on_both_homes(self):
        for module in ("listening", "speaking"):
            with self.subTest(module=module), tempfile.TemporaryDirectory() as runtime, \
                    mock.patch.dict("os.environ", {"SHERLOCK_RUNTIME_DIR": runtime,
                                                   "RESULTS_TOKEN": "token", "RESULTS_REPO": "test/private"}), \
                    mock.patch("urllib.request.urlopen", side_effect=TimeoutError):
                app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / "app.py"), default_timeout=20)
                app.query_params["module"] = module
                app.run()
                self.assertEqual(0, len(app.exception))
                self.assertTrue(app.warning)
                self.assertFalse(app.info)
                self.assertNotIn("未完成", " ".join(x.value for x in app.markdown))

    def test_large_result_recommends_term_day30_on_both_homes(self):
        rows, metadata, blob = self.fixture()
        def get(_method, url, _token, payload=None):
            if url.endswith("contents/results.json"):
                return metadata
            if "/git/blobs/" in url:
                return blob
            return {"content": base64.b64encode(b'[]' if "reconciliations" in url else b'{}').decode(), "sha": "optional"}
        def urlopen(request, data=None, timeout=None):
            obj = get("GET", request.full_url, "token")
            response = mock.MagicMock()
            response.__enter__.return_value.read.return_value = json.dumps(obj).encode()
            return response
        for module, prefix in (("listening", "L"), ("speaking", "S")):
            with self.subTest(module=module), tempfile.TemporaryDirectory() as runtime, \
                    mock.patch.dict("os.environ", {"SHERLOCK_RUNTIME_DIR": runtime,
                                                   "RESULTS_TOKEN": "token", "RESULTS_REPO": "test/private"}), \
                    mock.patch("urllib.request.urlopen", side_effect=urlopen):
                self.setUp()
                app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / "app.py"), default_timeout=20)
                app.query_params["module"] = module
                app.run()
                self.assertEqual(0, len(app.exception))
                self.assertTrue(any(prefix + "4A-T1-W01-D30" in x.value for x in app.info))
                self.assertFalse(any("01D39" in x.value for x in app.info))
                self.assertFalse((Path(runtime) / "results.json").exists())


if __name__ == "__main__":
    unittest.main()
