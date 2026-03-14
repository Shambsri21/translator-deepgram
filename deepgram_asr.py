from deepgram import DeepgramClient
import httpx
from deepgram.core.events import EventType
from deepgram.extensions.types.sockets import (
    ListenV2SocketClientResponse,
    ListenV2MediaMessage,
)

# ------------------------------------------------------------------
# FILE TRANSCRIPTION (REST – Synchronous)
# ------------------------------------------------------------------


def transcribe_file(
    api_key: str, audio_bytes: bytes, mime_type: str | None = None
) -> str:
    """
    Synchronous file transcription with increased timeout
    """

    # Increase timeouts for large files
    timeout = httpx.Timeout(
        connect=60.0,
        read=300.0,
        write=300.0,
        pool=60.0,
    )

    client = DeepgramClient(
        api_key=api_key,
        httpx_client=httpx.Client(timeout=timeout, trust_env=False),
    )

    response = client.listen.v1.media.transcribe_file(
        request=audio_bytes,
        model="nova-2",
        language="hi",
        punctuate=True,
    )

    try:
        return response["results"]["channels"][0]["alternatives"][0]["transcript"]
    except Exception:
        return ""


# ------------------------------------------------------------------
# LIVE MIC STREAMING (WebSocket – Listen V2)
# ------------------------------------------------------------------


def create_live_connection(api_key: str, on_message_callback):
    """
    Create a Deepgram Listen V2 WebSocket connection.

    `on_message_callback` is called with ListenV2SocketClientResponse
    """

    client = DeepgramClient(api_key=api_key)

    connection = client.listen.v2.connect(
        model="nova-2",
        language="hi",
        encoding="linear16",
        sample_rate=16000,
        channels=1,
        punctuate=True,
        interim_results=True,
    )

    # ---------------- Event Handlers ----------------

    connection.on(EventType.OPEN, lambda _: print("🔌 Deepgram WebSocket connected"))

    connection.on(EventType.CLOSE, lambda _: print("❌ Deepgram WebSocket closed"))

    connection.on(EventType.ERROR, lambda e: print("⚠️ Deepgram error:", e))

    connection.on(EventType.MESSAGE, on_message_callback)

    # Start listening
    connection.start_listening()

    return connection
