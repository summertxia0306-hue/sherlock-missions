import hashlib
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from listening import audio


class MediaDeliveryResilienceTests(unittest.TestCase):
    def test_same_path_audio_replacement_gets_a_new_cache_version(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target = root / 'static/audio/probe.mp3'
            target.parent.mkdir(parents=True)
            target.write_bytes(b'first audio')
            with mock.patch.object(audio, '__file__', str(root / 'listening/audio.py')):
                first = audio.local_audio_source('static/audio/probe.mp3')
                target.write_bytes(b'replaced longer audio')
                second = audio.local_audio_source('static/audio/probe.mp3')
            self.assertNotEqual(first, second)
            self.assertTrue(second.endswith(hashlib.sha256(target.read_bytes()).hexdigest()))

    def test_player_javascript_handles_stalled_sources_and_stale_callbacks(self):
        node = shutil.which('node')
        self.assertIsNotNone(node)
        root = Path(__file__).resolve().parents[1]
        result = subprocess.run([node, '--test', 'tests/js/limited_audio_resilience.test.cjs'],
                                cwd=root, capture_output=True, text=True, encoding='utf-8', timeout=20)
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)

    def test_recent_course_players_include_versioned_same_origin_audio(self):
        root = Path(__file__).resolve().parents[1]
        for module, prefix, days in [('listening', 'L', [29, 30]), ('speaking', 'S', [27, 28])]:
            for day in days:
                path = f'static/audio/{module}/{prefix}4A-T1-W01-D{day:02d}/q01.mp3'
                with self.subTest(path=path), mock.patch.object(audio, '_component') as component:
                    audio.limited_audio(path, 'q1', 2, 0, 'isolated-test')
                    src = component.call_args.kwargs.get('local_src', '')
                    digest = hashlib.sha256((root / path).read_bytes()).hexdigest()
                    self.assertEqual(f'app/{path}?v={digest}', src)


if __name__ == '__main__':
    unittest.main()
