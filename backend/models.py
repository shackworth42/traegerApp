from sqlmodel import SQLModel, Field
from typing import Optional
import time

class Session(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    start: float
    end: Optional[float] = None
    duration: Optional[float] = None

class CookLog(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    timestamp: float = Field(default_factory=lambda: time.time())
    grill_temp: float
    probe_temp: float
    grill_setpoint: Optional[float] = None
    probe_setpoint: Optional[float] = None
    ambient_temp: Optional[float] = None
    connected: Optional[bool] = None
