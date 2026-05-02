from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from data.db.models import Base
import os

def get_session():
    db_path = os.getenv("DB_PATH", "data/db/bourgelat.db")
    engine = create_engine(f"sqlite:///{db_path}")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return Session()