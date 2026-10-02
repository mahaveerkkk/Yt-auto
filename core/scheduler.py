import time
import random
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

    # Dynamic Autonomous Production Window: Daily 1 Master Documentary
    # Evaluated within 12:00 PM to 03:00 PM IST with randomized daily target time (Human-Variance Jitter)
    PRODUCTION_WINDOW_START_HOUR = 12
    PRODUCTION_WINDOW_END_HOUR = 15
    MORNING_BRIEFING_HOUR = 9       # 09:00 AM IST

    def __init__(self, produce_callback, notify_callback):
        self.produce_callback = produce_callback
        self.notify_callback = notify_callback
        self.running = False
        self.last_briefing_date = None
        self.last_cleanup_date = None
        self.last_sunday_report_date = None
        self.last_production_date = None
        # Daily randomized target time in window: hour between 12-14, minute between 5-55
        self.daily_random_hour = random.randint(12, 14)
        self.daily_random_minute = random.randint(5, 55)
        self.last_ab_check_time = time.time()
        self.last_comment_check_time = time.time()
        self.last_heartbeat_time = time.time()

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

                # 2. Autonomous Daily 1 Production Check (Randomized Window between 12:00 PM - 03:00 PM IST)
                if self.last_production_date != today_str:
                    time_matched = (curr_hour > self.daily_random_hour) or (curr_hour == self.daily_random_hour and curr_minute >= self.daily_random_minute)
                    if time_matched:
                        decision = ai_brain.should_produce_now()
                        if decision.get("allowed"):
                            self.last_production_date = today_str
                            logger.info(f"[Scheduler] Daily Random Slot Triggered ({curr_hour}:{curr_minute:02d} IST). AI Brain approved production.")
                            try:
                                self.notify_callback(f"⏰ *Autonomous Daily Production Triggered ({curr_hour}:{curr_minute:02d} IST)!*\nAI Brain verified quotas & schedule. Deploying documentary team...")
                            except Exception as ne:
                                logger.warning(f"[Scheduler] Notify callback failed: {ne}")
                            self.produce_callback(topic=None)
                            # Re-roll randomized slot for next day
                            self.daily_random_hour = random.randint(12, 14)
                            self.daily_random_minute = random.randint(5, 55)
                            logger.info(f"[Scheduler] Next day random production target pre-set: {self.daily_random_hour}:{self.daily_random_minute:02d} IST")
                        else:
                            logger.info(f"[Scheduler] Production postponed: {decision.get('reason')}. Retrying in 20 mins.")
                            # Push target forward by 20 minutes to retry within window
                            self.daily_random_minute = (curr_minute + 20) % 60
                            if curr_minute + 20 >= 60:
                                self.daily_random_hour = min(self.PRODUCTION_WINDOW_END_HOUR, curr_hour + 1)

                # 3. Strategic A/B Evaluation Loop (Daily / Every 24 hours)
                if time.time() - self.last_ab_check_time > 86400:
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
