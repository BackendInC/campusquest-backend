from fastapi import Depends, HTTPException, APIRouter
from db import schemas, get_db
from sqlalchemy.orm import Session
from sqlalchemy import desc
import db.models as models
import api.auth as auth


router = APIRouter()


def get_quest_id_from_user_quest_id(user_quest_id: int, db: Session):
    # get user quest object
    user_quest = (
        db.query(models.UserQuests)
        .filter(models.UserQuests.id == user_quest_id)
        .first()
    )
    return user_quest.quest_id


# read all posts no need for authentication since all users can see all posts
@router.get("/feed", response_model=list[schemas.FeedResponse])
def read_posts(db: Session = Depends(get_db)):
    # get all posts from the database sorted by created_at
    posts = db.query(models.Posts).order_by(desc(models.Posts.created_at)).all()
    feedPosts = []
    for post in posts:
        username = (
            db.query(models.User)
            .filter(models.User.id == post.user_id)
            .first()
            .username
        )
        feedPosts.append(
            schemas.FeedResponse(
                id=post.id,
                user_id=post.user_id,
                caption=post.caption,
                created_at=post.created_at,
                image_url=f"/posts/image/{post.id}",
                quest_id=get_quest_id_from_user_quest_id(post.user_quest_id, db),
                username=username,
                profile_picture_url=f"/users/profile_picture/{username}",
            )
        )

    return feedPosts


# get the posts by friends
@router.get("/feed/friends", response_model=list[schemas.FeedResponse])
def read_friends_posts(
    db: Session = Depends(get_db), user_id: int = Depends(auth.decode_jwt)
):
    # Get user friends
    try:
        friends = models.Friends.get_friends(user_id, db)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch friends: {str(e)}"
        )

    if not friends:
        return []

    # Get the posts with user_id in friends sorted by created_at
    try:
        posts = (
            db.query(models.Posts)
            .filter(
                models.Posts.user_id.in_([friend["friend_id"] for friend in friends])
            )
            .order_by(desc(models.Posts.created_at))
            .all()
        )

        feedPosts = []
        for post in posts:
            username = (
                db.query(models.User)
                .filter(models.User.id == post.user_id)
                .first()
                .username
            )
            feedPosts.append(
                schemas.FeedResponse(
                    id=post.id,
                    user_id=post.user_id,
                    caption=post.caption,
                    created_at=post.created_at,
                    image_url=f"/posts/image/{post.id}",
                    quest_id=get_quest_id_from_user_quest_id(post.user_quest_id, db),
                    username=username,
                    profile_picture_url=f"/users/profile_picture/{username}",
                )
            )

        return feedPosts
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch posts: {str(e)}")
