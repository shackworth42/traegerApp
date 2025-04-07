from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
import time
import threading
import random
import math

# === CONFIGURATION ===
SIMULATE = True  # Force simulate mode for standalone app
GRILL_TARGET_TEMP = 250
AMBIENT_TEMP = 70.0
SIM_DURATION = 60 * 60 * 3
FAN_OSCILLATION_PERIOD = 300
FAN_OSCILLATION_AMPLITUDE = 5

# === SHARED STATE ===
latest = {
    "timestamp": 0,
    "grill_temp": 0,
    "probe_temp": 0,
    "grill_setpoint": 0,
    "probe_setpoint": 0,
    "cook_timer_start": 0,
    "cook_timer_end": 0,
    "cook_timer_remaining": 0,
    "ambient_temp": None,
    "connected": False,
    "last_connected": None,
    "ever_connected": False,
    "is_idle": False,
}

data_points = []
sessions = []

# === FASTAPI SETUP ===
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# === SIMULATION MODE ===
def simulate_data():
    print("🔥 Simulated mode enabled (Grill warm-up in 10 minutes)")
    start = time.time()
    grill_temp = AMBIENT_TEMP
    probe_temp = AMBIENT_TEMP
    elapsed = 0

    grill_warmup_duration = 10 * 60
    probe_time_constant = 150
    probe_target_temp = 145

    while elapsed < SIM_DURATION:
        elapsed = time.time() - start

        if elapsed <= grill_warmup_duration:
            grill_temp = AMBIENT_TEMP + (GRILL_TARGET_TEMP - AMBIENT_TEMP) * (elapsed / grill_warmup_duration)
        else:
            grill_temp = GRILL_TARGET_TEMP

        fan_wave = FAN_OSCILLATION_AMPLITUDE * math.sin(
            2 * math.pi * (elapsed % FAN_OSCILLATION_PERIOD) / FAN_OSCILLATION_PERIOD
        )
        grill_temp += fan_wave + random.uniform(-1.0, 1.0)

        probe_temp += (grill_temp - probe_temp) * (1 - math.exp(-1 / probe_time_constant))
        probe_temp += random.uniform(-0.2, 0.2)

        update_latest(
            grill=grill_temp,
            probe=probe_temp,
            gset=GRILL_TARGET_TEMP,
            pset=probe_target_temp,
            ambient=AMBIENT_TEMP,
            connected=True
        )

        time.sleep(2)

# === STATE TRACKING ===
def update_latest(grill, probe, ambient=None, gset=None, pset=None, connected=True, last_conn=None,
                  cook_start=None, cook_end=None):
    now = time.time()
    latest["timestamp"] = now
    latest["grill_temp"] = round(grill, 1)
    latest["probe_temp"] = round(probe, 1)
    latest["grill_setpoint"] = gset
    latest["probe_setpoint"] = pset
    latest["ambient_temp"] = ambient
    latest["connected"] = connected
    latest["cook_timer_start"] = cook_start
    latest["cook_timer_end"] = cook_end

    if last_conn:
        if not latest["ever_connected"] or last_conn != latest["last_connected"]:
            latest["ever_connected"] = True
            latest["last_connected"] = last_conn
            sessions.append({"start": now, "end": None, "duration": None})
            print(f"🔌 Grill connected at {time.ctime(now)}")

    data_points.append({
        "time": now,
        "grill_temp": grill,
        "probe_temp": probe,
        "grill_setpoint": gset,
        "probe_setpoint": pset,
        "ambient_temp": ambient,
        "connected": connected,
        "last_connected": last_conn,
    })

    if len(data_points) > 10000:
        data_points.pop(0)

# === API ROUTES ===
@app.get("/api/stats")
def get_stats():
    return {
        "timestamp": latest["timestamp"],
        "grill_temp": latest["grill_temp"],
        "probe_temp": latest["probe_temp"],
        "grill_set": latest["grill_setpoint"],
        "probe_set": latest["probe_setpoint"],
        "ambient_temp": latest["ambient_temp"],
        "connected": latest["connected"],
        "is_simulated": SIMULATE,
        "is_idle": latest["is_idle"],
        "session_start_time": sessions[-1]["start"] if sessions else None,
        "last_connected": latest["last_connected"],
        "cook_timer_remaining": latest["cook_timer_remaining"],
    }

@app.get("/api/history")
def get_history():
    return data_points

@app.get("/api/sessions")
def get_sessions():
    return sessions

# === STARTUP ===
threading.Thread(target=simulate_data, daemon=True).start()