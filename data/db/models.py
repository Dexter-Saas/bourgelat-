from sqlalchemy import Column, String, Float, DateTime, Text, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime
import os

Base = declarative_base()

class Animal(Base):
    __tablename__ = "animals"
    id = Column(String, primary_key=True)
    farmer_phone = Column(String, nullable=False)
    name = Column(String)
    breed = Column(String)
    age_months = Column(Float)
    weight_kg = Column(Float)
    registered_vet = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

class HealthRecord(Base):
    __tablename__ = "health_records"
    id = Column(String, primary_key=True)
    animal_id = Column(String, nullable=False)
    bcs_score = Column(Float)
    diagnosis = Column(Text)
    severity = Column(String)
    treatment = Column(Text)
    confidence = Column(Float)
    video_path = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

class FeedRecord(Base):
    __tablename__ = "feed_records"
    id = Column(String, primary_key=True)
    animal_id = Column(String, nullable=False)
    ration = Column(Text)
    cost_estimate = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)

def init_db():
    db_path = os.getenv("DB_PATH", "data/db/bourgelat.db")
    engine = create_engine(f"sqlite:///{db_path}")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return Session()