# -*- coding: utf-8 -*-
import json
import os
import tempfile
import unittest
from unittest import mock

from speaking import recorder
from storage import progress


class DataKindTests(unittest.TestCase):
    def test_legacy_result_is_exposed_as_test_without_rewriting_source(self):
        legacy = [{"course_id": "W01D01", "student_id": "sherlock", "score": 90}]
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "results.json")
            with open(path, "w", encoding="utf-8") as fh:
                json.dump(legacy, fh, ensure_ascii=False)

            with mock.patch.object(progress, "_runtime_dir", return_value=tmp), \
                    mock.patch.object(progress, "persistence_enabled", return_value=False):
                rows = progress.list_results()

            self.assertEqual("test", rows[0]["data_kind"])
            with open(path, encoding="utf-8") as fh:
                self.assertNotIn("data_kind", json.load(fh)[0])

    def test_new_result_defaults_to_formal_and_persists_field(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = {"course_id": "W01D01", "student_id": "sherlock", "score": 100}
            with mock.patch.object(progress, "_runtime_dir", return_value=tmp), \
                    mock.patch.object(progress, "persistence_enabled", return_value=False):
                progress.save_result(result)

            with open(os.path.join(tmp, "results.json"), encoding="utf-8") as fh:
                saved = json.load(fh)
            self.assertEqual("formal", saved[0]["data_kind"])

    def test_invalid_explicit_data_kind_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = {
                "course_id": "W01D01",
                "student_id": "sherlock",
                "score": 100,
                "data_kind": "production",
            }
            with mock.patch.object(progress, "_runtime_dir", return_value=tmp), \
                    mock.patch.object(progress, "persistence_enabled", return_value=False):
                with self.assertRaises(ValueError):
                    progress.save_result(result)

    def test_completion_ids_only_include_formal_results(self):
        rows = [
            {"course_id": "W01D01", "data_kind": "test"},
            {"course_id": "W01D02", "data_kind": "formal"},
            {"course_id": "W01D03"},  # legacy records are test
        ]
        self.assertEqual({"W01D02"}, progress.completed_course_ids(rows))

    def test_parent_label_distinguishes_test_and_formal(self):
        self.assertEqual("开发/家长测试", progress.data_kind_label("test"))
        self.assertEqual("正式学习", progress.data_kind_label("formal"))

    def test_normal_child_entry_defaults_to_formal(self):
        self.assertEqual(
            "formal",
            progress.submission_data_kind(),
        )
        self.assertEqual(
            "formal",
            progress.submission_data_kind("formal", parent_authenticated=False),
        )

    def test_test_entry_requires_parent_authenticated_session(self):
        with self.assertRaises(PermissionError):
            progress.submission_data_kind("test", parent_authenticated=False)
        self.assertEqual(
            "test",
            progress.submission_data_kind("test", parent_authenticated=True),
        )

    def test_test_and_formal_course_sessions_use_different_keys(self):
        self.assertNotEqual(
            progress.course_session_key("L", "W01D01", "test"),
            progress.course_session_key("L", "W01D01", "formal"),
        )
        self.assertNotEqual(
            progress.course_session_key("S", "S01D01", "test"),
            progress.course_session_key("S", "S01D01", "formal"),
        )

    def test_legacy_recordings_default_to_test_and_metadata_can_mark_formal(self):
        items = [
            {"name": "old.wav", "path": "recordings/S01D01/old.wav", "size": 10},
            {"name": "new.wav", "path": "recordings/S01D01/new.wav", "size": 20},
        ]
        metadata = {
            "recordings/S01D01/new.wav": {"data_kind": "formal"},
        }
        rows = recorder.classify_recordings(items, metadata)
        self.assertEqual("test", rows[0]["data_kind"])
        self.assertEqual("formal", rows[1]["data_kind"])

    def test_formal_result_writes_recording_sidecar_without_touching_wav(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = {
                "course_id": "S01D01",
                "student_id": "sherlock",
                "module": "speaking",
                "question_results": [{
                    "id": 1,
                    "recordings": ["recordings/S01D01/a.wav"],
                    "recording_records": [{
                        "path": "recordings/S01D01/a.wav",
                        "data_kind": "formal",
                    }],
                }],
            }
            with mock.patch.object(progress, "_runtime_dir", return_value=tmp), \
                    mock.patch.object(progress, "persistence_enabled", return_value=False):
                progress.save_result(result)

            with open(os.path.join(tmp, "recording_metadata.json"), encoding="utf-8") as fh:
                metadata = json.load(fh)
            self.assertEqual(
                "formal",
                metadata["recordings/S01D01/a.wav"]["data_kind"],
            )

    def test_recording_identity_is_saved_immediately_before_result_submission(self):
        with tempfile.TemporaryDirectory() as tmp:
            with mock.patch.object(progress, "_runtime_dir", return_value=tmp), \
                    mock.patch.object(progress, "persistence_enabled", return_value=False):
                progress.save_recording_identity(
                    "recordings/S01D01/test.wav",
                    "test",
                    "S01D01",
                    1,
                )

            with open(os.path.join(tmp, "recording_metadata.json"), encoding="utf-8") as fh:
                metadata = json.load(fh)
            self.assertEqual(
                "test",
                metadata["recordings/S01D01/test.wav"]["data_kind"],
            )


if __name__ == "__main__":
    unittest.main()
