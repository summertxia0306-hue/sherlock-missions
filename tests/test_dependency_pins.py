from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


def _requirements():
    entries = {}
    for raw_line in (ROOT / "requirements.txt").read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        for marker in ("==", ">=", "<=", "~=", ">", "<"):
            if marker in line:
                name, version = line.split(marker, 1)
                entries[name.lower()] = marker + version
                break
    return entries


class DependencyPinTests(unittest.TestCase):
    def test_cloud_runtime_dependencies_are_pinned(self):
        requirements = _requirements()
        self.assertEqual(requirements.get("streamlit"), "==1.55.0")
        self.assertEqual(requirements.get("websocket-client"), "==1.9.0")


if __name__ == "__main__":
    unittest.main()
