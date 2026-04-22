# 🎙️ Bety: The Privacy-First Universal Dictator

<div align="center">

![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green)
![Privacy](https://img.shields.io/badge/Privacy-100%25%20Local-brightgreen?logo=shield&logoColor=white)
![Platform](https://img.shields.io/badge/Platform-Windows-0078D6?logo=windows&logoColor=white)

**A minimalist, ultra-fast universal dictation tool. Your voice. Your data. Your machine. Always.**

</div>

---

## 🚀 The Concept

Bety is not a chat bot. Bety does not have an AI "brain" that talks back to you. 

Bety is an **invisible, system-wide microphone**. She lives in your system tray. Whenever you press and hold `F9`, she listens to your voice. When you release `F9`, she instantly types what you said into whatever app you have open (Word, Chrome, Discord, anywhere).

**No cloud processing. No subscriptions. No privacy leaks.**

---

## 🚀 Easiest Way to Run — One-Click Install

> You only need to do this once. After the build, you have a standalone `.exe`.

### What you need first

1. **Python 3.10+** — download from [python.org/downloads](https://www.python.org/downloads/)
   - ⚠️ On the installer screen, **check the box that says "Add Python to PATH"** before clicking Install!
2. An **internet connection** for the first-time setup (to download the Whisper AI weights: ~145 MB)

### One-click build

1. [Download or clone this project](#) to your computer
2. Open the project folder
3. **Double-click `INSTALL.bat`**
4. Wait ~2–5 minutes while it installs everything.
5. Your `.exe` appears at:
   ```
   dist\Bety\Bety.exe
   ```

### Sharing with others

Zip up the entire `dist\Bety\` **folder** and send it. The folder is completely self-contained. Your friends don't need Python installed to run it.

---

## 🔒 Privacy — 100% Local Execution

| Component | Where it runs | Data sent externally? |
|-----------|--------------|----------------------|
| 🎙️ Audio recording | Local microphone | **Never** |
| 📝 Speech-to-text | Local CPU via `faster-whisper` | **Never** |
| ⌨️ Text injection | Local OS level | **Never** |

---

## ✨ Features

- **Global Dictation (Hold F9)** — press and hold `F9` in *any* application to dictate.
- **Dynamic Island UI** — Bety is completely invisible until you hold `F9`. Then, a sleek neon purple pill floats up from the bottom of your screen to show she is listening.
- **Audio Feedback** — satisfying "pop" sounds when starting, stopping, and successfully typing.
- **CPU Optimized** — runs pure `int8` on your CPU. No dedicated GPU required.
- **System Tray Home** — right-click the neon purple circle in your Windows tray to change language or quit.
- **Clean OS Exit** — guarantees no left-over keyboard hooks that cause game lag when closed.

---

## 👨‍💻 Architecture & Files

Bety was designed to be modular and easy to read.

```text
local-voice-assistant/
├── bety_ui.py            ← Entry point. System tray & Dynamic Island UI.
├── stt_engine.py         ← Speech-to-Text motor (CPU faster-whisper).
├── keyboard_handler.py   ← F9 hook lifecycle & type injection.
├── config_manager.py     ← Local JSON configuration reader/saver.
├── INSTALL.bat           ← One-click setup/build script.
├── build.py              ← PyInstaller bundler.
├── requirements.txt      ← Python package list.
└── README.md             ← This file.
```

---

## 🎛️ Customization

Right-click the Bety tray icon and hit **Settings...** to change the Whisper Language (Auto, English, Spanish). 
If Bety often gets words wrong, explicitly locking her to your native language drastically improves accuracy.

### Whisper model size

Open `config_manager.py` to change the underlying motor size.

| Model | Download size | RAM usage | Accuracy |
|-------|--------------|-----------|---------|
| tiny | ~75 MB | ~200 MB | Good |
| **base** | ~145 MB | ~300 MB | **Good (default)** |
| small | ~480 MB | ~600 MB | Better |

---

## 🛠️ Troubleshooting

| Problem | Solution |
|---------|----------|
| Microphone denied (`PortAudioError`) | Windows: *Settings → Privacy → Microphone*. Ensure desktop apps have access. |
| F9 doesn't type anything | Run Bety as Administrator. Some apps (like Discord or games) block virtual keyboards otherwise. |
| Lag on first transcription | Bety lazy-loads Whisper to keep startup fast. The *first* F9 press loads the model. |
| Black screen / `ModuleNotFoundError` | Run `pip install -r requirements.txt` inside your virtual environment. |

---

## 📄 License

This project is released under the **MIT License**.

Built with ❤️ for privacy-conscious users who believe your data belongs to you.
