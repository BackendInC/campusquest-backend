from fastapi import FastAPI
from api.achievements import router as achievementsRouter
from api.users import router as usersRouter
from api.quests import router as questsRouter
from api.email_verification import router as emailRouter

app = FastAPI()
app.include_router(achievementsRouter)
app.include_router(usersRouter)
app.include_router(questsRouter)
app.include_router(emailRouter)


def start_app():
    @app.get("/users/{user_id}", response_model=schemas.userresponse)
    def read_user(user_id: int, db: session = Depends(get_db)):
        # get the user by id
        user = db.query(models.user).filter(models.user.id == user_id).first()
        return user
