from fastapi import FastAPI
import models
import db

# Initialize the database
db.Base.metadata.create_all(bind=db.engine)

# Dependency to get a session per request
def get_db():
    session = db.SessionLocal()
    try:
        yield session
    finally:
        session.close()

app = FastAPI()

@app.get("/")
def read_root():
    return {"message" : "Hello World"}

