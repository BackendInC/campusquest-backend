from fastapi import FastAPI
from api.achievements import router as achievementsRouter
from api.users import router as usersRouter
from api.quests import router as questsRouter
from api.email_verification import router as emailRouter
from api.friends import router as friendsRouter
from api.posts import router as postsRouter
from api.feed import router as feedRouter
from api.admin import router as adminRouter
from api.milestones import (
    QUEST_MILESTONES,
    FRIEND_MILESTONES,
    LIKE_MILESTONES,
    VERIFICATION_MILESTONES,
)

from db import models, get_db

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(achievementsRouter)
app.include_router(usersRouter)
app.include_router(questsRouter)
app.include_router(emailRouter)
app.include_router(friendsRouter)
app.include_router(postsRouter)
app.include_router(feedRouter)
app.include_router(adminRouter)


@app.on_event("startup")
async def startup_event():
    db = next(get_db())
    try:
        models.Achievements.load_achievements(QUEST_MILESTONES, db)
        models.Achievements.load_achievements(FRIEND_MILESTONES, db)
        models.Achievements.load_achievements(LIKE_MILESTONES, db)
        models.Achievements.load_achievements(VERIFICATION_MILESTONES, db)
    except Exception:
        print("Error loading achievements!")
        print("Assuming they are already defined.")
