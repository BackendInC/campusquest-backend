from fastapi import FastAPI
import db
from api.users import router as users_router
from api.achievements import router as achievements_router
from api.posts import router as posts_router

app = FastAPI()

# Root endpoint
@app.get("/")
def read_root():
    return {"message": "Welcome to CampusQuest API!"}

# Include your routers here
app.include_router(users_router)
app.include_router(achievements_router)
app.include_router(posts_router)

db.Base.metadata.create_all(bind=db.engine)