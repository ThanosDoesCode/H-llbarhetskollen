from __future__ import annotations
import datetime as dt
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict

class UserCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)

class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str

class ActivityCreate(BaseModel):
    user_id: int
    category: str = Field(min_length=1, max_length=40)
    key: str = Field(min_length=1, max_length=60)
    amount: float = Field(gt=0)
    date: dt.date

class ActivityOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    user_id: int
    category: str
    key: str
    amount: float
    date: dt.date
    co2e: Optional[float] = None

class EmissionFactorOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    category: str
    key: str
    unit: str
    co2e_per_unit: float
    source: Optional[str] = None
    scope: Optional[str] = None

class WeeklyReportOut(BaseModel):
    user_id: int
    week_start: dt.date
    week_end: dt.date
    total_co2e: float