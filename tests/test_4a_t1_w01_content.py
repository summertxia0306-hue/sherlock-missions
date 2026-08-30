# -*- coding: utf-8 -*-
import json
import os
import re
import unittest


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BATCH_ROOT = os.path.join(ROOT, "content", "drafts", "4A-T1-W01")
LISTENING_ROOT = os.path.join(BATCH_ROOT, "listening")
SPEAKING_ROOT = os.path.join(BATCH_ROOT, "speaking")
ACTIVE_LISTENING_ROOT = os.path.join(ROOT, "content", "listening")
ACTIVE_SPEAKING_ROOT = os.path.join(ROOT, "content", "speaking")

LISTENING_COUNTS = [20, 20, 20, 25, 25, 25]
JSON_DIFFICULTIES = ["L1", "L1", "L2", "L2", "L3", "L3"]
PLANNED_DIFFICULTIES = ["L1", "L1+", "L2", "L2+", "L3", "L3综合"]
SECTION_IDS = [
    "word_discrimination",
    "sentence_meaning",
    "question_response",
    "dialogue",
    "passage",
]
FORBIDDEN_AFTER_P3 = (
    "student number",
    "new classmate",
    "jill",
    "sit here",
    "live near",
    "walk to school",
    "likes reading",
    "like reading",
    "likes dancing",
    "like dancing",
    "play basketball",
    "desk",
    "mask",
    "j-o-e",
    "r-o-s-e",
    "year-old",
    "introduce",
    "introduces",
    "family",
    "nice to see",
    "bitter",
    "has ",
    "like+v-ing",
)
SENSITIVE_MARKERS = (
    "XF_APPID",
    "XF_API_KEY",
    "XF_API_SECRET",
    "RESULTS_TOKEN",
    "PARENT_PASSWORD",
    "TCB_SECRET",
)


def load_json(path):
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def listening_path(day):
    return os.path.join(LISTENING_ROOT, "L4A-T1-W01-D%02d.json" % day)


def speaking_path(day):
    return os.path.join(SPEAKING_ROOT, "S4A-T1-W01-D%02d.json" % day)


def flat_listening(course):
    return [question for section in course["sections"] for question in section["questions"]]


def course_text(course):
    return json.dumps(course, ensure_ascii=False).lower()


def nested_keys(value):
    keys = set()
    if isinstance(value, dict):
        keys.update(value)
        for child in value.values():
            keys.update(nested_keys(child))
    elif isinstance(value, list):
        for child in value:
            keys.update(nested_keys(child))
    return keys


class FirstWeekContentTests(unittest.TestCase):
    def test_exact_course_files_exist(self):
        expected_listening = ["L4A-T1-W01-D%02d.json" % day for day in range(1, 7)]
        expected_speaking = ["S4A-T1-W01-D%02d.json" % day for day in range(1, 7)]
        self.assertEqual(expected_listening, sorted(os.listdir(LISTENING_ROOT)))
        self.assertEqual(expected_speaking, sorted(os.listdir(SPEAKING_ROOT)))

    def test_ids_pairing_scope_and_difficulty(self):
        for day in range(1, 7):
            with self.subTest(day=day):
                pair_id = "4A-T1-W01-D%02d" % day
                listening = load_json(listening_path(day))
                speaking = load_json(speaking_path(day))
                self.assertEqual("L%s" % pair_id, listening["course_id"])
                self.assertEqual("S%s" % pair_id, speaking["course_id"])
                for course in (listening, speaking):
                    self.assertEqual("4A-T1-W01", course["weekly_batch_id"])
                    self.assertEqual(pair_id, course["study_pack"])
                    self.assertEqual(pair_id, course["pair_id"])
                    self.assertEqual(1, course["week"])
                    self.assertEqual(day, course["day"])
                    self.assertEqual(JSON_DIFFICULTIES[day - 1], course["difficulty"])
                    self.assertIn("M1U1", course["scope"])
                    self.assertIn("p2", course["scope"])
                if day == 1:
                    self.assertNotIn("p3", listening["scope"])
                    self.assertNotIn("p3", speaking["scope"])
                else:
                    self.assertIn("p3", listening["scope"])
                    self.assertIn("p3", speaking["scope"])

    def test_listening_structure_counts_and_scoring(self):
        for day, expected_count in enumerate(LISTENING_COUNTS, 1):
            with self.subTest(day=day):
                course = load_json(listening_path(day))
                self.assertEqual(SECTION_IDS, [section["id"] for section in course["sections"]])
                per_section = expected_count // 5
                self.assertTrue(all(len(section["questions"]) == per_section for section in course["sections"]))
                questions = flat_listening(course)
                self.assertEqual(expected_count, len(questions))
                self.assertEqual(list(range(1, expected_count + 1)), [q["id"] for q in questions])
                self.assertEqual(5 if expected_count == 20 else 4, course["scoring"]["per_question"])
                self.assertEqual(100, course["scoring"]["total"])
                self.assertEqual(100, expected_count * course["scoring"]["per_question"])
                expected_type = "weekly_test" if day == 6 else "training"
                self.assertEqual(expected_type, course["course_type"])

    def test_listening_answers_are_valid(self):
        judge_values = {
            "sentence_judge": {"same", "different"},
            "passage_judge": {"true", "false"},
        }
        for day in range(1, 7):
            for question in flat_listening(load_json(listening_path(day))):
                with self.subTest(day=day, question=question["id"]):
                    if question["type"] in {"word_choice", "question_response", "dialogue_choice"}:
                        self.assertIsInstance(question["answer"], int)
                        self.assertGreaterEqual(question["answer"], 0)
                        self.assertLess(question["answer"], len(question["options"]))
                        self.assertEqual(len(question["options"]), len(set(question["options"])))
                    else:
                        self.assertIn(question["answer"], judge_values[question["type"]])

    def test_speaking_is_six_repeat_plus_two_qa(self):
        for day in range(1, 7):
            with self.subTest(day=day):
                course = load_json(speaking_path(day))
                questions = course["questions"]
                self.assertEqual(8, len(questions))
                self.assertEqual(list(range(1, 9)), [q["id"] for q in questions])
                self.assertEqual(["repeat"] * 6 + ["qa"] * 2, [q["type"] for q in questions])
                self.assertEqual("weekly_review" if day == 6 else "training", course["course_type"])
                for question in questions:
                    self.assertRegex(question["audio"], r"^static/audio/speaking/%s/q\d{2}\.mp3$" % re.escape(course["course_id"]))
                    if question["type"] == "qa":
                        self.assertTrue(question["question"])
                        self.assertTrue(question["expected"])
                        self.assertTrue(question["hint"].startswith("用英语说："))

    def test_all_content_stays_within_p2_p3(self):
        courses = []
        for day in range(1, 7):
            courses.extend((load_json(listening_path(day)), load_json(speaking_path(day))))
        combined = "\n".join(course_text(course) for course in courses)
        for phrase in FORBIDDEN_AFTER_P3:
            with self.subTest(phrase=phrase):
                self.assertNotIn(phrase, combined)

    def test_a_mainline_and_c_adjustment_are_traceable_and_bounded(self):
        total = 0
        c_total = 0
        for day in range(1, 7):
            courses = [load_json(listening_path(day)), load_json(speaking_path(day))]
            for course in courses:
                questions = flat_listening(course) if "sections" in course else course["questions"]
                total += len(questions)
                c_questions = [q for q in questions if q["tag"].startswith("C微调·")]
                c_total += len(c_questions)
                self.assertLessEqual(len(c_questions) / len(questions), 0.20)
                self.assertTrue(all(q["tag"].startswith(("A主线·", "C微调·")) for q in questions))
        self.assertLessEqual(c_total / total, 0.20)
        self.assertGreater(c_total, 0)

    def test_difficulty_progression_is_material(self):
        courses = [load_json(listening_path(day)) for day in range(1, 7)]
        self.assertTrue(all(section["max_plays"] >= 2 for section in courses[0]["sections"]))
        self.assertEqual(1, courses[3]["sections"][0]["max_plays"])
        self.assertEqual(1, courses[3]["sections"][2]["max_plays"])
        self.assertEqual(1, courses[4]["sections"][1]["max_plays"])
        self.assertEqual(1, courses[5]["sections"][0]["max_plays"])
        self.assertGreater(
            len(courses[5]["sections"][4]["passage_transcript"][0][1]),
            len(courses[0]["sections"][4]["passage_transcript"][0][1]),
        )

    def test_study_pack_and_audio_generation_plan_match_courses(self):
        packs = load_json(os.path.join(BATCH_ROOT, "study-packs.json"))
        audio_plan = load_json(os.path.join(BATCH_ROOT, "audio-generation-plan.json"))
        self.assertEqual("READY_FOR_TEST", packs["publication_status"])
        self.assertEqual(PLANNED_DIFFICULTIES, [pack["planned_difficulty"] for pack in packs["study_packs"]])
        self.assertEqual(6, len(packs["study_packs"]))
        expected_audio = set()
        for day in range(1, 7):
            listening = load_json(listening_path(day))
            speaking = load_json(speaking_path(day))
            expected_audio.add(listening["test_audio"])
            for section in listening["sections"]:
                if section.get("shared_audio"):
                    expected_audio.add(section["passage_audio"])
                for question in section["questions"]:
                    if question.get("audio"):
                        expected_audio.add(question["audio"])
            expected_audio.update(question["audio"] for question in speaking["questions"])
        planned_audio = {item["path"] for item in audio_plan["items"]}
        self.assertEqual(expected_audio, planned_audio)
        self.assertEqual(168, len(planned_audio))
        self.assertEqual("READY_TO_GENERATE", audio_plan["generation_status"])

    def test_no_sensitive_markers_in_deliverables(self):
        paths = [listening_path(day) for day in range(1, 7)] + [speaking_path(day) for day in range(1, 7)]
        paths += [
            os.path.join(BATCH_ROOT, "study-packs.json"),
            os.path.join(BATCH_ROOT, "audio-generation-plan.json"),
        ]
        for path in paths:
            text = json.dumps(load_json(path), ensure_ascii=False)
            for marker in SENSITIVE_MARKERS:
                with self.subTest(path=path, marker=marker):
                    self.assertNotIn(marker, text)

    def test_draft_child_copies_hide_parent_only_fields_and_are_not_visible(self):
        child_root = os.path.join(BATCH_ROOT, "child")
        forbidden_listening = {"answer", "transcript", "passage_transcript", "tag", "parent_note", "scoring", "difficulty"}
        forbidden_speaking = {"question", "expected", "tag", "parent_note", "score", "difficulty"}
        for module, forbidden in (("listening", forbidden_listening), ("speaking", forbidden_speaking)):
            module_root = os.path.join(child_root, module)
            catalog = load_json(os.path.join(module_root, "catalog.json"))
            self.assertEqual(6, len(catalog))
            self.assertTrue(all(entry["visible"] is False for entry in catalog))
            for entry in catalog:
                child = load_json(os.path.join(module_root, entry["course_id"] + ".json"))
                with self.subTest(module=module, course=entry["course_id"]):
                    self.assertFalse(nested_keys(child) & forbidden)
                    self.assertNotIn("weekly_batch_id", child)
                    self.assertEqual(entry["pair_id"], child["pair_id"])
                    self.assertEqual(entry["study_pack"], child["study_pack"])

    def test_promoted_courses_are_test_only_and_all_168_audio_files_are_manifested(self):
        listening_manifest = load_json(os.path.join(ROOT, "static", "audio", "listening", "manifest.json"))["courses"]
        speaking_manifest = load_json(os.path.join(ROOT, "static", "audio", "speaking", "manifest.json"))["courses"]
        planned = load_json(os.path.join(BATCH_ROOT, "audio-generation-plan.json"))["items"]
        self.assertEqual(168, len(planned))
        for item in planned:
            with self.subTest(path=item["path"]):
                active_root = ACTIVE_LISTENING_ROOT if item["module"] == "listening" else ACTIVE_SPEAKING_ROOT
                course = load_json(os.path.join(active_root, item["course_id"] + ".json"))
                self.assertEqual("test", course["publication_status"])
                self.assertTrue(os.path.isfile(os.path.join(ROOT, item["path"])))
                self.assertGreater(os.path.getsize(os.path.join(ROOT, item["path"])), 0)
                manifest = listening_manifest if item["module"] == "listening" else speaking_manifest
                self.assertIn(item["path"], manifest[item["course_id"]])

    def test_mapping_and_parent_documents_cover_all_six_pairs(self):
        docs_root = os.path.join(ROOT, "docs", "course-batches")
        mapping_path = os.path.join(docs_root, "2026-09-01-4A-T1-W01教材与课程映射.md")
        parent_path = os.path.join(docs_root, "2026-09-01-4A-T1-W01家长版答案原文.md")
        with open(mapping_path, encoding="utf-8") as handle:
            mapping = handle.read()
        with open(parent_path, encoding="utf-8") as handle:
            parent = handle.read()
        self.assertEqual(6, parent.count("\n## D"))
        for day in range(1, 7):
            self.assertIn("4A-T1-W01-D%02d" % day, mapping)
            self.assertIn("L4A-T1-W01-D%02d" % day, mapping)
            self.assertIn("S4A-T1-W01-D%02d" % day, mapping)
            listening = load_json(listening_path(day))
            for section in listening["sections"]:
                if section.get("shared_audio"):
                    self.assertIn(section["passage_transcript"][0][1], parent)
                    for question in section["questions"]:
                        self.assertIn(question["statement"], parent)


if __name__ == "__main__":
    unittest.main()
