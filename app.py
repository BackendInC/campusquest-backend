from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session, exc
from starlette.status import HTTP_200_OK
import db
import db.models as models
import db.schemas as schemas
from datetime import datetime, timezone

# Initialize the database
db.Base.metadata.create_all(bind=db.engine)

# Dependency to get a session per request
def get_db():
    session: Session = db.SessionLocal()
    try:
        yield session
    finally:
        session.close()

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Hello World"}

@app.get ("/users/{user_id}", response_model=schemas.UserResponse)
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
        raise HTTPException(status_code=400, detail="Username or email already exists")


@app.get("/achievements", response_model=list[schemas.AchievementResponse])
def read_achievements(db: Session = Depends(get_db)):
    # Get all achievements from the database
    achievements = db.query(models.Achievements).all()
    return achievements


@app.post("/achievements", response_model=schemas.AchievementResponse)
def create_achievement(achievement: schemas.AchievementBase, db: Session = Depends(get_db)):
    # Create a new Achievement instance
    new_achievement = models.Achievements(
        description=achievement.description,
        award_tokens=achievement.award_tokens
    )

    # Add and commit the achievement to the database
    db.add(new_achievement)
    db.commit()
    db.refresh(new_achievement)  # Refresh to get the ID after insert

    return new_achievement


@app.get("/{user_id}/achievements", response_model=list[schemas.UserAchievementResponse])
def read_user_achievements(user_id: int, db: Session = Depends(get_db)):
    # Get all achievements for a user
    user_achievements = db.query(models.UserAchievements).filter(models.UserAchievements.user_id == user_id).all()
    return user_achievements

@app.put("/achievements", status_code=HTTP_200_OK)
def create_user_achievement(achievement: schemas.UserAchievementBase, db: Session = Depends(get_db)):
    # Check if user exists
    user = db.query(models.User).filter(models.User.id == achievement.user_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    # Check if the user already has the achievement
    user_achievement = db.query(models.UserAchievements).filter(
        models.UserAchievements.user_id == achievement.user_id,
        models.UserAchievements.achievement_id == achievement.achievement_id
    ).first()

    if user_achievement is not None:
        raise HTTPException(status_code=400, detail="User already has this achievement")

    # Create a new UserAchievements instance
    new_user_achievement = models.UserAchievements(
        user_id=achievement.user_id,
        achievement_id=achievement.achievement_id,
        date_achieved=datetime.now(timezone.utc)
    )

    # Add and commit the user achievement to the database
    db.add(new_user_achievement)
    db.commit()
    db.refresh(new_user_achievement)

    return {"message": "Achievement added successfully"}
