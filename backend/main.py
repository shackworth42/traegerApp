from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pytraeger.manager import Manager as TraegerManager
from pytraeger.grill import grill as grillclass
from dotenv import load_dotenv
import os
import time
import threading
import random
import math

# Load environment variables
load_dotenv()

# === CONFIGURATION ===
SIMULATE = os.getenv("SIMULATE", "false").lower() == "true"
GRILL_TARGET_TEMP = 250                # 🎯 Target temp the grill is trying to hit
AMBIENT_TEMP = 70.0                    # 🌤️ Outside/room temp for sim
SIM_DURATION = 60 * 60 * 3             # 🕒 How long a fake cook should run (3 hours)
FAN_OSCILLATION_PERIOD = 300           # 🔄 Fan surges every 5 minutes
FAN_OSCILLATION_AMPLITUDE = 5          # 🌊 +/- degrees added by fan cycles

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

data_points = []  # 📈 For historical graphing
sessions = []     # 📚 Session tracking (start/end/duration)

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

    grill_warmup_duration = 10 * 60        # ⏱️ Grill heats over 10 minutes
    probe_time_constant = 150              # 🧠 Meat heats slower (lag factor)
    probe_target_temp = 145                # 🎯 Simulated meat target temp

    while elapsed < SIM_DURATION:
        elapsed = time.time() - start

        # Grill heating curve
        if elapsed <= grill_warmup_duration:
            grill_temp = AMBIENT_TEMP + (GRILL_TARGET_TEMP - AMBIENT_TEMP) * (elapsed / grill_warmup_duration)
        else:
            grill_temp = GRILL_TARGET_TEMP

        # Simulate oscillation (like fan surging)
        fan_wave = FAN_OSCILLATION_AMPLITUDE * math.sin(
            2 * math.pi * (elapsed % FAN_OSCILLATION_PERIOD) / FAN_OSCILLATION_PERIOD
        )
        grill_temp += fan_wave + random.uniform(-1.0, 1.0)

        # Simulate internal probe temp rising
        probe_temp += (grill_temp - probe_temp) * (1 - math.exp(-1 / probe_time_constant))
        probe_temp += random.uniform(-0.2, 0.2)

        # Push all values including setpoints into shared state
        update_latest(
            grill=grill_temp,
            probe=probe_temp,
            gset=GRILL_TARGET_TEMP,
            pset=probe_target_temp,
            ambient=AMBIENT_TEMP,
            connected=True
        )

        # Debug output
        # print(f"[Sim] 🔥 Grill: {grill_temp:.1f}°F | 🌡️ Probe: {probe_temp:.1f}°F | 🎯 Target: {probe_target_temp}°F")

        time.sleep(2)


# === LIVE MODE (pyTraeger) ===
def save_from_grill(event_grill: grillclass):
    status = event_grill.data.get("status", {})
    details = event_grill.data.get("details", {})
    acc = status.get("acc", [{}])[0]

    values = {
        "connected": status.get("connected"),  # 📡 Whether the grill is currently connected (True/False)
        "grill_temp": status.get("grill"),     # 🌡️ Current grill temperature in °F
        "probe_temp": status.get("probe"),     # 🌡️ Current internal meat probe temperature in °F
        "grill_setpoint": status.get("grillSetPoint") or status.get("grill_set") or status.get("set"),  
        "probe_setpoint": status.get("probeSetPoint") or status.get("probe_set") or acc.get("probe", {}).get("set_temp"),
        "cook_timer_start": status.get("cook_timer_start"),  # 🕒 Timestamp when cook timer started
        "cook_timer_end": status.get("cook_timer_end"),      # 🕒 Timestamp when cook timer ends
        "cook_timer_remaining": status.get("cook_timer_remaining"),  # ⏱️ Remaining time on cook timer
        "time": status.get("time"),            # 🕐 Current time from grill
        "last_connected": details.get("lastConnectedOn"),  # 📅 Timestamp of last successful connection
    }

    update_latest(
        grill=values["grill_temp"],
        probe=values["probe_temp"],
        ambient=None,
        gset=values["grill_setpoint"],
        pset=values["probe_setpoint"],
        connected=values["connected"],
        last_conn=values["last_connected"],
        cook_start=values["cook_timer_start"],
        cook_end=values["cook_timer_end"],
    )

def start_traeger():
    print("🔥 Live mode enabled. Starting pyTraeger...")
    manager = TraegerManager(interval_idle=10, interval_busy=5)
    for grill in manager.api.grills:
        grill.register_listener(save_from_grill)
    print("✅ PyTraeger listener registered.")
    while True:
        time.sleep(1)

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

# === IDLE WATCHER ===
def idle_watcher():
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
                    print("💤 Grill is idle.")
                latest["is_idle"] = True

                if sessions and sessions[-1]["end"] is None:
                    sessions[-1]["end"] = time.time()
                    sessions[-1]["duration"] = sessions[-1]["end"] - sessions[-1]["start"]
        else:
            if latest["is_idle"]:
                print("⚡ Exiting idle mode.")
            idle_start = None
            latest["is_idle"] = False

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
        "cook_timer_remaining": latest["cook_timer_remaining"],  # also useful!
    }


@app.get("/api/history")
def get_history():
    return data_points

@app.get("/api/sessions")
def get_sessions():
    return sessions

# === STARTUP ===
if SIMULATE:
    threading.Thread(target=simulate_data, daemon=True).start()
else:
    threading.Thread(target=start_traeger, daemon=True).start()