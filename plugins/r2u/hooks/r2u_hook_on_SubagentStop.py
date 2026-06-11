#!/usr/bin/env python3
import os
import sys
from datetime import datetime

LOG_FILE = os.path.join(os.getcwd(), ".codex\\logs\\hook.log")
os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)

if __name__ == "__main__":
    with open(LOG_FILE, "a", encoding="utf-8") as log_file:
        #log_file.write(f"{sys.stdin.read()}\n")
        log_file.write(f"{datetime.now().strftime('%Y-%m-%d-%H-%M-%S-%f')}\n")