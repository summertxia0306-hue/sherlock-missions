import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DRAFT_DIR = ROOT / "content" / "drafts" / "4A-T1-W01-UNIT2"
LISTENING_DIR = ROOT / "content" / "listening"
SPEAKING_DIR = ROOT / "content" / "speaking"
DOC_DIR = ROOT / "docs" / "course-batches"
LISTENING_IDS = [f"L4A-T1-W01-D{day:02d}" for day in range(11, 16)]
SPEAKING_IDS = [f"S4A-T1-W01-D{day:02d}" for day in range(11, 16)]
PAIR_IDS = [f"4A-T1-W01-D{day:02d}" for day in range(11, 16)]
EXPECTED_COUNTS = [20, 20, 20, 25, 25]
EXPECTED_DIFFICULTIES = ["L1", "L1", "L2", "L2", "L3"]
EXPECTED_SCOPES = ["p15-p16", "p15-p17", "p15-p19", "p15-p21", "p15-p22"]


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def listening_questions(course):
    return [question for section in course["sections"] for question in section["questions"]]


class Unit2ContentTests(unittest.TestCase):
    def test_ten_parent_courses_exist_with_pairing_and_formal_status(self):
        for index, day in enumerate(range(11, 16)):
            listening = load(LISTENING_DIR / f"{LISTENING_IDS[index]}.json")
            speaking = load(SPEAKING_DIR / f"{SPEAKING_IDS[index]}.json")
            pair_id = PAIR_IDS[index]
            for course in (listening, speaking):
                self.assertEqual("4A-T1-W01", course["weekly_batch_id"])
                self.assertEqual(pair_id, course["study_pack"])
                self.assertEqual(pair_id, course["pair_id"])
                self.assertEqual("formal", course["publication_status"])
                self.assertEqual(3, course["week"])
                self.assertEqual(index + 1, course["day"])
                self.assertEqual(EXPECTED_DIFFICULTIES[index], course["difficulty"])
                self.assertIn(EXPECTED_SCOPES[index], course["scope"])

    def test_listening_uses_five_balanced_types_and_scores_100(self):
        expected_section_ids = [
            "word_discrimination",
            "sentence_meaning",
            "question_response",
            "dialogue",
            "passage",
        ]
        expected_types = [
            "word_choice",
            "sentence_judge",
            "question_response",
            "dialogue_choice",
            "passage_judge",
        ]
        for index, course_id in enumerate(LISTENING_IDS):
            course = load(LISTENING_DIR / f"{course_id}.json")
            expected_count = EXPECTED_COUNTS[index]
            per_section = 4 if expected_count == 20 else 5
            self.assertEqual(expected_section_ids, [section["id"] for section in course["sections"]])
            self.assertEqual([per_section] * 5, [len(section["questions"]) for section in course["sections"]])
            self.assertEqual(expected_types, [section["questions"][0]["type"] for section in course["sections"]])
            self.assertEqual(expected_count, len(listening_questions(course)))
            self.assertEqual(100, course["scoring"]["total"])
            self.assertEqual(100, course["scoring"]["per_question"] * expected_count)

    def test_speaking_is_six_repeat_plus_two_qa(self):
        for course_id in SPEAKING_IDS:
            course = load(SPEAKING_DIR / f"{course_id}.json")
            self.assertEqual(8, len(course["questions"]))
            self.assertEqual(["repeat"] * 6 + ["qa"] * 2, [q["type"] for q in course["questions"]])
            self.assertEqual(list(range(1, 9)), [q["id"] for q in course["questions"]])

    def test_d15_is_unit_review_and_earlier_courses_are_training(self):
        for course_id in LISTENING_IDS[:-1]:
            self.assertEqual("training", load(LISTENING_DIR / f"{course_id}.json")["course_type"])
        for course_id in SPEAKING_IDS[:-1]:
            self.assertEqual("training", load(SPEAKING_DIR / f"{course_id}.json")["course_type"])
        self.assertEqual("weekly_test", load(LISTENING_DIR / f"{LISTENING_IDS[-1]}.json")["course_type"])
        self.assertEqual("weekly_review", load(SPEAKING_DIR / f"{SPEAKING_IDS[-1]}.json")["course_type"])

    def test_c_micro_adjustment_is_exactly_fifteen_of_150(self):
        listening_c = 0
        speaking_c = 0
        total = 0
        for course_id in LISTENING_IDS:
            questions = listening_questions(load(LISTENING_DIR / f"{course_id}.json"))
            listening_c += sum(q["tag"].startswith("C微调") for q in questions)
            total += len(questions)
        for course_id in SPEAKING_IDS:
            questions = load(SPEAKING_DIR / f"{course_id}.json")["questions"]
            speaking_c += sum(q["tag"].startswith("C微调") for q in questions)
            total += len(questions)
        self.assertEqual(10, listening_c)
        self.assertEqual(5, speaking_c)
        self.assertEqual(150, total)

    def test_content_stays_inside_unit2_and_excludes_unit3(self):
        allowed_markers = {
            "my classmates", "helpful", "interesting", "lovely", "different", "great", "writer",
            "painter", "football", "basketball", "often", "always", "guessing game",
            "clean the blackboard", "learn english", "long rope", "take it easy", "keep going",
            "happy and excited", "problem", "solution", "result", "painting pictures",
        }
        corpus_parts = []
        for course_id in LISTENING_IDS:
            corpus_parts.append((LISTENING_DIR / f"{course_id}.json").read_text(encoding="utf-8").lower())
        for course_id in SPEAKING_IDS:
            corpus_parts.append((SPEAKING_DIR / f"{course_id}.json").read_text(encoding="utf-8").lower())
        corpus = "\n".join(corpus_parts)
        self.assertTrue(all(marker in corpus for marker in allowed_markers))
        for forbidden in ("animals and their homes", "polar bear", "golden monkey", "giant panda"):
            self.assertNotIn(forbidden, corpus)

    def test_child_copies_and_catalogs_are_safe_and_visible(self):
        forbidden = {"answer", "transcript", "tag", "parent_note", "expected", "score", "scoring"}
        for module, ids in (("listening", LISTENING_IDS), ("speaking", SPEAKING_IDS)):
            catalog = load(DRAFT_DIR / "child" / module / "catalog.json")
            self.assertEqual(ids, [entry["course_id"] for entry in catalog])
            self.assertTrue(all(entry["visible"] is True for entry in catalog))
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

    def test_study_packs_audio_plan_and_documents_cover_all_courses(self):
        packs = load(DRAFT_DIR / "study-packs.json")
        self.assertEqual("4A-T1-W01", packs["weekly_batch_id"])
        self.assertEqual("formal", packs["publication_status"])
        self.assertTrue(packs["visible"])
        self.assertEqual(PAIR_IDS, [pack["pair_id"] for pack in packs["study_packs"]])

        audio = load(DRAFT_DIR / "audio-generation-plan.json")
        self.assertEqual(98, audio["expected_listening_outputs"])
        self.assertEqual(40, audio["expected_speaking_outputs"])
        self.assertEqual(138, audio["expected_total_outputs"])
        self.assertEqual(138, len(audio["items"]))

        mapping = (DOC_DIR / "2026-09-11-4A-Unit2-D11-D15教材与课程映射.md").read_text(encoding="utf-8")
        parent = (DOC_DIR / "2026-09-11-4A-Unit2-D11-D15家长版答案原文.md").read_text(encoding="utf-8")
        for course_id in LISTENING_IDS + SPEAKING_IDS:
            self.assertIn(course_id, mapping)
            self.assertIn(course_id, parent)

    def test_all_138_audio_outputs_exist_and_are_manifested(self):
        plan = load(DRAFT_DIR / "audio-generation-plan.json")
        listening_manifest = load(ROOT / "static" / "audio" / "listening" / "manifest.json")
        speaking_manifest = load(ROOT / "static" / "audio" / "speaking" / "manifest.json")
        for item in plan["items"]:
            path = item["path"]
            self.assertTrue((ROOT / path).is_file(), path)
            manifest = listening_manifest if item["module"] == "listening" else speaking_manifest
            course_entries = manifest["courses"].get(item["course_id"], {})
            self.assertIn(path, course_entries, f"{item['course_id']}: {path}")

    def test_no_sensitive_markers_in_deliverables(self):
        files = list(DRAFT_DIR.rglob("*.json"))
        files.extend(LISTENING_DIR / f"{course_id}.json" for course_id in LISTENING_IDS)
        files.extend(SPEAKING_DIR / f"{course_id}.json" for course_id in SPEAKING_IDS)
        lowered = "\n".join(path.read_text(encoding="utf-8") for path in files).lower()
        for marker in ("api_secret", "api_key", "parent_password", "private_key", "secret_key"):
            self.assertNotIn(marker, lowered)


if __name__ == "__main__":
    unittest.main()
