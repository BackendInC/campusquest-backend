from fastapi import Depends, HTTPException, APIRouter
from db import schemas, get_db
from sqlalchemy.orm import Session
from datetime import datetime, timezone
import db.models as models
import api.auth as auth

router = APIRouter(tags=["quests"])


@router.get("/quests", response_model=list[schemas.QuestBase])
def read_quests(db: Session = Depends(get_db)):
    # Get all achievements from the database
    achievements = db.query(models.Quests).all()
    return achievements


@router.post("/quests", response_model=schemas.QuestBase)
def create_quests(quest: schemas.QuestCreate, db: Session = Depends(get_db)):
    # Create a new Achievement instance
    new_quest = models.Quests(
        name=quest.name,
        description=quest.description,
        location_long=quest.location_long,
        location_lat=quest.location_lat,
        start_date=quest.start_date,
        end_date=quest.end_date,
        points=quest.points,
        image=quest.image,
    )

    # Add and commit the quest to the database
    db.add(new_quest)
    db.commit()
    db.refresh(new_quest)  # Refresh to get the ID after insert

    return new_quest


@router.delete("/quests/{quest_id}", status_code=204)
def delete_quest(quest_id: int, db: Session = Depends(get_db)):
    # Check if quest exists
    quest = db.query(models.Quests).filter(models.Quests.id == quest_id).first()
    if quest is None:
        raise HTTPException(status_code=404, detail="Quest not found")

    # Delete the quest
    db.delete(quest)
    db.commit()

    return None


@router.put("/quests/{quest_id}", response_model=schemas.QuestBase)
def update_quest(
    quest_id: int, quest: schemas.QuestCreate, db: Session = Depends(get_db)
):
    # Check if quest exists
    existing_quest = (
        db.query(models.Quests).filter(models.Quests.id == quest_id).first()
    )
    if existing_quest is None:
        raise HTTPException(status_code=404, detail="Quest not found")

    else:
        existing_quest.name = quest.name  # type: ignore
        existing_quest.description = quest.description  # type: ignore
        existing_quest.location_long = quest.location_long  # type: ignore
        existing_quest.location_lat = quest.location_lat  # type: ignore
        existing_quest.start_date = quest.start_date  # type: ignore
        existing_quest.end_date = quest.end_date  # type: ignore
        existing_quest.points = quest.points  # type: ignore
        existing_quest.image = quest.image  # type: ignore

        db.commit()
        db.refresh(existing_quest)

        return existing_quest


@router.get("/{user_id}/quests", response_model=list[schemas.UserQuestsResponse])
def read_user_quests(user_id: int, db: Session = Depends(get_db)):
    user_quests = (
        db.query(models.UserQuests).filter(models.UserQuests.user_id == user_id).all()
    )
    return user_quests


@router.put("/quests", status_code=200)
def create_user_quest(quest: schemas.UserQuestsBase, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == quest.user_id).first()

    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    user_quest = (
        db.query(models.UserQuests)
        .filter(
            models.UserQuests.user_id == quest.user_id,
            models.UserQuests.quest_id == quest.quest_id,
        )
        .first()
    )

    if user_quest is not None:
        raise HTTPException(status_code=400, detail="User already has this quest")

    new_user_quest = models.UserQuests(
        user_id=quest.user_id,
        quest_id=quest.quest_id,
        date_completed=datetime.now(timezone.utc),
    )

    # add and commit the user quest to the database
    db.add(new_user_quest)
    db.commit()
    db.refresh(new_user_quest)

    return {"message": "Quest added successfully"}


# is done by the user
@router.put("/user-quests/{user_quest_id}/complete")
def complete_user_quest(
    user_quest_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(auth.decode_jwt),
):
    user_quest = (
        db.query(models.UserQuests)
        .filter(models.UserQuests.id == user_quest_id)
        .first()
    )

    # basic safeguard
    if user_quest is None:
        raise HTTPException(status_code=404, detail="Quest not found")

    if user_quest.is_done:
        raise HTTPException(status_code=400, detail="Quest already completed")

    # Authorization check: Ensure the logged-in user is the one associated with the quest
    if user_quest.user_id != user_id:
        raise HTTPException(
            status_code=403, detail="User not authorized to complete this quest"
        )

    user_quest.is_done = True
    db.commit()

    return {"message": "Quest completed successfully"}


@router.post("/verify-quest")
def verify_quest(
    verification: schemas.QuestVerification,
    db: Session = Depends(get_db),
    user_id: int = Depends(auth.decode_jwt),
):
    # Retrieve the quest completion record
    user_quest = (
        db.query(models.UserQuests)
        .filter(models.UserQuests.id == verification.user_quest_id)
        .first()
    )

    if not user_quest:
        raise HTTPException(status_code=404, detail="Quest completion not found")

    if not user_quest.is_done:
        raise HTTPException(
            status_code=400, detail="Quest not completed yet by the user"
        )

    # Check if the quest has already been fully verified
    if user_quest.is_verified:
        raise HTTPException(status_code=200, detail="Quest already fully verified")

    # Ensure the verifier is not the user who completed the quest
    if user_quest.user_id == user_id:
        raise HTTPException(
            status_code=403, detail="Cannot verify own quest completion"
        )

    # Check if this verifier has already verified this quest
    existing_verification = (
        db.query(models.QuestVerification)
        .filter(
            models.QuestVerification.user_quest_id == verification.user_quest_id,
            models.QuestVerification.verifier_id == user_id,
        )
        .first()
    )
    if existing_verification:
        raise HTTPException(
            status_code=400, detail="You have already verified this quest"
        )

    # todo add is done if you have time add it to user quest
    # todo existing verification can be done by adding a unique constraint on the PK
    # post will become user_quest that is verified + post count will be this too
    # badges  is user_achivement when user_id = profile
    # todo testing pytest probably

    # Add new verification
    new_verification = models.QuestVerification(
        user_quest_id=verification.user_quest_id, verifier_id=user_id
    )
    db.add(new_verification)
    db.commit()

    # Check if there are now 2 verifications
    verification_count = (
        db.query(models.QuestVerification)
        .filter(models.QuestVerification.user_quest_id == verification.user_quest_id)
        .count()
    )
    if verification_count >= 2:
        user_quest.is_verified = True
        db.commit()

    return {
        "message": "Verification successful",
        "total_verifications": verification_count,
    }
