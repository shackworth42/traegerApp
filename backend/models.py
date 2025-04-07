# backend/models.py

from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime

class Session(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    start: datetime
    end: Optional[datetime] = None
    duration: Optional[float] = None  # seconds
    notes: Optional[str] = None
    grill_setpoint: Optional[float] = None
    probe_setpoint: Optional[float] = None
    ambient_temp: Optional[float] = None
