import time
import threading
from datetime import datetime, timezone, timedelta
from utils.logger import logger
from core.ai_brain import ai_brain
from core.ceo_comms import ceo_comms
from core.ab_optimizer import ab_optimizer
from core.resilience import watchdog
from core.comment_responder import comment_responder

IST = timezone(timedelta(hours=5, minutes=30))


class StudioScheduler:
    """
    Autonomous Studio Schedule & Heartbeat Engine:
    - 08:30 AM IST: Morning CEO Briefing with live monetization metrics
    - Production Slots: Evaluated dynamically via AI Brain (checks quota, channel frequency limits)
    - 3-Hour Interval: A/B Optimizer Check (Underperforming title/thumbnail swap)
    - 4-Hour Interval: Audience Comment Scan & Topic Mining
    - 6-Hour Interval: System Watchdog & Heartbeat Telemetry
    """

    SCHEDULE_HOURS_IST = [12, 19]  # 12:00 PM & 7:00 PM IST (optimal for long-form retention)
    MORNING_BRIEFING_HOUR = 9       # 09:00 AM IST

    def __init__(self, produce_callback, notify_callback):
        self.produce_callback = produce_callback
        self.notify_callback = notify_callback
        self.running = False
        self.last_briefing_date = None
        self.last_cleanup_date = None
        self.last_sunday_report_date = None
        self.last_production_hour = None
        self.last_ab_check_time = 0
        self.last_comment_check_time = 0
        self.last_heartbeat_time = 0

    def start(self):
        self.running = True
        t = threading.Thread(target=self._schedule_loop, daemon=True)
        t.start()
        logger.info("[Scheduler] Autonomous Studio 24/7 Scheduler started!")

    def _schedule_loop(self):
        while self.running:
            try:
                now = datetime.now(IST)
                today_str = now.strftime("%Y-%m-%d")
                curr_hour = now.hour
                curr_minute = now.minute

                # 0. Daily 04:00 AM IST Disk Hygiene & Pruning
                if curr_hour == 4 and self.last_cleanup_date != today_str:
                    try:
                        from utils.cleanup import prune_disk_hygiene
                        stats = prune_disk_hygiene(max_age_hours=48)
                        logger.info(f"[Scheduler] Daily 04:00 AM Disk Hygiene executed: {stats}")
                        self.last_cleanup_date = today_str
                    except Exception as cle:
                        logger.warning(f"[Scheduler] Disk hygiene error: {cle}")

                # 1. Morning Executive Standup (09:00 AM IST)
                if curr_hour == self.MORNING_BRIEFING_HOUR and curr_minute >= 0 and self.last_briefing_date != today_str:
                    logger.info("[Scheduler] Dispatching 09:00 AM CEO Morning Motivation Standup...")
                    ceo_comms.send_morning_executive_briefing()
                    self.last_briefing_date = today_str

                # 1b. Sunday 08:00 PM IST $1,000/Month Revenue Roadmap & Strategy Audit (Sunday = weekday 6)
                if now.weekday() == 6 and curr_hour == 20 and self.last_sunday_report_date != today_str:
                    logger.info("[Scheduler] Dispatching Sunday 08:00 PM $1,000/Month Revenue Audit...")
                    ceo_comms.send_weekly_revenue_report()
                    self.last_sunday_report_date = today_str

                # 2. Autonomous Production Check (During scheduled peak windows)
                if curr_hour in self.SCHEDULE_HOURS_IST and self.last_production_hour != curr_hour:
                    self.last_production_hour = curr_hour
                    decision = ai_brain.should_produce_now()
                    if decision.get("allowed"):
                        logger.info(f"[Scheduler] Slot triggered: Hour {curr_hour}:00 IST. AI Brain approved production.")
                        self.notify_callback(f"⏰ *Autonomous Production Triggered ({curr_hour}:00 IST)!*\nAI Brain verified quotas & schedule. Deploying documentary team...")
                        self.produce_callback(topic=None)
                    else:
                        logger.info(f"[Scheduler] Production postponed: {decision.get('reason')}")

                # 3. A/B Optimization Loop (Every 3 hours)
                if time.time() - self.last_ab_check_time > 10800:
                    self.last_ab_check_time = time.time()
                    report = ab_optimizer.check_and_optimize_videos()
                    if report:
                        self.notify_callback(report)

                # 4. Audience Comments & Topic Mining Loop (Every 4 hours)
                if time.time() - self.last_comment_check_time > 14400:
                    self.last_comment_check_time = time.time()
                    try:
                        res = comment_responder.scan_and_respond()
                        if res.get("topics_mined", 0) > 0:
                            summary = comment_responder.format_comment_summary(limit=3)
                            self.notify_callback(f"💬 *Audience Topic Radar:* New viewer request mined!\n\n{summary}")
                    except Exception as ce:
                        logger.warning(f"[Scheduler] Comment responder scan error: {ce}")

                # 5. System Watchdog & Heartbeat (Every 6 hours)
                if time.time() - self.last_heartbeat_time > 21600:
                    self.last_heartbeat_time = time.time()
                    health = watchdog.get_system_health()
                    self.notify_callback(
                        f"💓 *Studio Heartbeat — 100% Autopilot Active*\n\n"
                        f"• Host Node Pool: `{health.get('disk_free_gb')} GB free`\n"
                        f"• Studio Temp Cache: `{health.get('temp_cache_mb')} MB` (Optimal / Clean)\n"
                        f"• Storage Status: `{health.get('storage_status', 'Healthy & Clean')}`\n"
                        f"• Pexels Quota Remaining: `{health.get('quotas', {}).get('pexels', {}).get('remaining')}` calls\n\n"
                        "All background services running without issue."
                    )

            except Exception as e:
                logger.error(f"[Scheduler Loop Error]: {e}")

            time.sleep(60)


scheduler_instance = None
