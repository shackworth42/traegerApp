# backend/state.py

latest = {
    "mqtt_initialized": False,
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
