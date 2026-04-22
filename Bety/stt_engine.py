"""
stt_engine.py
-------------
Speech-to-Text core for Bety using local CPU-bound faster-whisper.

Handles PortAudio microphone streams safely via sounddevice.
Lazy-loads the AI model on first use so startup is instantaneous.
"""

from __future__ import annotations

import io
import threading
from typing import Callable

import numpy as np
import scipy.io.wavfile as wav
import sounddevice as sd
from faster_whisper import WhisperModel

import config_manager

# 16kHz Mono PCM16 is standard for Whisper
SAMPLE_RATE: int = 16_000
CHANNELS: int = 1
DTYPE: str = "int16"

_LANGUAGE_MAP: dict[str, str | None] = {
    "Auto": None,
    "English": "en",
    "Spanish": "es",
}


class STTEngine:
    """Manages recording state and transcription pipeline."""

    def __init__(self) -> None:
        self._frames: list[np.ndarray] = []
        self._stream: sd.InputStream | None = None
        self._lock = threading.Lock()
        
        self._model: WhisperModel | None = None
        self._model_lock = threading.Lock()
        
        # Thread safety guard for recording sessions
        self._in_use = threading.Event()

    @property
    def is_busy(self) -> bool:
        return self._in_use.is_set()

    def _get_model(self) -> WhisperModel:
        """Lazy load the Whisper model on first request."""
        with self._model_lock:
            if self._model is None:
                config = config_manager.load_config()
                model_size = config.get("WHISPER_MODEL_SIZE", "base")
                
                print(f"[stt] Loading Whisper {model_size} model on CPU...")
                self._model = WhisperModel(
                    model_size,
                    device="cpu",
                    compute_type="int8",
                )
                print("[stt] Model loaded.")
            return self._model

    def start_recording(self) -> str | None:
        """Starts the microphone stream. Returns None on success, string error otherwise."""
        with self._lock:
            self._frames = []

        if self._in_use.is_set():
            return "⚠️ Bety is already listening."

        def _callback(indata: np.ndarray, frames: int, time_info: object, status: sd.CallbackFlags) -> None:
            if status:
                print(f"[stt] sounddevice warning: {status}")
            with self._lock:
                self._frames.append(indata.copy())

        try:
            self._stream = sd.InputStream(
                samplerate=SAMPLE_RATE,
                channels=CHANNELS,
                dtype=DTYPE,
                callback=_callback,
            )
            self._stream.start()
            self._in_use.set()
            return None
        except sd.PortAudioError as exc:
            self._stream = None
            return f"⚠️ Microphone denied or missing: {exc}"
        except Exception as exc:  # noqa: BLE001
            self._stream = None
            return f"⚠️ Audio error: {exc}"

    def stop_and_transcribe(self, status_callback: Callable[[str], None] | None = None) -> str:
        """Stops the mic and converts buffered audio to text."""
        # Stop stream
        if self._stream is not None:
            try:
                self._stream.stop()
                self._stream.close()
            except Exception as exc:  # noqa: BLE001
                print(f"[stt] Stream close error: {exc}")
            finally:
                self._stream = None
                self._in_use.clear()

        # Extract frames
        with self._lock:
            frames = list(self._frames)
            
        if not frames:
            return ""

        audio_data = np.concatenate(frames, axis=0)
        
        # Whisper requires at least 0.5s to not hallucinate usually
        duration = len(audio_data) / SAMPLE_RATE
        if duration < 0.3:
            return ""

        if status_callback:
            status_callback("Loading model into memory..." if self._model is None else "Transcribing...")

        # Encode to WAV in memory
        wav_io = io.BytesIO()
        wav.write(wav_io, SAMPLE_RATE, audio_data)
        wav_io.seek(0)

        # Transcribe
        try:
            model = self._get_model()
            config = config_manager.load_config()
            lang_choice = config.get("WHISPER_LANGUAGE", "Auto")
            lang_code = _LANGUAGE_MAP.get(lang_choice)
            
            # A rich initial prompt forces the model to use proper capitalization and punctuation.
            prompt = "¡Hola! ¿Cómo estás? Bien, gracias. Hello! How are you? Good, thanks."

            segments, info = model.transcribe(
                wav_io,
                language=lang_code,
                beam_size=5,
                initial_prompt=prompt,
                condition_on_previous_text=True, 
            )
            
            transcript = "".join(segment.text for segment in segments).strip()
            return transcript
        except Exception as exc:  # noqa: BLE001
            return f"⚠️ Whisper error: {exc}"
