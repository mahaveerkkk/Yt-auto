#!/usr/bin/env python3
import sys
import time
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from utils.logger import logger
import ceo_bot

print("🎬 Triggering Full Test Production Run...")
ceo_bot.cmd_produce(topic="The 1997 Pacific Bloop Anomaly")

time.sleep(2)
while ceo_bot.production_active:
    print("⏳ Production in progress... please wait...")
    time.sleep(5)

print("🎉 Test Production Run Completed!")
