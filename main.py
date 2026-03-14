import os
import asyncio
from fastapi import FastAPI, WebSocket, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

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

    def on_message(self, result, **kwargs):
        sentence = result.channel.alternatives[0].transcript
        if not sentence.strip():
            return

        asyncio.create_task(process_and_send(sentence, ws))

    dg_connection = create_live_connection(DEEPGRAM_API_KEY, on_message)

    try:
        while True:
            audio = await ws.receive_bytes()
            dg_connection.send(audio)
    except Exception:
        dg_connection.finish()
        await ws.close()

async def process_and_send(sentence: str, ws: WebSocket):
    try:
        # 1. Send ASR immediately
        await ws.send_json({
            "type": "asr",
            "hindi": sentence
        })

        # 2. Translate asynchronously
        loop = asyncio.get_event_loop()
        translations = await loop.run_in_executor(
            None, translate_to_english_and_czech, sentence
        )

        # 3. Send translation
        await ws.send_json({
            "type": "translation",
            "english": translations["english"],
            "czech": translations["czech"]
        })
    except Exception as e:
        print(f"Error processing message: {e}")

# --------- REST (FILE UPLOAD) ----------
@app.post("/translate-file")
async def translate_audio_file(file: UploadFile = File(...)):
    audio_bytes = await file.read()

    # 1. Transcribe
    transcript = transcribe_file(DEEPGRAM_API_KEY, audio_bytes, mime_type=file.content_type)

    if not transcript:
        return {"error": "Could not transcribe audio"}

    # 2. Translate
    translations = translate_to_english_and_czech(transcript)

    return {
        "hindi": transcript,
        "english": translations["english"],
        "czech": translations["czech"]
    }
