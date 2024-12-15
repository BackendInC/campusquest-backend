from fastapi import FastAPI
from api.achievements import router as achievementsRouter
from api.users import router as usersRouter

# from api.quests import router as questsRouter

app = FastAPI()
app.include_router(achievementsRouter)
app.include_router(usersRouter)
# app.include_router(questsRouter)
