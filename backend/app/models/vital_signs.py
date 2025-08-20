from sqlalchemy import Column, String, Float, DateTime, ForeignKey, Enum, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

# VitalSign uses a separate base since it's in TimescaleDB
TimescaleBase = declarative_base()

class VitalType(enum.Enum):
    HEART_RATE = "heart_rate"
    BLOOD_PRESSURE_SYSTOLIC = "blood_pressure_systolic"
    BLOOD_PRESSURE_DIASTOLIC = "blood_pressure_diastolic"
    WEIGHT = "weight"
    HEIGHT = "height"
    BMI = "bmi"
    TEMPERATURE = "temperature"
    BLOOD_GLUCOSE = "blood_glucose"
    OXYGEN_SATURATION = "oxygen_saturation"
    RESPIRATORY_RATE = "respiratory_rate"
    STEPS = "steps"
    CALORIES = "calories"
    SLEEP_HOURS = "sleep_hours"
    WATER_INTAKE = "water_intake"
    CUSTOM = "custom"

class VitalSign(TimescaleBase):
    __tablename__ = "vital_signs"
    
    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, nullable=False, index=True)  # No ForeignKey - different database
    
    vital_type = Column(Enum(VitalType), nullable=False, index=True)
    value = Column(Float, nullable=False)
    unit = Column(String, nullable=False)
    
    custom_name = Column(String, nullable=True)
    notes = Column(Text, nullable=True)
    source = Column(String, nullable=True)
    
    recorded_at = Column(DateTime, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Note: relationship to User is not needed since VitalSign is in TimescaleDB
    # and User is in PostgreSQL - they are in different databases