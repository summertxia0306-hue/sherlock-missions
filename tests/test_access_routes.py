# -*- coding: utf-8 -*-
import unittest

from streamlit.testing.v1 import AppTest


class AccessRouteTests(unittest.TestCase):
    def _app(self):
        return AppTest.from_file("app.py", default_timeout=10)

    def test_direct_test_query_is_denied_without_parent_session(self):
        at = self._app()
        at.query_params["mode"] = "test"
        at.query_params["course_id"] = "W01D01"
        at.run()

        self.assertFalse(at.exception)
        self.assertIn(
            "家长测试入口未授权。请先进入家长端并通过密码验证。",
            [item.value for item in at.error],
        )
        self.assertNotIn("L_test_W01D01", at.session_state.filtered_state)

    def test_normal_course_entry_uses_formal_session(self):
        at = self._app()
        at.query_params["course_id"] = "W01D01"
        at.run()

        self.assertFalse(at.exception)
        self.assertIn("L_formal_W01D01", at.session_state.filtered_state)
        self.assertNotIn("L_test_W01D01", at.session_state.filtered_state)

    def test_authenticated_parent_launcher_opens_test_session(self):
        at = self._app()
        at.query_params["mode"] = "parent"
        at.run()
        at.text_input[0].input("xlk2026").run()

        self.assertTrue(at.session_state["parent_authenticated"])
        self.assertEqual(5, sum(b.label == "测试打开" for b in at.button))

        at.button[0].click().run()

        self.assertFalse(at.exception)
        self.assertEqual(["test"], at.query_params["mode"])
        self.assertEqual(["W01D01"], at.query_params["course_id"])
        self.assertIn("L_test_W01D01", at.session_state.filtered_state)
        self.assertIn(
            "🧪 家长测试模式：本次成绩和录音标记为 test，不计入孩子完成状态。",
            [item.value for item in at.warning],
        )


if __name__ == "__main__":
    unittest.main()
