# -*- coding: utf-8 -*-
import base64
import json
from pathlib import Path
import time
import unittest
from unittest import mock

from listening import audio as listening_audio
from listening import engine as listening_engine
from listening import models as listening_models
from listening import page as listening_page
from listening import results as listening_results
from speaking import engine as speaking_engine
from speaking import models as speaking_models
from speaking import page as speaking_page
from speaking import recorder


class _Response:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class RegressionTests(unittest.TestCase):
    def test_recorder_capture_failures_restore_a_tappable_microphone(self):
        html = (Path(recorder.__file__).parent / "frontend" / "index.html").read_text(
            encoding="utf-8"
        )
        self.assertIn("function recoverCaptureFailure(msg)", html)
        self.assertIn('recoverCaptureFailure("录音太短了，重新录一次吧")', html)
        self.assertIn('recoverCaptureFailure("好像没有录到声音，再点一次话筒重试', html)

    def test_recorder_uses_a_fresh_processed_stream_and_releases_it_before_review(self):
        html = (Path(recorder.__file__).parent / "frontend" / "index.html").read_text(
            encoding="utf-8"
        )
        self.assertIn("channelCount:1", html)
        self.assertIn("echoCancellation:true", html)
        self.assertIn("noiseSuppression:true", html)
        self.assertIn("autoGainControl:true", html)
        self.assertNotIn("健康流直接复用", html)
        stop_record = html.split("function stopRecord(){", 1)[1].split(
            "function encodeWav16k", 1
        )[0]
        self.assertIn("node.onaudioprocess=null", stop_record)
        self.assertIn("releaseStream();", stop_record)
        self.assertLess(stop_record.index("releaseStream();"), stop_record.index("var wav"))

    def test_limited_audio_uses_cdn_with_raw_fallback(self):
        path = "static/audio/listening/W01D39/q13.mp3"
        sources = listening_audio.audio_sources(path)
        self.assertEqual(2, len(sources))
        self.assertTrue(sources[0].startswith("https://cdn.jsdelivr.net/gh/"))
        self.assertTrue(sources[1].startswith("https://raw.githubusercontent.com/"))
        self.assertTrue(all("1f1e2ef175215128437df67d23d2707b3993993a" in source for source in sources))
        self.assertTrue(sources[0].endswith(path))
        self.assertTrue(sources[1].endswith(path))
        self.assertEqual(sources[0], listening_audio.audio_url(path))

    def test_all_course_json_files_still_validate(self):
        for path in listening_models.list_course_files():
            course = listening_models.load_course(
                path.rsplit("\\", 1)[-1].removesuffix(".json")
            )
            self.assertTrue(course["_questions"])
        for path in speaking_models.list_course_files():
            course = speaking_models.load_course(
                path.rsplit("\\", 1)[-1].removesuffix(".json")
            )
            self.assertTrue(course["questions"])

    def test_listening_scoring_and_correction_logic_are_unchanged(self):
        course = listening_models.load_course("W01D39")
        answers = {q["id"]: q["answer"] for q in course["_questions"]}
        result = listening_results.build_result(
            course, answers, {}, "sherlock", time.time() - 60, time.time()
        )
        self.assertEqual(100, result["score"])
        self.assertEqual("formal", result["data_kind"])
        first = course["_questions"][0]
        self.assertTrue(listening_engine.is_correct(first, first["answer"]))

    def test_speaking_result_keeps_first_last_best_and_each_take_stars(self):
        course = speaking_models.load_course("S01D39")
        qstates = {}
        for q in course["questions"]:
            qstates[q["id"]] = {
                "takes": [
                    {"total": 60, "is_rejected": False, "words": []},
                    {"total": 80, "is_rejected": False, "words": []},
                    {"total": 70, "is_rejected": False, "words": []},
                ],
                "recordings": [],
                "recording_records": [],
                "passed_by_safety": False,
            }
        result = speaking_engine.build_result(
            course, qstates, "sherlock", time.time() - 60
        )
        first = result["question_results"][0]
        self.assertEqual("formal", result["data_kind"])
        self.assertEqual(60, first["first_total"])
        self.assertEqual(70, first["last_total"])
        self.assertEqual(80, first["best_total"])
        self.assertEqual([2, 3, 2], first["take_stars"])

    def test_test_entry_identity_reaches_listening_result(self):
        course = listening_models.load_course("W01D39")
        state = {
            "result": None,
            "answers": {q["id"]: q["answer"] for q in course["_questions"]},
            "plays": {},
            "t0": time.time() - 60,
            "attempt": 1,
            "data_kind": "test",
        }
        listening_page._finish(course, state, "sherlock")
        self.assertEqual("test", state["result"]["data_kind"])

    def test_test_entry_identity_reaches_speaking_result_and_recordings(self):
        course = speaking_models.load_course("S01D39")
        qstates = {}
        for q in course["questions"]:
            qstates[q["id"]] = {
                "takes": [{"total": 80, "is_rejected": False, "words": []}],
                "recordings": ["recordings/S01D39/test.wav"],
                "recording_records": [{
                    "path": "recordings/S01D39/test.wav",
                    "data_kind": "test",
                }],
                "passed_by_safety": False,
            }
        state = {
            "result": None,
            "q": qstates,
            "t0": time.time() - 60,
            "attempt": 1,
            "data_kind": "test",
        }
        speaking_page._finish(course, state, "sherlock")
        self.assertEqual("test", state["result"]["data_kind"])
        self.assertEqual(
            "test",
            state["result"]["question_results"][0]["recording_records"][0]["data_kind"],
        )

    def test_recording_upload_still_writes_original_wav(self):
        secrets = {
            "RESULTS_TOKEN": "test-token",
            "RESULTS_REPO": "owner/private-results",
        }
        with mock.patch(
            "speaking.recorder.urllib.request.urlopen",
            return_value=_Response(),
        ) as urlopen:
            path, seconds = recorder.upload_recording(
                b"RIFF-test", "S01D39", 1, 1, secrets.get
            )
        self.assertTrue(path.startswith("recordings/S01D39/"))
        self.assertTrue(path.endswith("_q01_t1.wav"))
        self.assertGreaterEqual(seconds, 0)
        request = urlopen.call_args.args[0]
        self.assertEqual("PUT", request.method)
        self.assertIn("api.github.com/repos/owner/private-results/contents/", request.full_url)
        payload = json.loads(request.data.decode("utf-8"))
        self.assertEqual(b"RIFF-test", base64.b64decode(payload["content"]))


if __name__ == "__main__":
    unittest.main()
