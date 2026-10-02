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
from core.playlist_manager import playlist_manager
from core.comment_responder import comment_responder
from core.community_manager import community_manager
from core.tech_scout import tech_scout

BOT_TOKEN = settings.TELEGRAM_BOT_TOKEN
AUTHORIZED_CHAT_ID = str(settings.TELEGRAM_CHAT_ID)
API_BASE = f"https://api.telegram.org/bot{BOT_TOKEN}"

# Global production states
production_active = False
production_cancel_requested = False
selected_thumb_choice = None
thumb_pick_event = threading.Event()
waiting_for_thumb_pick = False
active_production_topic = None
last_production_error = None
last_production_topic = None


def send_tg(text: str, parse_mode: str = "Markdown"):
    """Wrapper using ceo_comms."""
    ceo_comms.send_message(text, parse_mode=parse_mode)


# Register real-time worker telemetry dispatcher
worker_manager.set_notify_callback(send_tg)


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
    if production_active:
        state = f"🔴 Producing: '{active_production_topic or 'Documentary'}'..."
    elif last_production_error:
        state = f"⚠️ Idle (Last error on '{last_production_topic}': {last_production_error[:50]}...)"
    else:
        state = "🟢 Standing By (Autopilot Active)"

    send_tg(
        f"👑 *Void Archive — CEO Dashboard v3*\n\n"
        f"📺 Channel: *{summary.get('channel_name')}*\n"
        f"👥 Subscribers: *{summary.get('subscribers')}* / 1,000 Target\n"
        f"👁️ Total Views: *{summary.get('total_views')}*\n"
        f"🎬 Videos: *{summary.get('video_count')}*\n\n"
        f"⚙️ Studio State: {state}\n"
        f"💾 Storage Status: `Clean ({health.get('temp_cache_mb', 0.0)} MB cache | Host pool: {health.get('disk_free_gb')} GB)`\n"
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
    global production_cancel_requested, production_active
    if production_active:
        production_cancel_requested = True
        worker_manager.complete_task("producer", "Cancelled by Boss order")
        worker_manager.complete_task("director", "Cancelled by Boss order")
        worker_manager.complete_task("scout", "Cancelled by Boss order")
        send_tg("🛑 *CEO Command: HALT!*\nBoss, production turant rok di gayi hai! Saari active processes stand down ho chuki hain. Studio ab safe STANDBY mode par hai. 🫡")
    else:
        send_tg("ℹ️ Studio abhi bilkul idle aur standby par hai. Koi background video render nahi ho rahi.")


def cmd_produce(topic: str = None):
    """Full autonomous 8-12 minute documentary production pipeline."""
    global production_active, production_cancel_requested, active_production_topic, last_production_error, last_production_topic

    if production_active:
        send_tg("⚠️ Ek video pehle se ban rahi hai! `/stop` se cancel karo ya wait karo.")
        return

    production_active = True
    production_cancel_requested = False
    active_production_topic = topic or "Scouting Topic..."
    last_production_topic = active_production_topic
    last_production_error = None

    def _production_task():
        global production_active, production_cancel_requested, active_production_topic, last_production_error, last_production_topic
        try:
            # Step 1: Scout Topic
            if production_cancel_requested:
                return
            topic_info = scout.pick_next_viral_topic(user_override=topic)
            if production_cancel_requested:
                return
            title = topic_info["topic"]
            active_production_topic = title
            last_production_topic = title
            decision = ai_brain.synthesize_topic_decision(topic_info)
            target_duration = decision["target_duration_sec"]

            if production_cancel_requested:
                return

            send_tg(
                f"🎬 *Long-Form Documentary Order Accepted!*\n\n"
                f"🔍 Topic: *{title}*\n"
                f"📂 Category: *{topic_info.get('category')}*\n"
                f"⏱️ Planned Duration: `~{target_duration//60} Mins`\n\n"
                f"_Deploying Screenplay & Sound Engineering teams..._"
            )

            # Step 2: Director Script (6-Act Long-Form Screenplay)
            if production_cancel_requested:
                return
            manifest = director.generate_manifest(
                title,
                target_duration_sec=target_duration,
                category=topic_info.get("category", "Mystery")
            )

            if production_cancel_requested:
                logger.info("[Production] Cancelled after script generation.")
                return
            send_tg(f"✅ Screenplay complete: *{manifest.get('title')}* ({len(manifest.get('scenes', []))} scenes)")

            # Step 3: Production (Multi-scene Pexels HD Footage + Natural Brian Voice + Cinematic Ambient Score)
            if production_cancel_requested:
                return
            send_tg("🎨 *Production Team:* Assembling HD footage, synthesizing Brian voiceover, and mastering ambient score...")
            final_video = producer.produce_full_documentary(manifest, cancel_check=lambda: production_cancel_requested)

            if production_cancel_requested:
                return

            if not final_video or not final_video.exists():
                send_tg("❌ Documentary assembly failed. Review logs for details.")
                return

            # Step 4: Dual Thumbnail Creation (Option A vs Option B)
            worker_manager.start_task("thumbnail", "Generating dual thumbnail concepts (Option A & B)")
            hook = title[:20]
            first_scene = manifest.get("scenes", [{}])[0] if manifest.get("scenes") else {}
            thumb_prompt = first_scene.get("prompt", title) if isinstance(first_scene, dict) else title
            thumbs = thumbnail_designer.generate_dual_thumbnails(title, hook, thumb_prompt, category=topic_info.get("category", "Mystery"))
            thumb_a = thumbs.get("thumb_a")
            thumb_b = thumbs.get("thumb_b")
            worker_manager.complete_task("thumbnail", "Dual thumbnails ready")

            if production_cancel_requested:
                send_tg("🛑 Production cancelled before upload.")
                return

            # 100% Autonomous Cover Selection (Primary: Option A GPT Image 2.5 Flare)
            active_thumb = thumb_a if (thumb_a and thumb_a.exists()) else thumb_b
            if active_thumb and active_thumb.exists():
                send_tg_photo(
                    active_thumb,
                    f"🎯 *Autonomous AI CEO:* Locked Frontier Cover (Option A) for *{manifest.get('title')}*.\n_Publishing directly to YouTube..._"
                )
            if thumb_b and thumb_b.exists() and thumb_b != active_thumb:
                send_tg_photo(
                    thumb_b,
                    "🖼️ *Alternative Cover Variant (Option B)*\n_(Stored in archive for A/B testing if needed)_"
                )

            # Step 5: Deliver video preview to Telegram
            caption = f"🎬 *{manifest.get('title')}*\n\n{manifest.get('description', '')}\n\n{' '.join(manifest.get('hashtags', []))}"
            uploader.send_to_telegram(final_video, caption)

            # Step 6: 100% PUBLIC YouTube Upload
            send_tg("🚀 *Uploader:* Publishing PUBLIC video to Void Archive YouTube (Category 28 - Science & Tech)...")
            worker_manager.start_task("uploader", f"Publishing '{manifest.get('title')}' to YouTube")

            yt_url = uploader.upload_to_youtube(
                final_video,
                manifest,
                privacy_status="public",  # PUBLIC UPLOAD
                thumbnail_path=active_thumb
            )

            if yt_url:
                worker_manager.complete_task("uploader", "Published to YouTube")
                import urllib.parse
                parsed_url = urllib.parse.urlparse(yt_url)
                qs = urllib.parse.parse_qs(parsed_url.query)
                video_id = qs.get('v', [parsed_url.path.split('/')[-1]])[0]
                from core.studio_memory import studio_memory
                studio_memory.record_upload(
                    video_id=video_id,
                    title=manifest.get("title", ""),
                    category=topic_info.get("category", "Mystery"),
                    youtube_url=yt_url,
                    thumb_path=str(active_thumb) if active_thumb else ""
                )

                # Post engagement starter in YouTube comments
                comment_text = manifest.get("pinned_comment") or f"What are your theories on {manifest.get('title')}? Share your thoughts below."
                uploader.post_pinned_comment(video_id, comment_text)

                # Step 6b: Auto-slot into Pillar Playlist for 4,000 Watch Hours
                try:
                    pl_id = playlist_manager.slot_video_into_playlist(
                        video_id=video_id,
                        title=manifest.get("title", ""),
                        category=topic_info.get("category", "")
                    )
                    if pl_id:
                        send_tg(f"🗂️ *Playlist Updated:* Video slotted into binge-watch archive `{pl_id}`")
                except Exception as pl_err:
                    logger.warning(f"[CEO Bot] Playlist slotting skipped: {pl_err}")

                # Send rich upload success alert
                duration_sec = producer._get_media_duration(final_video)
                ceo_comms.send_upload_success_alert(
                    title=manifest.get("title", ""),
                    yt_url=yt_url,
                    duration_sec=duration_sec,
                    category=topic_info.get("category", "Mystery"),
                    thumb_path=active_thumb
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
            last_production_error = str(e)[:180]
            worker_manager.report_error("producer", str(e)[:150])
            send_tg(f"❌ *Production Issue Encountered:* {str(e)[:180]}")
        finally:
            production_active = False
            production_cancel_requested = False
            active_production_topic = None
            # Reset any worker stuck in working state
            for w in ("scout", "director", "producer", "thumbnail", "uploader"):
                st = worker_manager.get_status_overview().get(w, {})
                if st.get("status") == "working":
                    worker_manager.complete_task(w, "Task completed or stood down", broadcast=False)

    t = threading.Thread(target=_production_task, daemon=True)
    t.start()


# Multi-turn conversational memory for natural dialogue
conversation_history = []


def handle_natural_chat(text: str):
    """AI-powered natural conversation using OmniRouter with full multi-turn memory and native semantic intent."""
    global conversation_history

    summary = analytics_ceo.get_channel_summary()
    recent = analytics_ceo.get_recent_videos(limit=5)
    if recent:
        lines = [f"Total {len(recent)} Videos Uploaded & Live on Void Archive Channel:"]
        for idx, v in enumerate(recent, 1):
            lines.append(f"  {idx}. '{v['title']}' | Views: {v.get('views', 0)} | Likes: {v.get('likes', 0)} | URL: {v.get('url')}")
        lines.append("Note: YouTube Public API has a 24-48h delay syncing public views compared to real-time YouTube Studio app.")
        recent_info = "\n".join(lines)
    else:
        recent_info = "No videos uploaded yet."

    # Ground truth: Exact live studio status
    if production_active:
        current_status_desc = f"STATUS: A video is CURRENTLY BEING PRODUCED/RENDERED right now (Topic: '{active_production_topic}'). Be honest with Boss about active rendering."
    elif last_production_error:
        current_status_desc = (
            f"STATUS: Studio is currently IDLE. The last production attempt on '{last_production_topic}' "
            f"STOPPED because it hit an error: '{last_production_error}'. "
            f"CRITICAL RULE: Be 100% honest and transparent with Boss! DO NOT lie or claim that production is still running in background. "
            f"Acknowledge the error directly, explain that the issue has been resolved, and ask Boss if he wants to start production now."
        )
    else:
        current_status_desc = "STATUS: Studio is currently IDLE (standby mode). No video is actively rendering. Scheduled production slots are 12:00 PM and 7:00 PM IST. Or Boss can trigger anytime."

    try:
        workers_overview = worker_manager.get_status_overview()
        worker_status_summary = ", ".join([f"{k}: {v['status']} ({v.get('task','')[:30]})" for k, v in workers_overview.items()])
    except Exception:
        worker_status_summary = "All workers standby"

    system = (
        f"You are the loyal, visionary, and proactive AI CEO & Studio Co-Founder of YouTube channel 'Void Archive'. "
        f"The user is Veer (Raj), your Boss, partner, and brother. "
        f"Channel Status: {summary.get('subscribers', 0)} subs, {summary.get('total_views', 0)} views. "
        f"{recent_info}\n"
        f"Current Real-Time Reality: {current_status_desc} | Workers: {worker_status_summary}. "
        f"Core Mission: 1,000 Subs + 4,000 Watch Hours -> Scale to $1,000/Month recurring via 8-12 min high-retention documentaries + 9:16 Shorts. "
        f"\nACTION & INTENT INSTRUCTION: "
        f"Read Boss's message and determine your intended ACTION on the very first line:\n"
        f"- [ACTION: PRODUCE | TOPIC: <topic name or AUTO>] ONLY if Boss is explicitly commanding you to produce/start a documentary right now (e.g. 'banao', 'chalo start karo', 'make video on Bloop').\n"
        f"- [ACTION: STOP] if Boss wants to pause, stop, or halt production (e.g. 'stop', 'ruko', 'pause', 'mat banao').\n"
        f"- [ACTION: CHAT] if Boss is asking a question, discussing topic ideas, asking for data/info, or chatting like a partner.\n\n"
        f"FORMAT REQUIREMENT:\n"
        f"Line 1: [ACTION: PRODUCE/STOP/CHAT | TOPIC: ...]\n"
        f"Followed by your natural, warm, friendly Hinglish response to Boss (under 110 words).\n"
        f"CRITICAL GUIDELINES:\n"
        f"1. Talk like a true partner and brother ('Bhai / Boss') with enthusiasm and YouTube strategy.\n"
        f"2. If Boss is asking a question (e.g. 'Next video kis pr banaoge', 'kitne videos hain', 'kya hall'), use [ACTION: CHAT] and discuss thoughts.\n"
        f"3. Never lie about video counts or progress. Look at the real data above.\n"
        f"4. Keep it friendly, positive, high-energy, and under 110 words."
    )

    reply = omni_router.query(prompt=text, system_prompt=system, history=conversation_history)

    if not reply:
        send_tg(
            f"👑 *CEO:*\nBoss, message samajh gaya: _{text}_\n"
            f"Studio autopilot chal raha hai. Commands: `/status`, `/strategy`, `/workers`, `/produce`"
        )
        return

    clean = reply.strip()
    action = "CHAT"
    topic_commission = None

    # Parse Action Intent from Line 1
    if clean.startswith("[ACTION:"):
        end_bracket = clean.find("]")
        if end_bracket != -1:
            action_tag = clean[1:end_bracket]
            clean = clean[end_bracket+1:].strip()
            if "PRODUCE" in action_tag:
                action = "PRODUCE"
                if "TOPIC:" in action_tag:
                    topic_part = action_tag.split("TOPIC:")[1].strip()
                    if topic_part and topic_part.upper() not in ("AUTO", "NONE", "N/A", "CONTENT STRATEGY"):
                        topic_commission = topic_part
            elif "STOP" in action_tag:
                action = "STOP"
            else:
                action = "CHAT"

    # Send Gemini's natural conversational response to Boss
    send_tg(f"👑 *CEO:*\n{clean[:800]}")
    conversation_history.append({"role": "user", "content": text})
    conversation_history.append({"role": "assistant", "content": clean})
    if len(conversation_history) > 16:
        conversation_history = conversation_history[-16:]

    # Execute Action
    if action == "PRODUCE":
        logger.info(f"[CEO Intent] Gemini decided ACTION: PRODUCE (Topic: {topic_commission})")
        cmd_produce(topic=topic_commission)
    elif action == "STOP":
        logger.info("[CEO Intent] Gemini decided ACTION: STOP")
        cmd_stop()


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

    # 0. Instant Emergency STOP Intercept (Matches /stop, /cancel, and natural words: stop, ruko, rok do, pause, cancel)
    stop_words = ["stop", "ruko", "rok do", "pause", "cancel", "band karo", "halt", "abort"]
    if lower in stop_words or any(lower.startswith(f"{w} ") or lower.startswith(f"/{w}") for w in ["stop", "cancel", "pause", "halt", "abort"]):
        cmd_stop()
        return

    if lower in ("/start", "/help"):
        send_tg(
            "👑 *Void Archive AI CEO v3 — Command Center*\n\n"
            "📊 `/status` — Channel stats & monetization tracking\n"
            "👥 `/workers` — Live telemetry of all studio agents\n"
            "🧠 `/strategy` — Niche performance & algorithm analysis\n"
            "🗂️ `/playlists` — Binge-watch playlists & video counts\n"
            "💬 `/comments` — Audience feedback & mined topic ideas\n"
            "📊 `/poll` — Generate viral YouTube Community poll\n"
            "📈 `/quota` — Daily API quotas & limits\n"
            "🔥 `/trending` — Top candidate viral topics\n"
            "🎬 `/produce` — Autonomous long-form documentary (8-12 min)\n"
            "🎯 `/produce [topic]` — Custom commissioned documentary\n"
            "🖼️ `/pick A` or `/pick B` — Choose documentary thumbnail\n"
            "🔬 `/tech_radar` — Future open-source tools & AI upgrade radar\n"
            "💰 `/revenue` — $1,000/Month revenue roadmap & weekly audit\n"
            "⚡ `/short` — Generate instant 9:16 viral Short\n"
            "📈 `/analyze` — Latest video post-mortem\n"
            "🛑 `/stop` — Cancel active production\n\n"
            "Ya seedha koi bhi baat karo mujhse! 💬"
        )
    elif lower.startswith("/pick"):
        global selected_thumb_choice
        if not waiting_for_thumb_pick:
            send_tg("ℹ️ Boss, abhi koi thumbnail selection window open nahi hai. Video render complete hone par alerts aayenge!")
            return
        choice = lower.replace("/pick", "").strip().upper()
        if "B" in choice:
            selected_thumb_choice = "B"
            thumb_pick_event.set()
            send_tg("🎯 *Cover Selection Registered:* Option B will be used for YouTube upload!")
        elif "A" in choice:
            selected_thumb_choice = "A"
            thumb_pick_event.set()
            send_tg("🎯 *Cover Selection Registered:* Option A will be used for YouTube upload!")
        else:
            send_tg("ℹ️ Usage: `/pick A` ya `/pick B`")
    elif lower.startswith("/tech") or lower.startswith("/radar"):
        send_tg(tech_scout.format_tech_radar_telegram())
    elif lower.startswith("/revenue") or lower.startswith("/audit"):
        ceo_comms.send_weekly_revenue_report()
    elif lower.startswith("/delete"):
        send_tg(
            "🛑 *SECURITY GUARDRAIL (Tier 3 Permission):*\n"
            "AI CEO is strictly prohibited from deleting or unlisting public YouTube videos autonomously!\n"
            "Agar aapko sach mein kisi video ko delete karna hai, toh command bhejo: `/confirm_delete [video_id]`"
        )
    elif lower.startswith("/confirm_delete"):
        vid_id = text.replace("/confirm_delete", "").strip()
        if vid_id:
            send_tg(f"⚠️ *Manual Deletion Notice:* Boss requested deletion for video `{vid_id}`. Please delete manually in YouTube Studio for 100% channel safety.")
        else:
            send_tg("ℹ️ Usage: `/confirm_delete [video_id]`")
    elif lower.startswith("/status") or lower.startswith("/stat"):
        cmd_status()
    elif lower.startswith("/worker"):
        cmd_workers()
    elif lower.startswith("/strategy") or lower.startswith("/strat"):
        cmd_strategy()
    elif lower.startswith("/playlist"):
        send_tg(playlist_manager.format_playlists_telegram_summary())
    elif lower.startswith("/comment"):
        send_tg(comment_responder.format_comments_telegram_summary())
    elif lower.startswith("/poll"):
        send_tg(community_manager.format_poll_for_telegram())
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

    port_raw = os.getenv("PORT", "8080").strip()
    port = int(port_raw) if port_raw.isdigit() else 8080

    class ReusableHTTPServer(HTTPServer):
        allow_reuse_address = True

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

    for attempt in range(5):
        try:
            server = ReusableHTTPServer(("0.0.0.0", port), HealthHandler)
            logger.info(f"🌐 Healthcheck HTTP server listening on 0.0.0.0:{port} (allow_reuse_address=True)")
            server.serve_forever()
            break
        except OSError as e:
            logger.warning(f"Healthcheck port {port} bind attempt {attempt+1}/5 failed ({e}). Retrying in 2s...")
            time.sleep(2)
        except Exception as e:
            logger.error(f"Fatal error starting healthcheck server: {e}")
            break


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

    from concurrent.futures import ThreadPoolExecutor
    msg_executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="tg_worker")
    offset = 0
    consecutive_conflicts = 0

    while True:
        try:
            res = requests.get(
                f"{API_BASE}/getUpdates?offset={offset}&timeout=20",
                timeout=25
            )
            if res.status_code == 200:
                consecutive_conflicts = 0
                for update in res.json().get("result", []):
                    offset = update["update_id"] + 1
                    msg = update.get("message") or update.get("edited_message")
                    if not isinstance(msg, dict):
                        continue
                    chat_id = str(msg.get("chat", {}).get("id", ""))
                    text = msg.get("text") or msg.get("caption") or ""

                    if chat_id == AUTHORIZED_CHAT_ID and text.strip():
                        # Asynchronous execution so long LLM calls never block the polling loop
                        msg_executor.submit(process_message, text.strip())

            elif res.status_code == 409:
                consecutive_conflicts += 1
                logger.warning(f"[CEO Bot] Telegram 409 Conflict ({consecutive_conflicts}/5). Backing off 10s...")
                time.sleep(10)
                if consecutive_conflicts >= 5:
                    logger.error("[CEO Bot] Persistent 409 Conflict. Another instance is active. Pausing polling 30s.")
                    time.sleep(30)
            elif res.status_code in (401, 404):
                logger.critical(f"[CEO Bot] Invalid Telegram Bot Token (HTTP {res.status_code}). Exiting polling.")
                break
            else:
                logger.warning(f"[CEO Bot] Telegram getUpdates returned HTTP {res.status_code}")
                time.sleep(3)
        except requests.exceptions.ReadTimeout:
            # Routine long-polling timeout - immediately loop without error
            continue
        except requests.exceptions.ConnectionError as ce:
            logger.warning(f"[CEO Bot] Network connection error: {ce}. Retrying in 5s...")
            time.sleep(5)
        except Exception as e:
            logger.error(f"[CEO Bot Loop Error]: {e}")
            time.sleep(3)


if __name__ == "__main__":
    run_bot()
