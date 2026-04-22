"""
keyboard_handler.py
-------------------
Bety's global input listener and output injector.

Listens for F9 globally. Manages the lifecycle of a dictation session.
Injects transcribed text into the active OS window.
Crucially unhooks itself on destruction to prevent OS input lag.
"""

from __future__ import annotations

import threading
import time
from typing import Callable

import keyboard
import pyautogui

try:
    import winsound as _winsound
    _HAS_WINSOUND = True
except ImportError:
    _winsound = None      # type: ignore[assignment]
    _HAS_WINSOUND = False

from stt_engine import STTEngine

HOTKEY = "f9"

# Configure pyautogui
pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.02


def _play_sfx(sound_type: str) -> None:
    """Non-blocking sound effect player."""
    if not _HAS_WINSOUND:
        return
        
    def _play() -> None:
        if sound_type == "start":
            _winsound.Beep(900, 80)
        elif sound_type == "stop":
            _winsound.Beep(600, 80)
        elif sound_type == "success":
            _winsound.Beep(800, 60)
            time.sleep(0.02)
            _winsound.Beep(1200, 80)
            
    threading.Thread(target=_play, daemon=True).start()


class KeyboardHandler:
    def __init__(
        self,
        stt_engine: STTEngine,
        ui_callback: Callable[[str, str], None]
    ) -> None:
        """
        Args:
            stt_engine: Shared transcription engine.
            ui_callback: fn(state, message) -> 'listening', 'transcribing', 'hidden', 'error'
        """
        self._stt = stt_engine
        self._ui_cb = ui_callback
        
        self._active = False
        self._is_recording = False
        self._recording_lock = threading.Lock()
        
    def start_listening(self) -> None:
        """Hooks F9 globally."""
        if self._active:
            return
        self._active = True
        
        # Unhook first just in case
        try:
            keyboard.unhook_all()
        except Exception:  # noqa: BLE001
            pass
            
        keyboard.on_press_key(HOTKEY, self._on_down, suppress=False)
        keyboard.on_release_key(HOTKEY, self._on_up, suppress=False)

    def cleanup(self) -> None:
        """Must be called before the app closes to restore normal keyboard function."""
        self._active = False
        if self._stt.is_busy:
            # Force stop recording
            # STTEngine has no abort, but wait for it to finish gracefully
            pass
        try:
            keyboard.unhook_all()
        except Exception:  # noqa: BLE001
            pass

    def __del__(self) -> None:
        self.cleanup()

    def _on_down(self, _event: keyboard.KeyboardEvent) -> None:
        """F9 pressed: signal UI, play SFX, start microphone."""
        with self._recording_lock:
            if self._is_recording or self._stt.is_busy:
                return
            self._is_recording = True
            
        _play_sfx("start")
        self._ui_cb("listening", "Listening...")
        
        err = self._stt.start_recording()
        if err:
            with self._recording_lock:
                self._is_recording = False
            self._ui_cb("error", err)

    def _on_up(self, _event: keyboard.KeyboardEvent) -> None:
        """F9 released: stop mic, play SFX, launch transcribe thread."""
        with self._recording_lock:
            if not self._is_recording:
                return
            self._is_recording = False
            
        _play_sfx("stop")
        self._ui_cb("transcribing", "Transcribing...")
        
        # Process audio on a daemon thread so keyboard hook returns instantly
        threading.Thread(target=self._process_and_type, daemon=True).start()

    def _process_and_type(self) -> None:
        """Transcribes the buffer and simulates keypresses."""
        try:
            transcript = self._stt.stop_and_transcribe()
            if not transcript or transcript.startswith("⚠️"):
                if transcript:
                    self._ui_cb("error", transcript)
                else:
                    self._ui_cb("hidden", "")
                return

            # Wait just a tiny bit for user to release F9 and refocus their window
            time.sleep(0.1)
            
            # Type execution
            try:
                keyboard.write(transcript)
            except Exception: # noqa: BLE001
                # Fallback to pyautogui for basic ASCII
                pyautogui.write(transcript, interval=0.01)

            _play_sfx("success")
            # Show the text Bety typed as a quick feedback flash
            self._ui_cb("success", transcript)
            
            # Hide after 1.5 seconds automatically
            time.sleep(1.5)
            self._ui_cb("hidden", "")
            
        except Exception as exc: # noqa: BLE001
            self._ui_cb("error", f"Error: {exc}")
