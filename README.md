# 🎬 AutoDirector: Autonomous AI Video Factory

Fully autonomous, lightweight system designed to generate AI YouTube Shorts, normalize them, overlay voice & subtitles, deliver via Telegram / YouTube, and auto-clean temporary files.

---

## 🚀 Quick Start

### 1. Install Dependencies
```bash
# System dependency (FFmpeg)
sudo apt update && sudo apt install -y ffmpeg

# Python dependencies
pip install -r requirements.txt
```

### 2. Configure API Keys
Copy the example environment file:
```bash
cp config/.env.example config/.env
```
Edit `config/.env` and add any of your available free keys:
- **`OPENROUTER_API_KEY`**: From [OpenRouter](https://openrouter.ai/keys) (Free router)
- **`GEMINI_API_KEY`**: From [Google AI Studio](https://aistudio.google.com/) (Free)
- **`HF_TOKEN`**: From [Hugging Face](https://huggingface.co/settings/tokens) (Free ZeroGPU access)
- **`PEXELS_API_KEY`**: From [Pexels API](https://www.pexels.com/api/) (Free HD stock fallback)
- **`TELEGRAM_BOT_TOKEN`** & **`TELEGRAM_CHAT_ID`**: From [@BotFather](https://t.me/BotFather) for instant phone alerts and video delivery!

---

## 💻 Usage

### Test Run (Dry Run without uploading)
```bash
python main.py --dry-run
```

### Generate a Video with Custom Topic
```bash
python main.py --topic "Mind-blowing psychology facts"
```

### Batch Generate 3 Videos in Sequence
```bash
python main.py --count 3
```

### Debug Mode (Keep temp video parts in /tmp)
```bash
python main.py --keep-temp
```

---

## ⏰ 24/7 Automation on VPS (Cron)

To automatically generate and deliver 3 YouTube Shorts daily (e.g. at 9:00 AM, 3:00 PM, and 9:00 PM):

Open your crontab:
```bash
crontab -e
```

Add this schedule:
```cron
0 9,15,21 * * * cd /home/veer/Desktop/experiment && /usr/bin/python3 main.py >> /var/log/autodirector.log 2>&1
```

---

## 🏗️ Architecture & Modules

- **`config/settings.py`**: Central configurations and fallback chains.
- **`core/director.py`**: OpenRouter Free + Gemini Flash dual LLM scriptwriter.
- **`core/video_engine.py`**: Multi-provider video parts generator (Wan 2.x/3.0, LTX-Video, Pexels fallback).
- **`core/voice_engine.py`**: Microsoft Edge Neural TTS (edge-tts) for Hindi & English voice + word timestamps.
- **`core/compositor.py`**: FFmpeg smart 9:16 vertical conformer, fast-merger, and subtitle burner.
- **`core/qc_validator.py`**: Automated ffprobe gate (checks streams, duration, black frames).
- **`core/uploader.py`**: Direct Telegram Bot video delivery + YouTube hooks.
- **`notifier/telegram_bot.py`**: Real-time heartbeat alerts to mobile phone.
- **`utils/cleanup.py`**: Auto-deletes temp files from RAM/tmpfs to protect storage.
