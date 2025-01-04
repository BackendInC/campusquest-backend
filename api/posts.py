from fastapi import Depends, HTTPException, APIRouter, File, UploadFile, Form, Response
from sqlalchemy.orm import Session
from db import schemas, get_db, models
import api.auth as auth
import base64
from io import BytesIO
from PIL import Image
from sqlalchemy import func, case

router = APIRouter()

MAX_FILE_SIZE = 5 * 1024 * 1024
ALLOWED_CONTENT_TYPES = ["image/jpeg", "image/png"]


@router.post("/posts", response_model=schemas.PostCreateResponse)
async def create_post(
    caption: str = Form(...),
    image: UploadFile = File(...),
    db: Session = Depends(get_db),
    quest_id: int = Form(...),
    current_user: int = Depends(auth.decode_jwt),
):
    try:
        # Check if the user has a post for this quest+id already
        if models.Posts.check_posted(current_user, quest_id, db):
            raise HTTPException(status_code=400, detail="User has already submitted.")

        # Upload the image
        image_data = await models.Posts.upload_image(image)

        # create new userquest and new post
        new_post = models.Posts.create_post_transcation(
            current_user, quest_id, caption, image_data, db
        )

        return schemas.PostCreateResponse(
            id=new_post.id,
            user_id=new_post.user_id,
            caption=new_post.caption,
            created_at=new_post.created_at,
            image_url=f"/posts/image/{new_post.id}",
            quest_id=quest_id,
        )

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Failed to create post: {str(e)}")


# read all posts information
@router.get("/posts", response_model=list[schemas.PostResponse])
def read_posts(
    db: Session = Depends(get_db), current_user: int = Depends(auth.decode_jwt)
):

    # Get all posts
    posts = models.Posts.get_all(db)

    # Map query results to response model
    return [
        schemas.PostResponse(
            id=post.id,
            user_id=post.user_id,
            caption=post.caption,
            likes_count=post.likes_count,
            dislikes_count=post.dislikes_count,
            created_at=post.created_at,
            image_url=f"/posts/image/{post.id}",
            quest_id=models.UserQuests.get_quest_id(post.user_quest_id, db),
            username=post.username,
            profile_picture_url=f"/users/profile_picture/{post.username}",
        )
        for post in posts
    ]


# read post information by post_id
@router.get("/posts/{post_id}", response_model=schemas.PostResponse)
def read_post(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: int = Depends(auth.decode_jwt),
):

    # Get the post by ID
    post, likes_count, dislikes_count, username = models.Posts.get_by_id(post_id, db)

    # Return the response
    return schemas.PostResponse(
        id=post.id,
        user_id=post.user_id,
        caption=post.caption,
        likes_count=likes_count,
        dislikes_count=dislikes_count,
        created_at=post.created_at,
        image_url=f"/posts/image/{post.id}",
        quest_id=models.UserQuests.get_quest_id(post.user_quest_id, db),
        username=username,
        profile_picture_url=f"/users/profile_picture/{username}",
    )


# get post image
@router.get("/posts/image/{post_id}", status_code=200)
async def get_image(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: int = Depends(auth.decode_jwt),
):
    post = db.query(models.Posts).filter(models.Posts.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    if not post.image:
        raise HTTPException(status_code=404, detail="Image not found")

    try:
        image = Image.open(BytesIO(post.image))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get image: {e}")

    # encode the image as JPEG
    buffer = BytesIO()
    image.save(buffer, format="JPEG")
    buffer.seek(0)

    return Response(content=buffer.getvalue(), media_type="image/jpeg")


# read all posts by a user
@router.get("/users/posts/{user_id}", response_model=list[schemas.PostResponse])
def read_user_posts(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: int = Depends(auth.decode_jwt),
):
    posts = models.Posts.get_by_user(user_id, db)

    return [
        schemas.PostResponse(
            id=post.id,
            user_id=post.user_id,
            caption=post.caption,
            likes_count=post.likes_count,
            dislikes_count=post.dislikes_count,
            created_at=post.created_at,
            image_url=f"/posts/image/{post.id}",
            quest_id=models.UserQuests.get_quest_id(post.user_quest_id, db),
            username=post.username,
            profile_picture_url=f"/users/profile_picture/{post.username}",
        )
        for post in posts
    ]


# update a post by id
@router.put("/posts/{post_id}", response_model=schemas.PostUpdateResponse)
def update_post(
    post_id: int,
    post: schemas.PostUpdate,
    db: Session = Depends(get_db),
    current_user: int = Depends(auth.decode_jwt),
):
    try:
        response = models.Posts.update(post_id, post.caption, current_user, db)
        return response
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to update post: {str(e)}")


# delete a post by id
@router.delete("/posts/{post_id}", status_code=200)
def delete_post(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: int = Depends(auth.decode_jwt),
):
    try:
        response = models.UserQuests.delete(post_id, current_user, db)
        return response
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to delete post: {str(e)}")


# like and unlike a post
@router.post("/posts/like/{post_id}", response_model=schemas.PostReactionResponse)
def toggle_like(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: int = Depends(auth.decode_jwt),
):
    # check if post exists
    post = db.query(models.Posts).filter(models.Posts.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    # check if the user has liked the post
    like = models.PostReactions.is_liked(current_user, post_id, db)

    # unlike the post if the user has liked it
    if like is not None:
        response = like.unlike_post(db)
        return response

    # check if the user disliked the post
    dislike = models.PostReactions.is_disliked(current_user, post_id, db)

    # remove dislike if the user has disliked the post
    if dislike is not None:
        response = dislike.remove_dislike(db)

    # like the post if the user has not liked it
    response = models.PostReactions.like_post(current_user, post_id, db)
    return response


# dislike and remove dislike
@router.post("/posts/dislike/{post_id}", response_model=schemas.PostReactionResponse)
def toggle_dislike(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: int = Depends(auth.decode_jwt),
):
    # check if post exists
    post = db.query(models.Posts).filter(models.Posts.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    # check if the user has disliked the post
    dislike = models.PostReactions.is_disliked(current_user, post_id, db)

    # undo the dislike if the user has disliked it
    if dislike is not None:
        response = dislike.remove_dislike(db)
        return response

    # check if the user liked the post
    like = models.PostReactions.is_liked(current_user, post_id, db)

    # remove like if the user has liked the post
    if like is not None:
        response = like.unlike_post(db)

    # dislike the post if the user has not liked or disliked it
    response = models.PostReactions.dislike_post(current_user, post_id, db)
    return response


# check if a user has liked a post
@router.get("/posts/like/{post_id}", response_model=bool)
def check_user_like(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: int = Depends(auth.decode_jwt),
):
    # check if post exists
    post = db.query(models.Posts).filter(models.Posts.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    # check if the user has liked the post
    like = models.PostReactions.is_liked(current_user, post_id, db)

    if like:
        return True
    return False


# check if a user has disliked a post
@router.get("/posts/dislike/{post_id}", response_model=bool)
def check_user_dislike(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: int = Depends(auth.decode_jwt),
):
    # check if post exists
    post = db.query(models.Posts).filter(models.Posts.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    # check if the user has disliked the post
    dislike = models.PostReactions.is_disliked(current_user, post_id, db)

    if dislike:
        return True
    return False


# read all users who liked a post
@router.get("/posts/likedby/{post_id}", response_model=list[schemas.UserResponse])
def read_post_likedby(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: int = Depends(auth.decode_jwt),
):
    # check if post exists
    post = db.query(models.Posts).filter(models.Posts.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    # get all users who liked a post
    try:
        users = models.PostReactions.get_likedby(post_id, db)
        if users:
            return users
        return []

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to get users: {str(e)}")


# read all users who disliked a post
@router.get("/posts/dislikedby/{post_id}", response_model=list[schemas.UserResponse])
def read_post_dislikedby(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: int = Depends(auth.decode_jwt),
):
    # check if post exists
    post = db.query(models.Posts).filter(models.Posts.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    # get all users who disliked a post
    try:
        users = models.PostReactions.get_dislikedby(post_id, db)
        if users:
            return users
        return []

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to get users: {str(e)}")
