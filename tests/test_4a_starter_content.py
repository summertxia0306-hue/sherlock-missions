# -*- coding: utf-8 -*-
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LISTENING_DIR = ROOT / "content" / "listening"
SPEAKING_DIR = ROOT / "content" / "speaking"
DRAFT_DIR = ROOT / "content" / "drafts" / "4A-T1-W01-STARTER"
DOC_DIR = ROOT / "docs" / "course-batches"

LISTENING_IDS = [f"L4A-T1-W01-D{day:02d}" for day in range(7, 12)]
SPEAKING_IDS = [f"S4A-T1-W01-D{day:02d}" for day in range(7, 12)]
PAIR_IDS = [f"4A-T1-W01-D{day:02d}" for day in range(7, 12)]
QUESTION_COUNTS = [20, 20, 20, 20, 25]
SCOPES = [
    "4A Starter p2-p3",
    "4A Starter p2-p4",
    "4A Starter p2-p5",
    "4A Starter p2-p6 Numbers",
    "4A Starter p2-p6 Days of the week and review",
]
JSON_DIFFICULTIES = ["L1", "L1", "L2", "L2", "L3"]
PLANNED_DIFFICULTIES = ["L1", "L1+", "L2", "L2+", "L3"]
MAX_PLAYS = [
    [2, 2, 2, 2, 3],
    [2, 2, 2, 2, 3],
    [2, 2, 2, 2, 3],
    [1, 2, 2, 2, 3],
    [1, 1, 2, 2, 3],
]
SECTION_IDS = [
    "word_discrimination",
    "sentence_meaning",
    "question_response",
    "dialogue",
    "passage",
]


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def flat_questions(course):
    return [question for section in course["sections"] for question in section["questions"]]


class StarterFivePackContentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.listening = [load(LISTENING_DIR / f"{course_id}.json") for course_id in LISTENING_IDS]
        cls.speaking = [load(SPEAKING_DIR / f"{course_id}.json") for course_id in SPEAKING_IDS]

    def test_exact_active_course_files_exist(self):
        for course_id in LISTENING_IDS:
            self.assertTrue((LISTENING_DIR / f"{course_id}.json").is_file())
        for course_id in SPEAKING_IDS:
            self.assertTrue((SPEAKING_DIR / f"{course_id}.json").is_file())

    def test_ids_pairing_scope_and_hidden_test_status(self):
        for index, (listening, speaking) in enumerate(zip(self.listening, self.speaking)):
            self.assertEqual(LISTENING_IDS[index], listening["course_id"])
            self.assertEqual(SPEAKING_IDS[index], speaking["course_id"])
            for course in (listening, speaking):
                self.assertEqual("4A-T1-W01", course["weekly_batch_id"])
                self.assertEqual(PAIR_IDS[index], course["study_pack"])
                self.assertEqual(PAIR_IDS[index], course["pair_id"])
                self.assertEqual("test", course["publication_status"])
                self.assertEqual("training", course["course_type"])
                self.assertEqual(SCOPES[index], course["scope"])
                self.assertEqual(JSON_DIFFICULTIES[index], course["difficulty"])

    def test_listening_structure_counts_scoring_and_play_limits(self):
        for index, course in enumerate(self.listening):
            self.assertEqual(SECTION_IDS, [section["id"] for section in course["sections"]])
            per_section = 4 if QUESTION_COUNTS[index] == 20 else 5
            self.assertTrue(all(len(section["questions"]) == per_section for section in course["sections"]))
            self.assertEqual(QUESTION_COUNTS[index], len(flat_questions(course)))
            self.assertEqual(100, course["scoring"]["total"])
            self.assertEqual(100, course["scoring"]["per_question"] * QUESTION_COUNTS[index])
            self.assertEqual(MAX_PLAYS[index], [section["max_plays"] for section in course["sections"]])

    def test_listening_answers_ids_and_c_adjustment(self):
        valid_judgements = {
            "sentence_judge": {"same", "different"},
            "passage_judge": {"true", "false"},
        }
        for course in self.listening:
            questions = flat_questions(course)
            self.assertEqual(list(range(1, len(questions) + 1)), [question["id"] for question in questions])
            self.assertEqual(2, sum(question["tag"].startswith("C微调·") for question in questions))
            for question in questions:
                if question["type"] in valid_judgements:
                    self.assertIn(question["answer"], valid_judgements[question["type"]])
                else:
                    self.assertGreaterEqual(question["answer"], 0)
                    self.assertLess(question["answer"], len(question["options"]))

    def test_speaking_is_six_repeat_plus_two_fixed_answer_qa(self):
        for course in self.speaking:
            questions = course["questions"]
            self.assertEqual(8, len(questions))
            self.assertEqual(list(range(1, 9)), [question["id"] for question in questions])
            self.assertEqual(["repeat"] * 6 + ["qa"] * 2, [question["type"] for question in questions])
            self.assertEqual(1, sum(question["tag"].startswith("C微调·") for question in questions))
            for question in questions[6:]:
                self.assertTrue(question["question"].strip())
                self.assertTrue(question["expected"].strip())
                self.assertTrue(question["hint"].strip())

    def test_material_difficulty_progression_is_not_title_only(self):
        max_dialogue_parts = []
        for course in self.listening:
            dialogue_section = next(section for section in course["sections"] if section["id"] == "dialogue")
            max_dialogue_parts.append(max(len(question["transcript"]) for question in dialogue_section["questions"]))
        self.assertGreaterEqual(max_dialogue_parts[2], max_dialogue_parts[0] + 1)
        self.assertGreaterEqual(max_dialogue_parts[4], max_dialogue_parts[2])
        self.assertLess(MAX_PLAYS[4][0], MAX_PLAYS[0][0])
        self.assertLess(MAX_PLAYS[4][1], MAX_PLAYS[0][1])

    def test_no_unit_one_or_old_textbook_content(self):
        payload = json.dumps(self.listening + self.speaking, ensure_ascii=False).lower()
        forbidden = [
            "school building", "library", "classroom", "computer room", "sports field",
            "art room", "bamboo", "wall", "peter", "kitty", "sally", "paul", "danny",
            "tracy", "ride a bicycle", "skip", "student number", "like playing",
        ]
        for term in forbidden:
            self.assertNotIn(term, payload)

    def test_study_packs_and_audio_plan_match_exactly(self):
        packs = load(DRAFT_DIR / "study-packs.json")
        self.assertEqual("4A-T1-W01", packs["weekly_batch_id"])
        self.assertEqual(PLANNED_DIFFICULTIES, [pack["planned_difficulty"] for pack in packs["study_packs"]])
        self.assertEqual(PAIR_IDS, [pack["pair_id"] for pack in packs["study_packs"]])
        self.assertEqual(LISTENING_IDS, [pack["listening_course_id"] for pack in packs["study_packs"]])
        self.assertEqual(SPEAKING_IDS, [pack["speaking_course_id"] for pack in packs["study_packs"]])

        plan = load(DRAFT_DIR / "audio-generation-plan.json")
        paths = [item["path"] for item in plan["items"]]
        self.assertEqual(94, plan["expected_listening_outputs"])
        self.assertEqual(40, plan["expected_speaking_outputs"])
        self.assertEqual(134, plan["expected_total_outputs"])
        self.assertEqual(134, len(paths))
        self.assertEqual(134, len(set(paths)))

    def test_all_134_audio_outputs_exist_and_are_manifested(self):
        plan = load(DRAFT_DIR / "audio-generation-plan.json")
        listening_manifest = load(ROOT / "static" / "audio" / "listening" / "manifest.json")
        speaking_manifest = load(ROOT / "static" / "audio" / "speaking" / "manifest.json")
        for item in plan["items"]:
            path = item["path"]
            self.assertTrue((ROOT / path).is_file(), path)
            manifest = listening_manifest if item["module"] == "listening" else speaking_manifest
            course_entries = manifest["courses"].get(item["course_id"], {})
            self.assertIn(path, course_entries, f"{item['course_id']}: {path}")

    def test_generated_child_validation_copies_are_safe_and_hidden(self):
        forbidden_listening = {"answer", "transcript", "passage_transcript", "tag", "parent_note"}
        forbidden_speaking = {"question", "expected", "tag", "parent_note", "scoring", "difficulty"}
        for module, ids, forbidden in (
            ("listening", LISTENING_IDS, forbidden_listening),
            ("speaking", SPEAKING_IDS, forbidden_speaking),
        ):
            catalog = load(DRAFT_DIR / "child" / module / "catalog.json")
            self.assertEqual(ids, [entry["course_id"] for entry in catalog])
            self.assertTrue(all(entry["visible"] is False for entry in catalog))
            for course_id in ids:
                child = load(DRAFT_DIR / "child" / module / f"{course_id}.json")
                keys = set()
                stack = [child]
                while stack:
                    value = stack.pop()
                    if isinstance(value, dict):
                        keys.update(value)
                        stack.extend(value.values())
                    elif isinstance(value, list):
                        stack.extend(value)
                self.assertFalse(keys & forbidden, f"{course_id}: {keys & forbidden}")

    def test_parent_and_mapping_documents_cover_all_courses(self):
        mapping = (DOC_DIR / "2026-09-07-4A-Starter-D07-D11教材与课程映射.md").read_text(encoding="utf-8")
        parent = (DOC_DIR / "2026-09-07-4A-Starter-D07-D11家长版答案原文.md").read_text(encoding="utf-8")
        for course_id in LISTENING_IDS + SPEAKING_IDS:
            self.assertIn(course_id, mapping)
            self.assertIn(course_id, parent)

    def test_no_sensitive_markers_in_deliverables(self):
        files = list(DRAFT_DIR.rglob("*.json"))
        files.extend(LISTENING_DIR / f"{course_id}.json" for course_id in LISTENING_IDS)
        files.extend(SPEAKING_DIR / f"{course_id}.json" for course_id in SPEAKING_IDS)
        lowered = "\n".join(path.read_text(encoding="utf-8") for path in files).lower()
        for marker in ("api_secret", "api_key", "parent_password", "private_key", "secret_key"):
            self.assertNotIn(marker, lowered)


if __name__ == "__main__":
    unittest.main()
