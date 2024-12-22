from fastapi import Depends, HTTPException, APIRouter
from db import schemas, get_db
from sqlalchemy.orm import Session
from datetime import datetime, timezone
import db.models as models

import api.auth as auth

router = APIRouter(tags=["achievements"])


@router.get("/achievements", response_model=list[schemas.AchievementResponse])
def read_achievements(db: Session = Depends(get_db)):
    # Get all achievements from the database
    achievements = db.query(models.Achievements).all()
    return achievements


@router.post(
    "/achievements",
    response_model=schemas.AchievementResponse,
)
def create_achievement(
    achievement: schemas.AchievementBase,
    db: Session = Depends(get_db),
    user_id: int = Depends(auth.verify_admin),
):
    # Create a new Achievement instance
    new_achievement = models.Achievements(
        description=achievement.description, award_tokens=achievement.award_tokens
    )

    # Add and commit the achievement to the database
    db.add(new_achievement)
    db.commit()
    db.refresh(new_achievement)  # Refresh to get the ID after insert

    return new_achievement


@router.get(
    "/{user_id}/achievements", response_model=list[schemas.UserAchievementResponse]
)
def read_user_achievements(user_id: int, db: Session = Depends(get_db)):
    # Get all achievements for a user
    user_achievements = (
        db.query(models.UserAchievements)
        .filter(models.UserAchievements.user_id == user_id)
        .all()
    )
    return user_achievements


@router.put("/achievements", status_code=200)
def create_user_achievement(
    achievement: schemas.UserAchievementBase, db: Session = Depends(get_db)
):
    # Check if user exists
    user = db.query(models.User).filter(models.User.id == achievement.user_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    # Check if the user already has the achievement
    user_achievement = (
        db.query(models.UserAchievements)
        .filter(
            models.UserAchievements.user_id == achievement.user_id,
            models.UserAchievements.achievement_id == achievement.achievement_id,
        )
        .first()
    )

    if user_achievement is not None:
        raise HTTPException(status_code=400, detail="User already has this achievement")

    # Create a new UserAchievements instance
    new_user_achievement = models.UserAchievements(
        user_id=achievement.user_id,
        achievement_id=achievement.achievement_id,
        date_achieved=datetime.now(timezone.utc),
    )

    # Add and commit the user achievement to the database
    db.add(new_user_achievement)
    db.commit()
    db.refresh(new_user_achievement)

    return {"message": "Achievement added successfully"}
