import asyncio
from unittest import TestCase, mock

import edge_tts
from edge_tts import communicate
from edge_tts.constants import TRUSTED_CLIENT_TOKEN

from tools.edge_tts_compat import configure_synthesis_endpoint
from tools import make_audio_speaking, make_audio_v2


class EdgeTTSCompatibilityTests(TestCase):
    def test_legacy_transport_uses_supported_endpoint(self):
        legacy = "wss://speech.platform.bing.com/consumer/speech/synthesize/readaloud/edge/v1?TrustedClientToken=" + TRUSTED_CLIENT_TOKEN
        with mock.patch.object(communicate, "WSS_URL", legacy):
            self.assertTrue(configure_synthesis_endpoint())
            self.assertEqual(
                "wss://api.msedgeservices.com/tts/cognitiveservices/websocket/v1?Ocp-Apim-Subscription-Key=" + TRUSTED_CLIENT_TOKEN,
                communicate.WSS_URL,
            )
            self.assertFalse(configure_synthesis_endpoint())

    def test_new_or_custom_endpoint_is_preserved(self):
        for endpoint in (
            "wss://api.msedgeservices.com/tts/cognitiveservices/websocket/v1?future=1",
            "wss://speech.platform.bing.com/another/path",
            "wss://example.com/custom",
        ):
            with self.subTest(endpoint=endpoint), mock.patch.object(communicate, "WSS_URL", endpoint):
                self.assertFalse(configure_synthesis_endpoint())
                self.assertEqual(endpoint, communicate.WSS_URL)

    def test_both_generators_configure_transport_before_communicating(self):
        observed = []

        class FakeCommunicate:
            def __init__(self, text, voice, **kwargs):
                observed.append((communicate.WSS_URL, text, voice, kwargs))

            async def stream(self):
                yield {"type": "audio", "data": b"a" * 1200}

        calls = (
            (make_audio_v2, make_audio_v2.synth_fragment, ("n", "Hello.", "probe.mp3")),
            (make_audio_speaking, make_audio_speaking.synth, ("Hello.", "probe.mp3")),
        )
        for module, function, arguments in calls:
            with self.subTest(module=module.__name__), \
                    mock.patch.object(communicate, "WSS_URL", "wss://speech.platform.bing.com/consumer/speech/synthesize/readaloud/edge/v1?old=1"), \
                    mock.patch.object(edge_tts, "Communicate", FakeCommunicate), \
                    mock.patch.object(module, "prefer_threaded_dns_on_windows"), \
                    mock.patch("builtins.open", mock.mock_open()), \
                    mock.patch.object(module.os, "replace"):
                asyncio.run(function(*arguments))
        self.assertEqual(2, len(observed))
        for endpoint, text, voice, kwargs in observed:
            self.assertIn("api.msedgeservices.com/tts/cognitiveservices/websocket/v1", endpoint)
            self.assertEqual("Hello.", text)
            self.assertEqual("en-US-AnaNeural", voice)
            self.assertEqual("-10%", kwargs["rate"])
