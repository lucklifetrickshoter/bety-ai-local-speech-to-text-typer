"""
bety_ui.py
----------
Bety's entry point and Dynamic Island interface.

This application is primarily a system tray process. The UI is a borderless,
translucent pill that only appears during dictation and retreats when done.
"""

from __future__ import annotations

import sys
import threading

import customtkinter as ctk

from config_manager import DEFAULTS, load_config, save_config
from keyboard_handler import KeyboardHandler
from stt_engine import STTEngine

try:
    import pystray
    from PIL import Image, ImageDraw
    _HAS_TRAY = True
except ImportError:
    _HAS_TRAY = False

# --- Design Tokens ---
BG_COLOR = "#0D0D12"       # Ultra dark
BORDER_COLOR = "#1A1A24"
TEXT_COLOR = "#FFFFFF"
ACCENT_COLOR = "#B5179E"   # Neon Purple
ERROR_COLOR = "#F72585"

W = 280
H = 64
MARGIN_BTM = 80


class BetySettings(ctk.CTkToplevel):
    """A tiny settings panel just for changing the language."""
    def __init__(self, parent: BetyApp) -> None:
        super().__init__(parent)
        self.title("Bety Settings")
        self.geometry("300x180")
        self.resizable(False, False)
        self.configure(fg_color=BG_COLOR)
        
        # Center window
        self.update_idletasks()
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"+{(sw-300)//2}+{(sh-180)//2}")
        
        ctk.CTkLabel(self, text="Whisper Language", font=("Segoe UI", 14, "bold"), text_color=TEXT_COLOR).pack(pady=(20, 5))
        
        self.lang_var = ctk.StringVar(value=load_config().get("WHISPER_LANGUAGE", "Auto"))
        self.menu = ctk.CTkOptionMenu(
            self,
            variable=self.lang_var,
            values=["Auto", "English", "Spanish"],
            fg_color="#1A1A24",
            button_color=ACCENT_COLOR,
            button_hover_color="#7209B7",
            command=self._save
        )
        self.menu.pack(pady=10)
        
    def _save(self, choice: str) -> None:
        cfg = load_config()
        cfg["WHISPER_LANGUAGE"] = choice
        save_config(cfg)


class BetyApp(ctk.CTk):
    """Main Application. Creates the overlay and tray icon, manages lifecycle."""
    
    _DOTS = ["·", "· ·", "· · ·", "· ·", "·"]
    
    def __init__(self) -> None:
        super().__init__()
        # 1. Hide the root window immediately. Bety operates from the tray/overlay.
        self.withdraw()
        
        # 2. Start engines
        self.stt = STTEngine()
        self.keyboard = KeyboardHandler(self.stt, self.on_state_change)
        
        # 3. Build Overlay
        self._build_overlay()
        
        # 4. State
        self._anim_job_id: str | None = None
        self._dot_idx = 0
        
        # 5. Connect F9
        self.keyboard.start_listening()
        
        # 6. System Tray
        self.tray: pystray.Icon | None = None
        if _HAS_TRAY:
            self._start_tray()
            
        print("Bety is running in the background. Hold F9 to dictate.")

    def _build_overlay(self) -> None:
        self.overlay = ctk.CTkToplevel(self)
        self.overlay.overrideredirect(True)
        self.overlay.attributes("-topmost", True)
        self.overlay.configure(fg_color=BG_COLOR)
        self.overlay.resizable(False, False)
        self.overlay.withdraw()
        
        # Attempt alpha
        try:
            self.overlay.attributes("-alpha", 0.95)
        except Exception: # noqa: BLE001
            pass
            
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        self.overlay.geometry(f"{W}x{H}+{(sw - W) // 2}+{sh - H - MARGIN_BTM}")
        
        # Pill Frame
        self.pill = ctk.CTkFrame(
            self.overlay, 
            fg_color=BG_COLOR, 
            border_color=BORDER_COLOR, 
            border_width=1, 
            corner_radius=H//2
        )
        self.pill.pack(fill="both", expand=True, padx=2, pady=2)
        
        # Inner Layout
        self.icon_lbl = ctk.CTkLabel(self.pill, text="🎙️", font=("Segoe UI", 20), text_color=ACCENT_COLOR)
        self.icon_lbl.pack(side="left", padx=(20, 10))
        
        self.msg_lbl = ctk.CTkLabel(self.pill, text="Bety is ready", font=("Segoe UI", 14, "bold"), text_color=TEXT_COLOR)
        self.msg_lbl.pack(side="left", fill="x", expand=True, padx=(0, 20))

    def on_state_change(self, state: str, message: str) -> None:
        """Called by keyboard_handler from background threads."""
        # Marshal to main thread
        self.after(0, lambda s=state, m=message: self._update_ui(s, m))

    def _update_ui(self, state: str, message: str) -> None:
        self._stop_animation()
        
        if state == "hidden":
            self.overlay.withdraw()
            return
            
        self.overlay.deiconify()
        self.overlay.lift()
        
        if state == "listening":
            self.icon_lbl.configure(text="🎙️", text_color=ACCENT_COLOR)
            self.msg_lbl.configure(text=message, text_color=TEXT_COLOR)
        elif state == "transcribing":
            self.icon_lbl.configure(text="⚡", text_color=ACCENT_COLOR)
            self._start_animation()
        elif state == "success":
            self.icon_lbl.configure(text="✅", text_color="#4ADE80")
            # Truncate message if long
            short_msg = message if len(message) < 20 else message[:17] + "..."
            self.msg_lbl.configure(text=short_msg, text_color="#4ADE80")
        elif state == "error":
            self.icon_lbl.configure(text="⚠️", text_color=ERROR_COLOR)
            self.msg_lbl.configure(text="Microphone Error", text_color=ERROR_COLOR)

    def _start_animation(self) -> None:
        self._dot_idx = 0
        self._anim_step()
        
    def _anim_step(self) -> None:
        frame = self._DOTS[self._dot_idx % len(self._DOTS)]
        self.msg_lbl.configure(text=f"Transcribing {frame}")
        self._dot_idx += 1
        self._anim_job_id = self.after(300, self._anim_step)
        
    def _stop_animation(self) -> None:
        if self._anim_job_id:
            try:
                self.after_cancel(self._anim_job_id)
            except Exception: # noqa: BLE001
                pass
            self._anim_job_id = None

    # --- Tray Lifecycle ---
    
    def _create_tray_image(self) -> "Image.Image":
        size = 64
        img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        # Draw a neon purple circle
        draw.ellipse([8, 8, size-8, size-8], fill=ACCENT_COLOR)
        # Inner dark circle
        draw.ellipse([16, 16, size-16, size-16], fill=BG_COLOR)
        return img

    def _start_tray(self) -> None:
        image = self._create_tray_image()
        menu = pystray.Menu(
            pystray.MenuItem("Settings...", self._open_settings),
            pystray.MenuItem("Quit Bety", self._quit_app),
        )
        self.tray = pystray.Icon("Bety", image, "Bety (F9 Dictator)", menu=menu)
        threading.Thread(target=self.tray.run, daemon=True).start()

    def _open_settings(self, icon=None, item=None) -> None:
        self.after(0, lambda: BetySettings(self))

    def _quit_app(self, icon=None, item=None) -> None:
        def _cleanup() -> None:
            print("[bety] Shutting down...")
            if self.tray:
                try:
                    self.tray.stop()
                except Exception: # noqa: BLE001
                    pass
            self.keyboard.cleanup()
            self.destroy()
        self.after(0, _cleanup)

if __name__ == "__main__":
    ctk.set_appearance_mode("dark")
    app = BetyApp()
    # Intercept kill signals to guarantee keyboard hook drops
    app.protocol("WM_DELETE_WINDOW", lambda: app._quit_app())
    app.mainloop()
