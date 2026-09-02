# -*- coding: utf-8 -*-
import unittest

from speaking import models as speaking_models
from storage import progress


class StreamlitPublicationGateTests(unittest.TestCase):
    def test_listening_test_courses_are_not_exposed_by_streamlit(self):
        self.assertIn("L4A-T1-W01-D01", progress.all_courses())
        courses = progress.visible_courses()
        self.assertNotIn("L4A-T1-W01-D01", courses)
        self.assertIn("W01D50", courses)

    def test_speaking_test_courses_are_not_exposed_by_streamlit(self):
        self.assertIn("S4A-T1-W01-D01", speaking_models.all_courses())
        courses = speaking_models.visible_courses()
        self.assertNotIn("S4A-T1-W01-D01", courses)
        self.assertIn("S01D50", courses)


if __name__ == "__main__":
    unittest.main()
