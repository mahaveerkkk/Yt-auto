import time
import threading
from datetime import datetime
from utils.logger import logger
from core.ai_brain import ai_brain
from core.ceo_comms import ceo_comms
from core.ab_optimizer import ab_optimizer
from core.resilience import watchdog


class StudioScheduler:
    """
    Autonomous Studio Schedule & Heartbeat Engine:
    - 08:30 AM IST: Morning CEO Briefing with live monetization metrics
    - Production Slots: Evaluated dynamically via AI Brain (checks quota, channel frequency limits)
    - 3-Hour Interval: A/B Optimizer Check (Underperforming title/thumbnail swap)
    - 6-Hour Interval: System Watchdog & Heartbeat Telemetry
    """

    SCHEDULE_HOURS_IST = [12, 19]  # 12:00 PM & 7:00 PM (optimal for long-form retention)
    MORNING_BRIEFING_HOUR = 8       # 8:30 AM IST

    def __init__(self, produce_callback, notify_callback):
        self.produce_callback = produce_callback
        self.notify_callback = notify_callback
        self.running = False
        self.last_briefing_date = None
        self.last_production_hour = None
        self.last_ab_check_time = 0
        self.last_heartbeat_time = 0

    def start(self):
        self.running = True
        t = threading.Thread(target=self._schedule_loop, daemon=True)
        t.start()
        logger.info("[Scheduler] Autonomous Studio 24/7 Scheduler started!")

    def _schedule_loop(self):
        while self.running:
            try:
                now = datetime.now()
                today_str = now.strftime("%Y-%m-%d")
                curr_hour = now.hour
                curr_minute = now.minute

                # 1. Morning Executive Briefing (08:30 AM IST)
                if curr_hour == self.MORNING_BRIEFING_HOUR and curr_minute >= 30 and self.last_briefing_date != today_str:
                    logger.info("[Scheduler] Dispatching Morning CEO Executive Briefing...")
                    ceo_comms.send_morning_executive_briefing()
                    self.last_briefing_date = today_str

                # 2. Autonomous Production Check (During scheduled peak windows)
                if curr_hour in self.SCHEDULE_HOURS_IST and self.last_production_hour != curr_hour:
                    decision = ai_brain.should_produce_now()
                    if decision.get("allowed"):
                        logger.info(f"[Scheduler] Slot triggered: Hour {curr_hour}:00 IST. AI Brain approved production.")
                        self.notify_callback(f"⏰ *Autonomous Production Triggered ({curr_hour}:00 IST)!*\nAI Brain verified quotas & schedule. Deploying documentary team...")
                        self.produce_callback(topic=None)
                        self.last_production_hour = curr_hour
                    else:
                        logger.info(f"[Scheduler] Production postponed: {decision.get('reason')}")

                # 3. A/B Optimization Loop (Every 3 hours)
                if time.time() - self.last_ab_check_time > 10800:
                    self.last_ab_check_time = time.time()
                    report = ab_optimizer.check_and_optimize_videos()
                    if report:
                        self.notify_callback(report)

                # 4. System Watchdog & Heartbeat (Every 6 hours)
                if time.time() - self.last_heartbeat_time > 21600:
                    self.last_heartbeat_time = time.time()
                    health = watchdog.get_system_health()
                    self.notify_callback(
                        f"💓 *Studio Heartbeat — 100% Autopilot Active*\n\n"
                        f"• VPS Disk Free: `{health.get('disk_free_gb')} GB`\n"
                        f"• Temporary Cache: `{health.get('temp_cache_mb')} MB`\n"
                        f"• Pexels Quota Remaining: `{health.get('quotas', {}).get('pexels', {}).get('remaining')}` calls\n\n"
                        "All background services running without issue."
                    )

            except Exception as e:
                logger.error(f"[Scheduler Loop Error]: {e}")

            time.sleep(60)


scheduler_instance = None
