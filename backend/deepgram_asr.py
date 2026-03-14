from deepgram import (
    DeepgramClient,
    LiveOptions,
    LiveTranscriptionEvents,
    PrerecordedOptions,
)
import httpx

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

    client = DeepgramClient(api_key=api_key)

    options = PrerecordedOptions(
        model="nova-2",
        language="hi",
        punctuate=True,
    )

    mime = mime_type or "audio/wav"
    source = {"buffer": audio_bytes, "mimetype": mime}

    response = client.listen.rest.v("1").transcribe_file(source, options)

    try:
        return response.results.channels[0].alternatives[0].transcript
    except Exception:
        return ""


# ------------------------------------------------------------------
# LIVE MIC STREAMING (WebSocket – Listen V2)
# ------------------------------------------------------------------


def create_live_connection(api_key: str, on_message_callback):
    """
    Create a Deepgram Listen V1 WebSocket connection.
    """

    client = DeepgramClient(api_key=api_key)
    connection = client.listen.websocket.v("1")

    options = LiveOptions(
        model="nova-2",
        language="hi",
        encoding="linear16",
        sample_rate=16000,
        channels=1,
        punctuate=True,
        interim_results=True,
    )

    # ---------------- Event Handlers ----------------

    connection.on(
        LiveTranscriptionEvents.Open,
        lambda self, open, **kwargs: print("Deepgram WebSocket connected"),
    )

    connection.on(
        LiveTranscriptionEvents.Close,
        lambda self, close, **kwargs: print("Deepgram WebSocket closed"),
    )

    connection.on(
        LiveTranscriptionEvents.Error,
        lambda self, error, **kwargs: print("Deepgram error:", error),
    )

    connection.on(LiveTranscriptionEvents.Transcript, on_message_callback)

    connection.start(options)

    return connection
