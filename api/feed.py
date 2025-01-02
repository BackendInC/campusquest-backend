from fastapi import Depends, HTTPException, APIRouter
from db import schemas, get_db
from sqlalchemy.orm import Session
from sqlalchemy import desc
from datetime import datetime, timezone
import db.models as models
import api.auth as auth
import base64


router = APIRouter()

# read all posts no need for authentication since all users can see all posts
@router.get("/posts/feed", response_model=list[schemas.PostResponse])
def read_posts(db: Session = Depends(get_db)):
    # get all posts from the database sorted by created_at
    posts = db.query(models.Posts).order_by(desc(models.Posts.created_at)).all()

    # decode the image as base64
    for post in posts:
        if post.image:
            post.image = base64.b64encode(post.image).decode("utf-8")

    return posts

# get the posts by friends
@router.get("/posts/friends", response_model=schemas.PostResponse)
def read_friends_posts(db: Session = Depends(get_db), user_id: int = Depends(auth.decode_jwt)):
    # Get user friends
    try:
        friends = db.query(models.Friends).filter(models.Friends.user_id == user_id).all()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch friends: {str(e)}")

    if not friends:
        return []  # or raise HTTPException(status_code=404, detail="No friends found") better to return empty list

    # Get the posts with user_id in friends sorted by created_at
    try:
        posts = db.query(models.Posts) \
            .filter(models.Posts.user_id.in_([friend.friend_id for friend in friends])) \
            .order_by(desc(models.Posts.created_at)) \
            .all()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch posts: {str(e)}")

    # decode the image as base64
    for post in posts:
        if post.image:
            post.image = base64.b64encode(post.image).decode("utf-8")

    return posts

