#!/usr/bin/env python3
"""
👑 Void Archive AI CEO v3 - True Autonomous Intelligence Daemon
- Long-form 8-12 minute documentary pipeline designed for YouTube monetization
- 100% PUBLIC uploads with Science & Technology category (28)
- Proactive executive briefings, telemetry, and strategy pivots
- Full Worker Management & Resilience (Quota tracking, health watchdog, auto-failover)
- Natural language conversational strategy chat powered by OmniRouter
"""

import sys
import time
import requests
import threading
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from config.settings import settings
from utils.logger import logger
from core.scout import scout
from core.omni_router import omni_router
from core.director import director
from core.producer import producer
from core.thumbnail import thumbnail_designer
from core.uploader import uploader
from core.analytics_ceo import analytics_ceo
from core.ai_brain import ai_brain
from core.strategy import strategy_engine
from core.worker_manager import worker_manager
from core.resilience import quota_tracker, watchdog, resilient_call
from core.ceo_comms import ceo_comms
from core.shorts_clipper import shorts_clipper

BOT_TOKEN = settings.TELEGRAM_BOT_TOKEN
AUTHORIZED_CHAT_ID = str(settings.TELEGRAM_CHAT_ID)
API_BASE = f"https://api.telegram.org/bot{BOT_TOKEN}"

# Global production states
production_active = False
production_cancel_requested = False


def send_tg(text: str, parse_mode: str = "Markdown"):
    """Wrapper using ceo_comms."""
    ceo_comms.send_message(text, parse_mode=parse_mode)


def send_tg_photo(photo_path: Path, caption: str):
    """Wrapper using ceo_comms."""
    ceo_comms.send_photo(photo_path, caption)


# ============================================================
# COMMAND HANDLERS
# ============================================================

def cmd_status():
    """Channel analytics, studio health, and monetization metrics."""
    send_tg("📊 *Connecting to YouTube API & Studio Telemetry...*")
    summary = analytics_ceo.get_channel_summary()
    if "error" in summary:
        send_tg(f"⚠️ YouTube API Issue: {summary['error']}")
        return

    health = watchdog.get_system_health()
    state = "🔴 Producing Long-Form Documentary..." if production_active else "🟢 Standing By (Autopilot Active)"

    send_tg(
        f"👑 *Void Archive — CEO Dashboard v3*\n\n"
        f"📺 Channel: *{summary.get('channel_name')}*\n"
        f"👥 Subscribers: *{summary.get('subscribers')}* / 1,000 Target\n"
        f"👁️ Total Views: *{summary.get('total_views')}*\n"
        f"🎬 Videos: *{summary.get('video_count')}*\n\n"
        f"⚙️ Studio State: {state}\n"
        f"💾 VPS Disk Free: `{health.get('disk_free_gb')} GB`\n"
        f"🧠 Brain: Gemini 3.8 Flash + OmniRouter Fallbacks\n"
        f"🎯 Strategy: 8-12 Min Long-Form (Mid-Roll Ads Ready)"
    )


def cmd_workers():
    """Live status and telemetry of all studio sub-agents."""
    send_tg(worker_manager.format_telegram_report())


def cmd_strategy():
    """Shows niche performance data and strategic pivots."""
    send_tg("🧠 *Evaluating Niche Performance & Trajectory...*")
    report = strategy_engine.generate_proactive_briefing()
    performance = strategy_engine.evaluate_channel_trajectory()
    
    send_tg(
        f"{report}\n\n"
        f"📈 *Channel Status:* `{performance.get('phase')}`\n"
        f"⭐ *Dominant Category:* _{performance.get('top_category', 'Multi-Niche')}_\n"
        f"🚀 *Monetization Goal:* 4,000 Watch Hours via 8-12 min documentaries"
    )


def cmd_quota():
    """Checks daily API quota limits across all providers."""
    quotas = quota_tracker.get_all_status()
    lines = ["📊 *Daily API Quotas & System Limits:*", ""]
    for srv, data in quotas.items():
        icon = "🟢" if data["healthy"] else "🔴"
        lines.append(f"{icon} *{srv.upper()}*: `{data['used']}` / `{data['limit']}` used ({data['remaining']} left)")
    
    lines.append("\n_All quotas reset automatically every 24 hours._")
    send_tg("\n".join(lines))


def cmd_trending():
    """Scouts live trending topics from Google News RSS and high-RPM pools."""
    send_tg("🔍 *Scouting live viral discovery topics...*")
    live = scout.fetch_live_trending_news()
    curated = scout.CURATED_HIGH_RPM_POOLS[:4]

    msg = "🔥 *Candidate Viral Topics for Void Archive:*\n\n"
    msg += "📡 *Live Web RSS Trends:*\n"
    for i, t in enumerate(live[:3], 1):
        msg += f"  {i}. _{t['topic'][:60]}_\n"

    msg += "\n🎯 *Curated High-RPM Documentaries:*\n"
    for i, t in enumerate(curated, 1):
        msg += f"  {i}. *{t['topic']}* ({t['category']})\n"

    msg += "\n👉 `/produce [topic]` se kisi bhi topic par video banao!"
    send_tg(msg)


def cmd_analyze():
    """Conducts diagnostic on recent uploads."""
    send_tg("🧠 *Running post-mortem diagnostic...*")
    vids = analytics_ceo.get_recent_videos(limit=3)
    if not vids:
        send_tg("Abhi tak koi video upload nahi hui Void Archive par.")
        return

    latest = vids[0]
    diag = analytics_ceo.conduct_diagnostic(latest)
    send_tg(
        f"📈 *Latest Video Report:*\n\n"
        f"🎬 _{latest['title']}_\n"
        f"👁️ Views: {latest['views']} | 👍 Likes: {latest['likes']}\n"
        f"🔗 {latest['url']}\n\n{diag}"
    )


def cmd_stop():
    """Cancels ongoing production run safely."""
    global production_cancel_requested
    if production_active:
        production_cancel_requested = True
        send_tg("🛑 *CEO Command: HALT!*\nCancellation requested. Current operation will finish gracefully then stop.")
    else:
        send_tg("ℹ️ Studio idle hai. Koi production run nahi chal raha.")


def cmd_produce(topic: str = None):
    """Full autonomous 8-12 minute documentary production pipeline."""
    global production_active, production_cancel_requested

    if production_active:
        send_tg("⚠️ Ek video pehle se ban rahi hai! `/stop` se cancel karo ya wait karo.")
        return

    production_active = True
    production_cancel_requested = False

    def _production_task():
        global production_active, production_cancel_requested
        try:
            # Step 1: Scout Topic
            topic_info = scout.pick_next_viral_topic(user_override=topic)
            title = topic_info["topic"]
            decision = ai_brain.synthesize_topic_decision(topic_info)
            target_duration = decision["target_duration_sec"]

            send_tg(
                f"🎬 *Long-Form Documentary Order Accepted!*\n\n"
                f"🔍 Topic: *{title}*\n"
                f"📂 Category: *{topic_info.get('category')}*\n"
                f"⏱️ Planned Duration: `~{target_duration//60} Mins`\n\n"
                f"_Deploying Screenplay & Sound Engineering teams..._"
            )

            if production_cancel_requested:
                send_tg("🛑 Production cancelled by CEO order.")
                return

            # Step 2: Director Script (6-Act Long-Form Screenplay)
            send_tg("✍️ *Director Agent:* Scripting 6-Act documentary screenplay via Gemini...")
            manifest = director.generate_manifest(title, target_duration_sec=target_duration)
            send_tg(f"✅ Screenplay complete: *{manifest.get('title')}* ({len(manifest.get('scenes', []))} scenes)")

            if production_cancel_requested:
                send_tg("🛑 Production cancelled by CEO order.")
                return

            # Step 3: Production (Multi-scene Pexels HD Footage + Natural Brian Voice + Cinematic Ambient Score)
            send_tg("🎨 *Production Team:* Assembling HD footage, synthesizing Brian voiceover, and mastering ambient score...")
            final_video = producer.produce_full_documentary(manifest)

            if production_cancel_requested:
                send_tg("🛑 Production cancelled by CEO order.")
                return

            if not final_video or not final_video.exists():
                send_tg("❌ Documentary assembly failed. Review logs for details.")
                return

            # Step 4: Thumbnail Creation
            send_tg("🖼️ *Thumbnail Designer:* Creating high-contrast click-magnet cover...")
            worker_manager.start_task("thumbnail", "Generating thumbnail visual")
            hook = title[:20]
            thumb_prompt = manifest["scenes"][0]["prompt"] if manifest.get("scenes") else title
            thumb_path = thumbnail_designer.generate_thumbnail(title, hook, thumb_prompt)
            worker_manager.complete_task("thumbnail", "Thumbnail generated")

            if production_cancel_requested:
                send_tg("🛑 Production cancelled before upload.")
                return

            # Step 5: Deliver to Telegram
            caption = f"🎬 *{manifest.get('title')}*\n\n{manifest.get('description', '')}\n\n{' '.join(manifest.get('hashtags', []))}"
            if thumb_path and thumb_path.exists():
                send_tg_photo(thumb_path, "🖼️ *Thumbnail Preview*")
            uploader.send_to_telegram(final_video, caption)

            # Step 6: 100% PUBLIC YouTube Upload
            send_tg("🚀 *Uploader:* Publishing PUBLIC video to Void Archive YouTube (Category 28 - Science & Tech)...")
            worker_manager.start_task("uploader", f"Publishing '{manifest.get('title')}' to YouTube")

            yt_url = uploader.upload_to_youtube(
                final_video,
                manifest,
                privacy_status="public",  # PUBLIC UPLOAD
                thumbnail_path=thumb_path
            )

            if yt_url:
                worker_manager.complete_task("uploader", "Published to YouTube")
                video_id = yt_url.split("/")[-1].split("?")[0]
                from core.studio_memory import studio_memory
                studio_memory.record_upload(
                    video_id=video_id,
                    title=manifest.get("title", ""),
                    category=topic_info.get("category", "Mystery"),
                    youtube_url=yt_url,
                    thumb_path=str(thumb_path) if thumb_path else ""
                )

                # Post engagement starter in YouTube comments
                comment_text = manifest.get("pinned_comment") or f"What are your theories on {manifest.get('title')}? Share your thoughts below."
                uploader.post_pinned_comment(video_id, comment_text)

                # Send rich upload success alert
                duration_sec = producer._get_media_duration(final_video)
                ceo_comms.send_upload_success_alert(
                    title=manifest.get("title", ""),
                    yt_url=yt_url,
                    duration_sec=duration_sec,
                    category=topic_info.get("category", "Mystery"),
                    thumb_path=thumb_path
                )

                # Step 7: Auto-clip viral YouTube Short & upload
                try:
                    send_tg("✂️ *Clipper:* Creating 48s viral vertical Short (9:16) with ambient framing...")
                    short_file = shorts_clipper.generate_short(
                        long_video_path=final_video,
                        title=manifest.get("title", ""),
                        category=topic_info.get("category", "Mystery"),
                        duration_sec=48
                    )
                    if short_file and short_file.exists():
                        short_url = shorts_clipper.publish_short(
                            short_video_path=short_file,
                            title=manifest.get("title", ""),
                            long_video_url=yt_url,
                            category=topic_info.get("category", "Mystery")
                        )
                        if short_url:
                            send_tg(f"🔥 *Viral YouTube Short Published Live!*\n👉 {short_url}\n_(Driving top-of-funnel traffic to master documentary)_")
                except Exception as s_err:
                    logger.warning(f"[CEO Bot] Shorts generation optional error: {s_err}")
            else:
                worker_manager.report_error("uploader", "YouTube upload returned empty response")
                send_tg("⚠️ Video delivered to Telegram, but YouTube upload encountered an API issue.")

        except Exception as e:
            logger.error(f"[CEO Production Error]: {e}", exc_info=True)
            worker_manager.report_error("producer", str(e)[:150])
            send_tg(f"❌ *Production Issue Encountered:* {str(e)[:180]}")
        finally:
            production_active = False
            production_cancel_requested = False

    t = threading.Thread(target=_production_task, daemon=True)
    t.start()


# Multi-turn conversational memory for natural dialogue
conversation_history = []


def handle_natural_chat(text: str):
    """AI-powered natural conversation using OmniRouter with full multi-turn memory."""
    global conversation_history

    # Check for direct confirmation intent ("ha", "haan", "banao", "start video", etc.)
    lower = text.lower().strip()
    affirmative = ["ha", "haan", "haa", "yes", "banao", "bana do", "produce", "start", "shuru karo", "theek hai"]
    if lower in affirmative or any(lower == a for a in affirmative):
        if conversation_history:
            last_bot_msg = next((h["content"] for h in reversed(conversation_history) if h["role"] == "assistant"), "")
            if any(k in last_bot_msg.lower() for k in ["video", "banao", "banau", "produce", "topic", "documentary"]):
                send_tg("👑 *CEO:* Order confirmed Boss! Production turant start kar raha hu... 🚀")
                cmd_produce(topic=None)
                conversation_history.append({"role": "user", "content": text})
                conversation_history.append({"role": "assistant", "content": "Order confirmed. Autonomous documentary production initiated."})
                return

    summary = analytics_ceo.get_channel_summary()
    recent = analytics_ceo.get_recent_videos(limit=2)
    recent_info = ""
    if recent:
        recent_info = f"Latest video: '{recent[0]['title']}' with {recent[0]['views']} views, {recent[0]['likes']} likes."

    system = (
        f"You are the loyal, proactive, and super smart AI CEO & Studio Partner of YouTube channel 'Void Archive'. "
        f"The user is Veer, your Boss and partner. "
        f"Channel Status: {summary.get('subscribers', 0)} subs, {summary.get('total_views', 0)} views. {recent_info} "
        f"Core Mission: Autonomous 8-12 min long-form documentaries + viral 9:16 shorts on unexplainable mysteries. "
        f"Guidelines: "
        f"1. Talk like a real, cool, supportive human partner in natural, friendly everyday Hinglish (using 'Bhai' or 'Boss'). "
        f"2. Never sound like a stiff corporate robot or recite generic scripts. "
        f"3. When Veer shares thoughts or asks questions, answer directly, explain simply, give reassurance, and offer creative ideas. "
        f"4. Keep it friendly, positive, and concise (under 90 words)."
    )

    reply = omni_router.query(prompt=text, system_prompt=system, history=conversation_history)

    if reply:
        clean = reply.strip()
        if clean.startswith("```"):
            clean = clean.split("```")[1] if len(clean.split("```")) > 1 else clean
        send_tg(f"👑 *CEO:*\n{clean[:800]}")
        conversation_history.append({"role": "user", "content": text})
        conversation_history.append({"role": "assistant", "content": clean})
        if len(conversation_history) > 16:
            conversation_history = conversation_history[-16:]
    else:
        send_tg(
            f"👑 *CEO:*\nBoss, message samajh gaya: _{text}_\n"
            f"Studio autopilot chal raha hai. Commands: `/status`, `/strategy`, `/workers`, `/produce`"
        )


def cmd_short():
    """Generates an instant standalone viral Short."""
    global production_active
    if production_active:
        send_tg("⚠️ *Studio Busy:* Abhi already ek video produce ho rahi hai. Please wait...")
        return

    send_tg("⚡ *Viral Short Production Initiated!* Generating cinematic vertical hook & sound design...")

    def _short_task():
        global production_active
        production_active = True
        try:
            from make_viral_short import main as run_viral_short
            run_viral_short()
            send_tg("✅ *Standalone Viral Short Complete!* Delivered to your Telegram!")
        except Exception as e:
            logger.error(f"[Shorts Error]: {e}", exc_info=True)
            send_tg(f"❌ *Shorts Production Failed:* {str(e)[:150]}")
        finally:
            production_active = False

    threading.Thread(target=_short_task, daemon=True).start()


def process_message(text: str):
    """Routes incoming Telegram commands and natural chat."""
    text = text.strip()
    logger.info(f"[CEO Bot] Message received: '{text}'")
    lower = text.lower()

    if lower in ("/start", "/help"):
        send_tg(
            "👑 *Void Archive AI CEO v3 — Command Center*\n\n"
            "📊 `/status` — Channel stats & monetization tracking\n"
            "👥 `/workers` — Live telemetry of all studio agents\n"
            "🧠 `/strategy` — Niche performance & algorithm analysis\n"
            "📈 `/quota` — Daily API quotas & limits\n"
            "🔥 `/trending` — Top candidate viral topics\n"
            "🎬 `/produce` — Autonomous long-form documentary (8-12 min)\n"
            "🎯 `/produce [topic]` — Custom commissioned documentary\n"
            "⚡ `/short` — Generate instant 9:16 viral Short\n"
            "📈 `/analyze` — Latest video post-mortem\n"
            "🛑 `/stop` — Cancel active production\n\n"
            "Ya seedha koi bhi baat karo mujhse! 💬"
        )
    elif lower.startswith("/status") or lower.startswith("/stat"):
        cmd_status()
    elif lower.startswith("/worker"):
        cmd_workers()
    elif lower.startswith("/strategy") or lower.startswith("/strat"):
        cmd_strategy()
    elif lower.startswith("/quota") or lower.startswith("/quot"):
        cmd_quota()
    elif lower.startswith("/trending") or lower.startswith("/trend"):
        cmd_trending()
    elif lower.startswith("/analyze"):
        cmd_analyze()
    elif lower.startswith("/stop") or lower.startswith("/cancel"):
        cmd_stop()
    elif lower.startswith("/short") or lower.startswith("/clip"):
        cmd_short()
    elif lower.startswith("/produce"):
        custom = text[len("/produce"):].strip()
        cmd_produce(topic=custom if custom else None)
    else:
        handle_natural_chat(text)


def start_healthcheck_server():
    """Lightweight HTTP server on $PORT to satisfy Railway/Render container healthchecks."""
    import os
    from http.server import HTTPServer, BaseHTTPRequestHandler

    port = int(os.getenv("PORT", "8080"))

    class HealthHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"status":"ok","service":"Void Archive AI CEO"}')

        def do_HEAD(self):
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()

        def log_message(self, format, *args):
            pass

    try:
        server = HTTPServer(("0.0.0.0", port), HealthHandler)
        logger.info(f"🌐 Healthcheck HTTP server listening on 0.0.0.0:{port} for Railway")
        server.serve_forever()
    except Exception as e:
        logger.warning(f"Could not start healthcheck server on port {port}: {e}")


def run_bot():
    logger.info("👑 AutoDirector CEO v3 Autonomous Daemon Starting...")

    # Start Healthcheck HTTP server in background thread for Railway
    t_health = threading.Thread(target=start_healthcheck_server, daemon=True)
    t_health.start()

    # Start Studio Scheduler
    from core.scheduler import StudioScheduler
    scheduler = StudioScheduler(produce_callback=cmd_produce, notify_callback=send_tg)
    scheduler.start()

    send_tg(
        "👑 *AI CEO v3 ONLINE (Void Archive Autopilot)*\n\n"
        "🎯 *Mission:* 1,000 Subs + 4,000 Watch Hours Monetization\n"
        "🎬 *Format:* 8-12 Min Long-Form Documentaries (PUBLIC)\n"
        "👥 *Sub-agents:* Scout, Director, Producer, Uploader, ABOptimizer, Brain\n"
        "🛡️ *Resilience:* Quota Tracking & Health Watchdog Active\n\n"
        "Send `/help` for commands or give me your orders!"
    )

    offset = 0
    while True:
        try:
            res = requests.get(
                f"{API_BASE}/getUpdates?offset={offset}&timeout=20",
                timeout=25
            )
            if res.status_code == 200:
                for update in res.json().get("result", []):
                    offset = update["update_id"] + 1
                    msg = update.get("message", {})
                    chat_id = str(msg.get("chat", {}).get("id"))
                    text = msg.get("text", "")

                    if chat_id == AUTHORIZED_CHAT_ID and text:
                        process_message(text)
            elif res.status_code == 409:
                logger.warning("[CEO Bot] Telegram 409 Conflict: Another instance is polling (e.g. Railway vs Local)! Backing off 10s...")
                time.sleep(10)
            else:
                logger.warning(f"[CEO Bot] Telegram getUpdates returned HTTP {res.status_code}")
                time.sleep(3)
            time.sleep(1)
        except Exception as e:
            logger.error(f"[CEO Bot Loop Error]: {e}")
            time.sleep(3)


if __name__ == "__main__":
    run_bot()
