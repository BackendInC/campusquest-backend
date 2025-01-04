from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import session
from db import get_db, schemas, models
import api.utils as utils
import api.auth as auth

router = APIRouter()

#add a new friend
@router.post("/friends", response_model=schemas.FriendCreateResponse)
def add_friend(
    friend: schemas.FriendCreate, 
    db: session = Depends(get_db), 
    user_id: int = Depends(auth.decode_jwt)
):  
    try:  
        #create a new friend instance
        response = models.Friends.create_friend(user_id, friend.friend_id, db)

        return schemas.FriendCreateResponse(
            id=response.id,
            friend_id=response.friend_id,
            user_id=response.user_id,
            message="Friend added successfully"
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


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
    return models.Friends.get_friends(user_id, db)

#check if a user is a friend
@router.get("/friends/{friend_id}", response_model=bool)
def check_friend(
    friend_id: int, 
    db: session = Depends(get_db), 
    user_id: int = Depends(auth.decode_jwt)
):
    #check if a user is a friend
    return models.Friends.are_friends(user_id, friend_id, db)

#get mutual friends
@router.get("/friends/mutual/{friend_id}", response_model=list[schemas.MutualFriendResponse])
def get_mutual_friends(
    friend_id: int, 
    db: session = Depends(get_db), 
    user_id: int = Depends(auth.decode_jwt)
):
    #get mutual friends
    return models.Friends.get_mutuals(user_id, friend_id, db)