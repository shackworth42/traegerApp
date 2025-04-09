# backend/idle_watcher.py

import time
from .state import latest

def idle_loop():
    print("Watching for idle state...")
    idle_start = None

    while True:
        time.sleep(2)
        grill = latest.get("grill_temp")
        probe = latest.get("probe_temp")

        if grill == 95 and probe == 69:
            if idle_start is None:
                idle_start = time.time()
            elif time.time() - idle_start > 15:
                if not latest["is_idle"]:
                    print("Grill is idle.")
                latest["is_idle"] = True
        else:
            if latest["is_idle"]:
                print("Exiting idle mode.")
            idle_start = None
            latest["is_idle"] = False
