# -*- coding: utf-8 -*-
import unittest

from streamlit.testing.v1 import AppTest
class AccessRouteTests(unittest.TestCase):
    def _app(self):
        return AppTest.from_file("app.py", default_timeout=10)

    def test_streamlit_is_a_read_only_migration_notice_for_test_routes(self):
        at = self._app()
        at.query_params["mode"] = "test"
        at.query_params["course_id"] = "W01D39"
        at.run()

        self.assertFalse(at.exception)
        self.assertIn(
            "课程已迁移到新地址",
            [item.value for item in at.title],
        )
        self.assertNotIn("L_test_W01D39", at.session_state.filtered_state)

    def test_streamlit_never_starts_a_formal_course_session(self):
        at = self._app()
        at.query_params["course_id"] = "W01D39"
        at.run()

        self.assertFalse(at.exception)
        self.assertIn("课程已迁移到新地址", [item.value for item in at.title])
        self.assertNotIn("L_formal_W01D39", at.session_state.filtered_state)
        self.assertNotIn("L_test_W01D39", at.session_state.filtered_state)

    def test_streamlit_parent_route_has_no_password_or_course_actions(self):
        at = self._app()
        at.query_params["mode"] = "parent"
        at.run()
        self.assertFalse(at.exception)
        self.assertIn("课程已迁移到新地址", [item.value for item in at.title])
        self.assertEqual([], list(at.text_input))
        self.assertEqual([], [button for button in at.button if "测试打开" in button.label])


if __name__ == "__main__":
    unittest.main()
