from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import session, exc
from db import get_db
import db.models as models
import db.schemas as schemas

# routers for each api prefix
from api.achievements import router as achievementsrouter
from api.quests import router as questsrouter

app = FastAPI()
app.include_router(achievementsrouter)
app.include_router(questsrouter)



def start_app():
    @app.get("/")
    def read_root():
        return {"message": "hello world"}

    @app.get("/users/{user_id}", response_model=schemas.userresponse)
    def read_user(user_id: int, db: session = Depends(get_db)):
        # get the user by id
        user = db.query(models.user).filter(models.user.id == user_id).first()
        return user

    @app.post("/users", response_model=schemas.userresponse)
    def create_user(user: schemas.usercreate, db: session = Depends(get_db)):
        # create a new user instance
        new_user = models.user(
            username=user.username,
            email=user.email,
            password=user.password,
            num_quests_completed=0,
            tokens=0,
        )

        try:
            # add and commit the user to the database
            db.add(new_user)
            db.commit()
            db.refresh(new_user)

            return new_user
        except exc.sa_exc.integrityerror:
            raise HTTPException(
                status_code=400, detail="username or email already exists"
            )
