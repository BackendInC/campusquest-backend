from fastapi import APIRouter, Depends
from sqlalchemy.orm import session
from db import get_db, schemas, models
import api.auth as auth
from api.achievements_service import AchievementService

router = APIRouter()


# add a new friend
@router.post("/friends/{friend_id}", response_model=schemas.FriendResponse)
def add_friend(
    friend_id: int,
    db: session = Depends(get_db),
    user_id: int = Depends(auth.decode_jwt),
):
    # create a new friend instance
    response = models.Friends.create_friend(user_id, friend_id, db)
    new_achievements = AchievementService.check_achievements(user_id, db)
    response["new_achievements"] = new_achievements
    return response


# remove a friend
@router.delete("/friends/{friend_id}", status_code=200)
def remove_friend(
    friend_id: int,
    db: session = Depends(get_db),
    user_id: int = Depends(auth.decode_jwt),
):
    # remove a friend instance
    return models.Friends.remove_friend(user_id, friend_id, db)


# list all friends
@router.get("/friends", response_model=list[int])
def list_friends(
    db: session = Depends(get_db), user_id: int = Depends(auth.decode_jwt)
):
    # list all friends
    return models.Friends.list_friends(user_id, db)


# check if a user is a friend
@router.get("/friends/{friend_id}", response_model=schemas.FriendResponse)
def check_friend(
    friend_id: int,
    db: session = Depends(get_db),
    user_id: int = Depends(auth.decode_jwt),
):
    # check if a user is a friend
    return models.Friends.check_friend(user_id, friend_id, db)


# get mutual friends
@router.get("/friends/mutuals/{friend_id}", response_model=list[schemas.FriendResponse])
def get_mutual_friends(
    friend_id: int,
    db: session = Depends(get_db),
    user_id: int = Depends(auth.decode_jwt),
):
    # get mutual friends
    return models.Friends.get_mutual_friends(user_id, friend_id, db)
