from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import select
from contextlib import contextmanager
from dotenv import load_dotenv
import os
import time
import threading
import random
import math
from datetime import datetime

from backend.state import latest, data_points, sessions
from backend.models import Session as SessionModel, CookLog
from backend.db import init_db, get_db
from pathlib import Path

# === LOAD ENVIRONMENT VARIABLES ===
load_dotenv(dotenv_path=Path(__file__).parent / ".env")
SIMULATE = os.getenv("SIMULATE", "false").lower() == "true"

# === INIT DB ===
init_db()

# === CONFIGURATION ===
GRILL_TARGET_TEMP = 250
AMBIENT_TEMP = 70.0
SIM_DURATION = 60 * 60 * 3
FAN_OSCILLATION_PERIOD = 300
FAN_OSCILLATION_AMPLITUDE = 5
WAKE_THRESHOLD_SECONDS = 1

# === APP SETUP ===
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@contextmanager
def get_sync_session():
    db_gen = get_db()
    db = next(db_gen)
    try:
        yield db
    finally:
        db_gen.close()

# === IDLE LOOP ===
def idle_loop():
    while True:
        time.sleep(2)
        now = time.time()
        last_conn = latest.get("last_connected")

        if last_conn and abs(now - last_conn) <= WAKE_THRESHOLD_SECONDS:
            latest["is_idle"] = False
        else:
            if not latest["is_idle"]:
                print("💤 Entering idle state.")
                latest["is_idle"] = True

                with get_sync_session() as db:
                    session_obj = db.exec(select(SessionModel).order_by(SessionModel.id.desc())).first()
                    if session_obj and session_obj.end is None:
                        session_obj.end = datetime.fromtimestamp(now)
                        session_obj.duration = now - session_obj.start.timestamp()
                        db.add(session_obj)
                        db.commit()

# === SIMULATED DATA GENERATOR ===
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

if not SIMULATE:
    from pytraeger.manager import Manager
    manager = Manager()
    manager.api.do_cognito()
    manager.api.init()
    manager.api.get_grills()
    grill = manager.api.grills[0]
    mqtt = manager.api.mqtt_client

    if mqtt:
        latest["mqtt_initialized"] = True
        mqtt.set_datahook(lambda grill_id, data: grill.update(data))
        mqtt.start()
    else:
        latest["mqtt_initialized"] = False



# === SHARED STATE LOGGER ===
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

    with get_sync_session() as session:
        session.add(CookLog(
            timestamp=now,
            grill_temp=grill,
            probe_temp=probe,
            grill_setpoint=gset,
            probe_setpoint=pset,
            ambient_temp=ambient,
            connected=connected
        ))
        session.commit()

# === ROUTES ===
@app.get("/api/stats")
def get_stats():
    print(f"📊 /stats → SIMULATE={SIMULATE}, IDLE={latest['is_idle']}, MQTT={latest.get('mqtt_initialized')}")
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
        "is_mqtt_live": latest.get("mqtt_initialized", False),
    }
    print(f"[] is_simulated = {SIMULATE}")


@app.get("/api/mode")
def get_mode():
    return {"simulate": SIMULATE}

@app.get("/api/history")
def get_history():
    return data_points

@app.get("/api/sessions")
def get_sessions():
    return sessions

@app.get("/api/test-db")
def test_db():
    with get_sync_session() as session:
        rows = session.exec(select(CookLog)).all()
        return {"status": "success", "rows": len(rows)}

# === THREADS ===
if SIMULATE:
    threading.Thread(target=simulate_data, daemon=True).start()
else:
    print("🛑 Simulated data disabled — waiting for real grill input...")

threading.Thread(target=idle_loop, daemon=True).start()