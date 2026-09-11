# -*- coding: utf-8 -*-
import base64
import importlib
import json
import math
from pathlib import Path
import shutil
import struct
import subprocess
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
    @staticmethod
    def _wav_bytes(samples, sample_rate=16000):
        pcm = b"".join(struct.pack("<h", max(-32768, min(32767, int(v))))
                       for v in samples)
        data_size = len(pcm)
        return (b"RIFF" + struct.pack("<I", 36 + data_size) + b"WAVEfmt "
                + struct.pack("<IHHIIHH", 16, 1, 1, sample_rate,
                              sample_rate * 2, 2, 16)
                + b"data" + struct.pack("<I", data_size) + pcm)

    @staticmethod
    def _speech_like_frames(frame_count=24, frame_size=1365):
        samples = []
        for frame_index in range(frame_count):
            frequency = 170 + frame_index * 13
            samples.extend(
                int(7000 * math.sin(2 * math.pi * frequency * i / 16000))
                for i in range(frame_size)
            )
        return samples

    def test_recorder_capture_failures_restore_a_tappable_microphone(self):
        html = (Path(recorder.__file__).parent / "frontend" / "index.html").read_text(
            encoding="utf-8"
        )
        self.assertIn("function recoverCaptureFailure(msg)", html)
        self.assertIn('recoverCaptureFailure("录音太短了，重新录一次吧")', html)
        self.assertIn('recoverCaptureFailure("好像没有录到声音，再点一次话筒重试', html)

    def test_streamlit_hot_deploy_reloads_recorder_before_speaking_page(self):
        app_source = (Path(recorder.__file__).parents[1] / "app.py").read_text(
            encoding="utf-8"
        )
        self.assertIn("from speaking import recorder as srecorder", app_source)
        self.assertIn("srecorder = importlib.reload(srecorder)", app_source)
        self.assertLess(
            app_source.index("srecorder = importlib.reload(srecorder)"),
            app_source.index("spage = importlib.reload(spage)"),
        )

        # Reproduce the exact production failure: the long-lived Streamlit process
        # has an old recorder module while app.py/page.py have already hot-updated.
        from streamlit.testing.v1 import AppTest

        delattr(recorder, "validate_wav_integrity")
        try:
            app = AppTest.from_file(
                str(Path(recorder.__file__).parents[1] / "app.py"), default_timeout=20
            )
            app.query_params["course_id"] = "S4A-T1-W01-D15"
            app.run()
            self.assertEqual(0, len(app.exception))
            self.assertTrue(hasattr(recorder, "validate_wav_integrity"))
        finally:
            importlib.reload(recorder)

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

    def test_recorder_uses_media_recorder_primary_capture_and_integrity_guards(self):
        html = (Path(recorder.__file__).parent / "frontend" / "index.html").read_text(
            encoding="utf-8"
        )
        self.assertIn("new MediaRecorder", html)
        self.assertIn("decodeAudioData", html)
        self.assertIn("function startLegacyRecord()", html)
        self.assertIn("function closeAudioContext()", html)
        self.assertIn("function hasAlternatingSilentChunks(parts)", html)
        self.assertIn("function hasDuplicatedAudioFrames", html)

        primary = html.split("function startRecord(){", 1)[1].split(
            "function startLegacyRecord", 1
        )[0]
        self.assertIn("MediaRecorder", primary)
        self.assertNotIn("createScriptProcessor", primary)

        stop_record = html.split("function stopRecord(){", 1)[1].split(
            "function encodeWav16k", 1
        )[0]
        self.assertIn("finishNativeRecording", stop_record)
        self.assertIn("这次录音出现断续，已自动作废", stop_record)

    def test_wav_integrity_rejects_duplicated_scriptprocessor_frames(self):
        frame_size = 1365
        originals = self._speech_like_frames(frame_count=12, frame_size=frame_size)
        duplicated = []
        for offset in range(0, len(originals), frame_size):
            frame = originals[offset:offset + frame_size]
            duplicated.extend(frame)
            duplicated.extend(frame)
        verdict = recorder.validate_wav_integrity(self._wav_bytes(duplicated))
        self.assertFalse(verdict["ok"])
        self.assertEqual("duplicated_frames", verdict["reason"])

    def test_wav_integrity_accepts_continuous_speech_like_audio(self):
        samples = self._speech_like_frames(frame_count=24)
        verdict = recorder.validate_wav_integrity(self._wav_bytes(samples))
        self.assertTrue(verdict["ok"], verdict)

    def test_wav_integrity_rejects_offset_alternating_silence(self):
        frame_size = 1365
        voiced = self._speech_like_frames(frame_count=1, frame_size=frame_size)
        samples = voiced[:frame_size // 2]
        for _ in range(8):
            samples.extend([0] * frame_size)
            samples.extend(voiced)
        verdict = recorder.validate_wav_integrity(self._wav_bytes(samples))
        self.assertFalse(verdict["ok"])
        self.assertEqual("alternating_silence", verdict["reason"])

    def test_wav_integrity_rejects_malformed_short_and_silent_audio(self):
        self.assertEqual(
            "invalid_wav", recorder.validate_wav_integrity(b"not a wav")["reason"]
        )
        self.assertEqual(
            "too_short",
            recorder.validate_wav_integrity(self._wav_bytes([1200] * 1000))["reason"],
        )
        self.assertEqual(
            "silent",
            recorder.validate_wav_integrity(self._wav_bytes([0] * 8000))["reason"],
        )

    def test_browser_integrity_detectors_execute_against_known_patterns(self):
        node = shutil.which("node")
        if not node:
            self.skipTest("Node.js is unavailable; browser detector behavior not executable")
        html = (Path(recorder.__file__).parent / "frontend" / "index.html").read_text(
            encoding="utf-8"
        )
        detector_source = "function frameCorrelation" + html.split(
            "function frameCorrelation", 1
        )[1].split("function hasAlternatingSilentChunks", 1)[0]
        script = detector_source + r"""
function speechFrame(index, size) {
  var frame = new Float32Array(size), frequency = 170 + index * 13;
  for (var i = 0; i < size; i++) frame[i] = 0.22 * Math.sin(2 * Math.PI * frequency * i / 16000);
  return frame;
}
function joinFrames(frames) {
  var length = frames.reduce(function(total, frame){ return total + frame.length; }, 0);
  var output = new Float32Array(length), offset = 0;
  frames.forEach(function(frame){ output.set(frame, offset); offset += frame.length; });
  return output;
}
var size = 1365, normal = [], duplicated = [];
for (var index = 0; index < 24; index++) normal.push(speechFrame(index, size));
for (var pair = 0; pair < 12; pair++) {
  var frame = speechFrame(pair, size); duplicated.push(frame, frame);
}
var voiced = speechFrame(0, size), alternating = [voiced.slice(0, Math.floor(size / 2))];
for (var run = 0; run < 8; run++) alternating.push(new Float32Array(size), voiced);
if (hasDuplicatedAudioFrames(joinFrames(normal), 16000)) throw new Error("normal audio rejected");
if (!hasDuplicatedAudioFrames(joinFrames(duplicated), 16000)) throw new Error("duplicate pattern missed");
if (!hasAlternatingSilentSamples(joinFrames(alternating), 16000)) throw new Error("alternating silence missed");
"""
        result = subprocess.run(
            [node, "-"], input=script, text=True, capture_output=True, check=False
        )
        self.assertEqual(0, result.returncode, result.stderr)

    def test_invalid_capture_never_reaches_scoring_or_upload(self):
        rv = {"wav_b64": base64.b64encode(self._wav_bytes([1000] * 8000)).decode(),
              "dur": 0.5, "take": 1}
        state = {"data_kind": "formal"}
        qstate = {"takes": [], "recordings": [], "recording_records": []}
        course = {"course_id": "S4A-T1-W01-D05"}
        question = {"id": 6, "type": "repeat", "text": "hello"}
        with mock.patch("speaking.page.recorder.validate_wav_integrity",
                        return_value={"ok": False, "reason": "duplicated_frames"}), \
             mock.patch("speaking.page.ise.evaluate_retry") as evaluate, \
             mock.patch("speaking.page.recorder.upload_recording") as upload:
            accepted = speaking_page._consume_take(
                course, question, qstate, rv, state
            )
        self.assertFalse(accepted)
        self.assertEqual([], qstate["takes"])
        self.assertIn("capture_error", state)
        self.assertEqual(1, state["capture_gen"][6])
        evaluate.assert_not_called()
        upload.assert_not_called()

    def test_valid_capture_completes_the_formal_scoring_path(self):
        wav = self._wav_bytes(self._speech_like_frames(frame_count=12))
        rv = {"wav_b64": base64.b64encode(wav).decode(), "dur": 1.0, "take": 1}
        state = {"data_kind": "formal"}
        qstate = {"takes": [], "recordings": [], "recording_records": []}
        course = {"course_id": "S4A-T1-W01-D15"}
        question = {"id": 1, "type": "repeat", "text": "hello"}
        score = {
            "total": 82,
            "accuracy": 82,
            "fluency": 82,
            "integrity": 82,
            "standard": 82,
            "is_rejected": False,
            "words": [],
            "raw_xml": "",
            "seconds": 1.0,
        }
        with mock.patch("speaking.page._secret", return_value="test-secret"), \
             mock.patch("speaking.page.ise.evaluate_retry", return_value=score) as evaluate, \
             mock.patch("speaking.page.recorder.upload_recording",
                        return_value=("recordings/test.wav", 0.1)) as upload, \
             mock.patch("speaking.page.progress.save_recording_identity") as save_identity:
            accepted = speaking_page._consume_take(
                course, question, qstate, rv, state
            )
        self.assertTrue(accepted)
        self.assertEqual(82, qstate["takes"][0]["total"])
        self.assertEqual(["recordings/test.wav"], qstate["recordings"])
        evaluate.assert_called_once()
        upload.assert_called_once()
        save_identity.assert_called_once_with(
            "recordings/test.wav", "formal", "S4A-T1-W01-D15", 1
        )

    def test_limited_audio_uses_cdn_with_raw_fallback(self):
        path = "static/audio/listening/W01D39/q13.mp3"
        sources = listening_audio.audio_sources(path)
        self.assertEqual(2, len(sources))
        self.assertTrue(sources[0].startswith("https://cdn.jsdelivr.net/gh/"))
        self.assertTrue(sources[1].startswith("https://raw.githubusercontent.com/"))
        self.assertTrue(all("b5dbb07aadf6a4e43ee8dc9f281a596ae8ed5543" in source for source in sources))
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
