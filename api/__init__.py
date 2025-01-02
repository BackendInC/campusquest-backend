from fastapi import FastAPI
from api.achievements import router as achievementsRouter
from api.users import router as usersRouter
from api.quests import router as questsRouter
from api.email_verification import router as emailRouter
from api.friends import router as friendsRouter
from api.posts import router as postsRouter

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


def start_app():
    @app.get("/users/{user_id}", response_model=schemas.userresponse)
    def read_user(user_id: int, db: session = Depends(get_db)):
        # get the user by id
        user = db.query(models.user).filter(models.user.id == user_id).first()
        return user
