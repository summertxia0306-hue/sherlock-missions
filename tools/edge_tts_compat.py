"""Development-only compatibility for edge-tts's retired synthesis endpoint."""
from urllib.parse import urlsplit


def configure_synthesis_endpoint():
    """Patch only the known legacy transport; future upstream endpoints win.

    Upstream fix: https://github.com/rany2/edge-tts/pull/491
    communicate imports WSS_URL by value, so updating constants alone cannot
    affect the connection. Voices, rate, token generation and caches stay intact.
    """
    from edge_tts import communicate
    from edge_tts.constants import TRUSTED_CLIENT_TOKEN

    current = urlsplit(communicate.WSS_URL)
    if (current.scheme, current.hostname, current.path) != (
        "wss", "speech.platform.bing.com",
        "/consumer/speech/synthesize/readaloud/edge/v1",
    ):
        return False
    communicate.WSS_URL = (
        "wss://api.msedgeservices.com/tts/cognitiveservices/websocket/v1"
        "?Ocp-Apim-Subscription-Key=" + TRUSTED_CLIENT_TOKEN
    )
    return True
