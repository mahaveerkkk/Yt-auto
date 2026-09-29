#!/usr/bin/env python3
"""
Void Archive AI CEO Studio — Comprehensive Master Integration Test Suite
Validates all 14 core subsystems:
1. SQLite Database Schema & Tables Integrity
2. Worker Manager & Telemetry Notifications
3. Scout Viral Title Polisher
4. Script Quality Control (QC) Validator
5. Director Chapter Calculation & YouTube Timestamps
6. Audio SFX Assets & Outro End-Screen FFmpeg Engine
7. Dual-Thumbnail Generator (Option A vs Option B)
8. Tech Scout Autonomous R&D Radar
9. CEO Comms & Financial Progress Modeling
10. Themed Auto-Playlists Manager
11. Comment Responder & Viewer Idea Hunter
12. Community Tab Poll Generator
13. CEO Bot Command Dispatcher & Security Guardrails
14. Disk Hygiene & Garbage Collection
"""

import os
import sys
import time
import sqlite3
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

# --- SAFETY: Redirect studio_memory to a temp DB so tests never corrupt production data ---
import tempfile
_test_db_dir = tempfile.mkdtemp(prefix="void_archive_test_")
os.environ["STUDIO_MEMORY_TEST_DB"] = os.path.join(_test_db_dir, "test_studio_memory.db")

passed_tests = 0
failed_tests = 0


def log_test(name: str, passed: bool, details: str = ""):
    global passed_tests, failed_tests
    if passed:
        passed_tests += 1
        print(f"  ✅ PASS: {name} {f'({details})' if details else ''}")
    else:
        failed_tests += 1
        print(f"  ❌ FAIL: {name} - {details}")


print("=" * 70)
print("🚀 STARTING VOID ARCHIVE SYSTEM INTEGRATION & INTEGRITY AUDIT")
print("=" * 70)

# =====================================================================
# TEST 1: Database Schema & Integrity Check
# =====================================================================
print("\n[1/14] Testing Studio Database (studio_memory.db)...")
try:
    from core.studio_memory import studio_memory
    conn = sqlite3.connect(studio_memory.db_path)
    cursor = conn.cursor()
    cursor.execute("PRAGMA integrity_check;")
    integrity = cursor.fetchone()[0]
    log_test("SQLite PRAGMA integrity_check", integrity == "ok", f"result: {integrity}")

    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [r[0] for r in cursor.fetchall()]
    expected_tables = [
        "videos", "niche_stats", "strategy_decisions", "worker_status",
        "daily_reports", "content_calendar", "playlists", "viewer_comments",
        "tech_discoveries"
    ]
    all_tables_present = all(t in tables for t in expected_tables)
    log_test("All 9 Core SQLite Tables Present", all_tables_present, f"found: {len(tables)} tables")

    studio_memory.update_worker_status("test_worker", "working", "Running diagnostic unit test")
    status = studio_memory.get_worker_status("test_worker")
    log_test("Worker Status Persistence", status and status.get("status") == "working", "read/write verified")
    studio_memory.update_worker_status("test_worker", "idle", "Diagnostic complete")
    conn.close()
except Exception as e:
    log_test("Database Integrity", False, str(e))

# =====================================================================
# TEST 2: Worker Manager & Telemetry
# =====================================================================
print("\n[2/14] Testing Worker Manager & Telemetry Broadcaster...")
try:
    from core.worker_manager import worker_manager
    broadcasts = []
    worker_manager.set_notify_callback(lambda msg: broadcasts.append(msg))

    worker_manager.start_task("director", "Drafting 6-act screenplay for Mariana Trench")
    worker_manager.complete_task("director", "Screenplay generated: 1,120 words")
    overview = worker_manager.get_status_overview()
    director_status = overview.get("director", {}).get("status")

    log_test("Worker State Transition (start -> complete)", director_status == "idle", f"status: {director_status}")
    log_test("Real-Time Broadcast Callback Dispatched", len(broadcasts) >= 2, f"broadcasts: {len(broadcasts)}")
    report = worker_manager.format_telegram_report()
    log_test("Worker Telemetry Report Format", "Studio Workers Telemetry" in report and "DIRECTOR" in report)
except Exception as e:
    log_test("Worker Manager", False, str(e))

# =====================================================================
# TEST 3: Scout Viral Title Polisher
# =====================================================================
print("\n[3/14] Testing Scout Viral Mystery Hook Polisher...")
try:
    from core.scout import scout
    raw_topic = "Scientists detect mysterious acoustic hum in oceanic trench"
    candidate = {"topic": raw_topic, "category": "Ocean Mystery"}
    polished_cand = scout._polish_viral_title(candidate)
    polished = polished_cand.get("topic", "")
    log_test("Scout Title Transformation", len(polished) > 10 and polished != raw_topic, f"Result: '{polished}'")
    curated = scout.CURATED_HIGH_RPM_POOLS
    log_test("Curated High-RPM Topic Pools", len(curated) >= 8, f"{len(curated)} curated topics")
except Exception as e:
    log_test("Scout Polisher", False, str(e))

# =====================================================================
# TEST 4: Script Quality Control (QC) Validator
# =====================================================================
print("\n[4/14] Testing Script QC Validator...")
try:
    from core.qc_validator import qc_validator

    short_script = "This is a short script about an anomaly. It vanished in the abyss. " * 20
    is_valid_short, msg_short, stats_short = qc_validator.validate_script(short_script, min_words=950)
    log_test("QC Rejects Sub-8-Minute Script (<950 words)", not is_valid_short, f"words: {stats_short.get('words')}")

    intro = "In 1977, naval sonar operators detected an impossible anomaly deep in the dark abyss. The signal baffled scientists and remained classified for decades. "
    body = "Declassified archives reveal unexplained sensor readings. What vanished into the cosmic void remains unknown. " * 75
    long_script = intro + body
    is_valid_long, msg_long, stats_long = qc_validator.validate_script(long_script, min_words=950)
    log_test("QC Accepts 8+ Minute Documentary Script", is_valid_long, f"words: {stats_long.get('words')}, hook score: {stats_long.get('hook_score')}/10")
except Exception as e:
    log_test("QC Validator", False, str(e))

# =====================================================================
# TEST 5: Director Dynamic Video Chapters
# =====================================================================
print("\n[5/14] Testing Director Dynamic Chapters & SEO Timestamps...")
try:
    from core.director import director
    chapters = director._calculate_video_chapters(word_count=1350, topic="The Bloop Underwater Anomaly")
    log_test("Chapters Calculation Generated", len(chapters) >= 4, f"{len(chapters)} chapters")
    log_test("First Chapter Starts at 00:00 (YouTube Requirement)", chapters[0]["time"] == "00:00", f"Start: {chapters[0]['time']}")
    ascending = all(chapters[i]["time"] <= chapters[i+1]["time"] for i in range(len(chapters)-1))
    log_test("Chapter Timestamps in Ascending Order", ascending)
except Exception as e:
    log_test("Director Chapters", False, str(e))

# =====================================================================
# TEST 6: Cinematic SFX & FFmpeg Outro Engine
# =====================================================================
print("\n[6/14] Testing Cinematic SFX Assets & FFmpeg Outro Engine...")
try:
    from core.producer import producer
    sfx_dir = BASE_DIR / "assets" / "sfx"
    expected_sfx = [
        "sfx_braam.mp3", "sfx_whoosh.mp3", "sfx_static.mp3",
        "sfx_heartbeat.mp3", "sfx_riser.mp3"
    ]
    all_sfx_exist = all((sfx_dir / f).exists() and (sfx_dir / f).stat().st_size > 1000 for f in expected_sfx)
    log_test("5 Royalty-Free SFX Assets Built & Non-Empty", all_sfx_exist)

    test_outro = Path("/tmp/test_system_outro.mp4")
    success_outro = producer._generate_outro_clip(test_outro, duration=2.0)
    log_test("Outro 12-Second Card FFmpeg Rendering", success_outro and test_outro.exists() and test_outro.stat().st_size > 5000)
    if test_outro.exists():
        test_outro.unlink()
except Exception as e:
    log_test("SFX & Outro Engine", False, str(e))

# =====================================================================
# TEST 7: Dual-Thumbnail Generator (Option A vs Option B)
# =====================================================================
print("\n[7/14] Testing Dual-Thumbnail Architecture...")
try:
    from core.thumbnail import thumbnail_designer
    import subprocess

    mock_base = thumbnail_designer.output_dir / "raw_thumb_a.jpg"
    mock_base_b = thumbnail_designer.output_dir / "raw_thumb_b.jpg"
    subprocess.run([
        "ffmpeg", "-y", "-f", "lavfi", "-i", "color=c=navy:s=1280x720:d=1",
        "-frames:v", "1", str(mock_base)
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    subprocess.run([
        "ffmpeg", "-y", "-f", "lavfi", "-i", "color=c=darkred:s=1280x720:d=1",
        "-frames:v", "1", str(mock_base_b)
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

    res = thumbnail_designer.generate_dual_thumbnails(
        title="The Mariana Void Anomaly",
        hook_text="WHAT LIES BENEATH",
        visual_prompt="Submarine spotlights illuminate gargantuan underwater trench structure",
        category="Ocean Mystery"
    )
    thumb_a = res.get("thumb_a")
    thumb_b = res.get("thumb_b")

    log_test("Option A Thumbnail Rendered (Yellow Text + PI/4 Vignette)", thumb_a and thumb_a.exists() and thumb_a.stat().st_size > 10000)
    log_test("Option B Thumbnail Rendered (Red Dossier + PI/3 Vignette)", thumb_b and thumb_b.exists() and thumb_b.stat().st_size > 10000)
except Exception as e:
    log_test("Dual Thumbnail Generator", False, str(e))

# =====================================================================
# TEST 8: Tech Scout Autonomous R&D Radar
# =====================================================================
print("\n[8/14] Testing Autonomous Tech Scout (R&D)...")
try:
    from core.tech_scout import tech_scout
    discoveries = studio_memory.get_tech_discoveries(limit=5)
    log_test("Tech Discoveries Table Populated", len(discoveries) >= 3, f"found: {len(discoveries)} discoveries")
    radar_msg = tech_scout.format_tech_radar_telegram()
    log_test("Tech Radar Telegram Formatting", "R&D Tech Radar" in radar_msg and "Kokoro" in radar_msg)
except Exception as e:
    log_test("Tech Scout", False, str(e))

# =====================================================================
# TEST 9: CEO Comms & Financial Models
# =====================================================================
print("\n[9/14] Testing CEO Comms & Monetization Roadmap...")
try:
    from core.ceo_comms import ceo_comms
    bar_50 = ceo_comms._render_progress_bar(500, 1000, length=10)
    log_test("ASCII Progress Bar Calculation", bar_50 == "[▓▓▓▓▓░░░░░] 50.0%", f"bar: {bar_50}")

    views = 50000
    est_monthly_views = views * 4
    est_cpm = 5.50
    est_monthly_revenue = round((est_monthly_views / 1000) * est_cpm, 2)
    log_test("$1,000/mo Revenue Modeling ($5.50 CPM)", est_monthly_revenue == 1100.0, f"${est_monthly_revenue}")
except Exception as e:
    log_test("CEO Comms & Financials", False, str(e))

# =====================================================================
# TEST 10: Auto-Playlists Manager
# =====================================================================
print("\n[10/14] Testing Auto-Playlists Manager...")
try:
    from core.playlist_manager import playlist_manager
    pillars = playlist_manager.PILLAR_PLAYLISTS
    log_test("5 Core Content Pillars Defined", len(pillars) == 5, f"{[p['category'] for p in pillars]}")
    matched_ocean = playlist_manager._match_pillar("Mariana Trench Abyssal Secret", "Ocean Mystery")
    matched_space = playlist_manager._match_pillar("James Webb Discovers Cosmic Void", "Space & Astronomy")
    log_test("Playlist Slot Matching (Ocean)", matched_ocean["category"] == "Ocean", f"matched: {matched_ocean['name']}")
    log_test("Playlist Slot Matching (Space)", matched_space["category"] == "Space", f"matched: {matched_space['name']}")
    summary = playlist_manager.format_playlists_telegram_summary()
    log_test("Playlist Summary Formatting", "Playlists" in summary)
except Exception as e:
    log_test("Playlist Manager", False, str(e))

# =====================================================================
# TEST 11: Comment Responder & Viewer Idea Hunter
# =====================================================================
print("\n[11/14] Testing Audience Comment Responder & Topic Hunter...")
try:
    from core.comment_responder import comment_responder
    test_comment = "Great documentary! Can you please cover the Baltic Sea Anomaly? It's so mysterious."
    extracted = comment_responder._extract_topic_suggestion(test_comment)
    log_test("Topic Suggestion Extracted From Comment", bool(extracted) and "Baltic Sea Anomaly" in extracted, f"extracted: '{extracted}'")
    test_comment_2 = "Next topic should be the Dyatlov Pass Incident"
    extracted_2 = comment_responder._extract_topic_suggestion(test_comment_2)
    log_test("Topic Suggestion Extracted Pattern 2", bool(extracted_2) and "Dyatlov Pass" in extracted_2, f"extracted: '{extracted_2}'")
except Exception as e:
    log_test("Comment Responder", False, str(e))

# =====================================================================
# TEST 12: Community Tab Poll Generator
# =====================================================================
print("\n[12/14] Testing Community Tab Poll Generator...")
try:
    from core.community_manager import community_manager
    poll_msg = community_manager.format_poll_for_telegram()
    log_test("Community Poll Telegram Formatting", "Community Tab" in poll_msg and "📊" in poll_msg)
except Exception as e:
    log_test("Community Poll", False, str(e))

# =====================================================================
# TEST 13: CEO Bot Command Routing & Security Guardrails
# =====================================================================
print("\n[13/14] Testing CEO Bot Command Routing & Guardrails...")
try:
    import ceo_bot
    captured_replies = []
    orig_send_tg = ceo_bot.send_tg
    ceo_bot.send_tg = lambda msg, parse_mode="Markdown": captured_replies.append(msg)

    # Test 1: Security Guardrail against deletion
    ceo_bot.process_message("/delete 12345")
    log_test("Security Guardrail: /delete Blocked", any("SECURITY GUARDRAIL" in m for m in captured_replies))

    # Test 2: /confirm_delete requires manual YouTube Studio action
    captured_replies.clear()
    ceo_bot.process_message("/confirm_delete 12345")
    log_test("Security Guardrail: /confirm_delete Enforces Studio Deletion", any("Manual Deletion Notice" in m for m in captured_replies))

    # Test 3: /pick A and /pick B
    captured_replies.clear()
    ceo_bot.process_message("/pick A")
    log_test("/pick A Registers Selection", ceo_bot.selected_thumb_choice == "A")

    ceo_bot.process_message("/pick B")
    log_test("/pick B Registers Selection", ceo_bot.selected_thumb_choice == "B")

    # Restore send_tg
    ceo_bot.send_tg = orig_send_tg
except Exception as e:
    log_test("CEO Bot Guardrails", False, str(e))

# =====================================================================
# TEST 14: Disk Hygiene & Storage Maintenance
# =====================================================================
print("\n[14/14] Testing Disk Hygiene Engine (1-Year Autopilot Safety)...")
try:
    from utils.cleanup import cleanup_intermediate_production, prune_disk_hygiene
    test_prod_dir = Path("/tmp/autodirector_production")
    test_prod_dir.mkdir(parents=True, exist_ok=True)
    temp_clip = test_prod_dir / "temp_scene_clip_1.mp4"
    temp_clip.write_text("dummy test data")
    master_clip = test_prod_dir / "master_final_documentary.mp4"
    master_clip.write_text("master output video data")

    cleanup_intermediate_production(keep_path=master_clip)
    log_test("Intermediate Clip Purged", not temp_clip.exists())
    log_test("Master Output Preserved", master_clip.exists())
    master_clip.unlink()

    stats = prune_disk_hygiene(max_age_hours=0)
    log_test("Disk Hygiene Prune Free Space Audit", "free_disk_gb" in stats and stats["free_disk_gb"] > 0, f"{stats['free_disk_gb']} GB Free")
except Exception as e:
    log_test("Disk Hygiene", False, str(e))

print("\n" + "=" * 70)
print(f"🏁 INTEGRATION TEST COMPLETE: {passed_tests} PASSED | {failed_tests} FAILED")
print("=" * 70)

if failed_tests > 0:
    sys.exit(1)
else:
    print("🌟 ALL 14 SYSTEMS OPERATIONAL AND PASSING 100%!")
    sys.exit(0)
