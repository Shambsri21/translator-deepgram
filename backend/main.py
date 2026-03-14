import os
import asyncio
from fastapi import FastAPI, WebSocket, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from starlette.websockets import WebSocketDisconnect

load_dotenv()

from deepgram_asr import create_live_connection, transcribe_file
from gemini_nlp import translate_to_english_and_czech

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY")


# --------- WEBSOCKET (LIVE MIC) ----------
@app.websocket("/ws/live")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()

    loop = asyncio.get_event_loop()

    def on_message(self, result, **kwargs):
        try:
            alt = result.channel.alternatives[0]
        except (AttributeError, IndexError):
            return

        sentence = alt.transcript
        if not sentence.strip():
            return

        is_final = getattr(result, "is_final", False)
        if is_final:
            # Final: send ASR + trigger translation
            asyncio.run_coroutine_threadsafe(process_and_send(sentence, ws), loop)
        else:
            # Interim: send immediately for live display, skip translation
            asyncio.run_coroutine_threadsafe(
                ws.send_json({"type": "asr_interim", "hindi": sentence}), loop
            )

    dg_connection = create_live_connection(DEEPGRAM_API_KEY, on_message)

    try:
        while True:
            audio = await ws.receive_bytes()
            dg_connection.send(audio)
    except WebSocketDisconnect:
        pass
    except Exception as e:
        print(f"WebSocket loop error: {e}")
    finally:
        try:
            dg_connection.finish()
        except Exception as e:
            print(f"Deepgram finish error: {e}")


async def process_and_send(sentence: str, ws: WebSocket):
    try:
        # 1. Send final ASR immediately
        await ws.send_json({"type": "asr_final", "hindi": sentence})

        # 2. Translate asynchronously
        loop = asyncio.get_event_loop()
        translations = await loop.run_in_executor(
            None, translate_to_english_and_czech, sentence
        )

        # 3. Send translation
        await ws.send_json(
            {
                "type": "translation",
                "english": translations["english"],
                "czech": translations["czech"],
            }
        )
    except Exception as e:
        print(f"Error processing message: {e}")


# --------- REST (FILE UPLOAD) ----------
@app.post("/translate-file")
async def translate_audio_file(file: UploadFile = File(...)):
    audio_bytes = await file.read()

    # 1. Transcribe
    transcript = transcribe_file(
        DEEPGRAM_API_KEY, audio_bytes, mime_type=file.content_type
    )

    if not transcript:
        return {"error": "Could not transcribe audio"}

    # 2. Translate
    translations = translate_to_english_and_czech(transcript)

    return {
        "hindi": transcript,
        "english": translations["english"],
        "czech": translations["czech"],
    }
