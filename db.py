from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Database configuration
DATABASE_URL = "postgresql://root:1234@db:5432/backendinc"

# Set up the database engine
engine = create_engine(DATABASE_URL)

# Create all tables (if they don’t exist) based on the models
from models import Base  # Assuming your model is saved in models.py

Base.metadata.create_all(engine)

# Session setup
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Usage example of a session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
