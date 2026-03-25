#!/usr/bin/env python3
"""
Real-time viewer for Robocross workout debug logs.
Shows the last 50 lines and updates as new logs are written.
"""
import time
from pathlib import Path

LOG_PATH = Path(__file__).parent / "logs/workouts.log"

def tail_log(num_lines=50):
    """Display the last N lines of the log file and follow new lines."""
    print(f"📋 Monitoring debug log: {LOG_PATH}")
    print("=" * 80)

    if not LOG_PATH.exists():
        print(f"⚠ Log file doesn't exist yet: {LOG_PATH}")
        print("   It will be created when the app starts.")
        return

    # Show last N lines
    with open(LOG_PATH, 'r') as f:
        lines = f.readlines()
        for line in lines[-num_lines:]:
            print(line, end='')

    print("\n" + "=" * 80)
    print("📡 Following new log entries (Ctrl+C to stop)...")
    print("=" * 80)

    # Follow new lines
    with open(LOG_PATH, 'r') as f:
        # Move to end
        f.seek(0, 2)

        try:
            while True:
                line = f.readline()
                if line:
                    print(line, end='')
                else:
                    time.sleep(0.1)
        except KeyboardInterrupt:
            print("\n\n👋 Stopped monitoring log")

if __name__ == "__main__":
    tail_log()
