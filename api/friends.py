from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import session
from db import get_db, schemas, models
import api.utils as utils
import api.auth as auth

router = APIRouter()

#add a new friend
@router.post("/friends", response_model=schemas.FriendResponse)
def add_friend(
    friend: schemas.FriendCreate, 
    db: session = Depends(get_db), 
    user_id: int = Depends(auth.decode_jwt)
):    
    #create a new friend instance
    return models.Friends.create_friend(user_id, friend.friend_id, db)


#remove a friend
@router.delete("/friends/{friend_id}", status_code=200)
def remove_friend(
    friend_id: int, 
    db: session = Depends(get_db), 
    user_id: int = Depends(auth.decode_jwt)
):
    #remove a friend instance
    return models.Friends.remove_friend(user_id, friend_id, db)

#list all friends
@router.get("/friends", response_model=list[schemas.FriendResponse])
def list_friends(
    db: session = Depends(get_db), 
    user_id: int = Depends(auth.decode_jwt)
):
    #list all friends
    return models.Friends.list_friends(user_id, db)

