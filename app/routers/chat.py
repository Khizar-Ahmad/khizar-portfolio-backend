from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from app.rag.engine import ask_agent
import io
import tempfile
import os
import json

router = APIRouter(prefix="/api", tags=["chat"])


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    answer: str


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    if not request.message.strip():
        raise HTTPException(400, "Message cannot be empty")
    answer = await ask_agent(request.message.strip())
    print("response in chat route:",answer)
    return ChatResponse(answer=answer)


@router.post("/voice/transcribe")
async def transcribe_voice(audio: UploadFile = File(...)):
    """
    Transcribe audio using Web Speech API on frontend (free).
    This endpoint receives pre-transcribed text from the browser,
    runs it through the RAG agent, and returns the answer + TTS audio.
    """
    raise HTTPException(501, "Use /api/voice/ask with transcribed text instead")


@router.post("/voice/ask")
async def voice_ask(request: ChatRequest):
    """
    Receives transcribed text from browser's Web Speech API,
    runs RAG agent, returns answer text + TTS audio (gTTS, free).
    """
    if not request.message.strip():
        raise HTTPException(400, "Message cannot be empty")

    answer = await ask_agent(request.message.strip())

    # Generate TTS audio using gTTS (completely free, no API key needed)
    try:
        from gtts import gTTS
        tts = gTTS(text=answer, lang='en', slow=False)
        audio_buffer = io.BytesIO()
        tts.write_to_fp(audio_buffer)
        audio_buffer.seek(0)

        # Return both text answer and audio as multipart
        return {
            "answer": answer,
            "has_audio": True,
        }
    except Exception as e:
        return {"answer": answer, "has_audio": False}


@router.post("/voice/tts")
async def text_to_speech(request: ChatRequest):
    """Return MP3 audio stream for given text using gTTS (free)."""
    try:
        from gtts import gTTS
        tts = gTTS(text=request.message, lang='en', slow=False)
        audio_buffer = io.BytesIO()
        tts.write_to_fp(audio_buffer)
        audio_buffer.seek(0)
        return StreamingResponse(
            audio_buffer,
            media_type="audio/mpeg",
            headers={"Content-Disposition": "inline; filename=speech.mp3"}
        )
    except Exception as e:
        raise HTTPException(500, f"TTS error: {str(e)}")
