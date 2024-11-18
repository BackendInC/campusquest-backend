from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session, exc
import db
import db.models as models
import db.schemas as schemas


# Dependency to get a session per request
def get_db():
    session: Session = db.SessionLocal()
    try:
        yield session
    finally:
        session.close()


app = FastAPI()


def start_app():
    @app.get("/")
    def read_root():
        return {"message": "Hello World"}

    @app.get("/users/{user_id}", response_model=schemas.UserResponse)
    def read_user(user_id: int, db: Session = Depends(get_db)):
        # Get the user by ID
        user = db.query(models.User).filter(models.User.id == user_id).first()
        return user

    @app.post("/users", response_model=schemas.UserResponse)
    def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
        # Create a new User instance
        new_user = models.User(
            username=user.username,
            email=user.email,
            password=user.password,
            num_quests_completed=0,
            tokens=0,
        )

        try:
            # Add and commit the user to the database
            db.add(new_user)
            db.commit()
            db.refresh(new_user)

            return new_user
        except exc.sa_exc.IntegrityError:
            raise HTTPException(
                status_code=400, detail="Username or email already exists"
            )
