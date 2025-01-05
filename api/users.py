from email.policy import HTTP
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Response
from sqlalchemy.orm import session, exc
from io import BytesIO
from PIL import Image

from db import get_db
from db import schemas
from db import models

import api.utils as utils
import api.auth as auth
import os

MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

router = APIRouter(tags=["users"])


@router.post("/users", response_model=schemas.UserResponse)
def create_user(user: schemas.UserCreate, db: session = Depends(get_db)):
    new_user = None
    try:
        new_user = models.User.create_user(user, db)
        if os.getenv("TEST") == "1":
            new_user.is_email_verified = True
            db.commit()
            db.refresh(new_user)
            return new_user

        verificationInstance = models.EmailVerificationCode(username=new_user.username)
        try:
            models.EmailVerificationCode.create(verificationInstance, db)
            models.EmailVerificationCode.send_email(
                verificationInstance.code, new_user.email
            )
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=str(e))
        db.commit()
        db.refresh(new_user)
        return new_user

    except exc.sa_exc.IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="username or email already exists")


@router.post("/users/login", status_code=200)
def login_user(userRequest: schemas.UserLogin, db: session = Depends(get_db)):
    # get the user by username
    user: models.User = (
        db.query(models.User)
        .filter(models.User.username == userRequest.username)
        .first()
    )

    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    if not user.is_email_verified:
        raise HTTPException(status_code=401, detail="User is not verified")
    if models.BannedUsers.is_banned(user.id, db):
        raise HTTPException(status_code=403, detail="User is banned")

    # check if the password is correct
    hashed_password = utils.hash_password(userRequest.password, user.salt)
    if hashed_password != user.password:
        raise HTTPException(status_code=400, detail="Incorrect password")

    # create a new session
    session_token = auth.generate_jwt(user.id)
    new_session = models.Sessions(user_id=user.id, session_token=session_token)

    # add and commit the session to
    try:
        db.add(new_session)
        db.commit()
        db.refresh(new_session)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create session {e}")
    return {
        "jwt_token": new_session.session_token,
        "user": {"id": user.id, "username": user.username, "email": user.email},
    }


@router.get("/user_info")
def get_profile(
    db: session = Depends(get_db), current_user: int = Depends(auth.decode_jwt)
):
    user: models.User = (
        db.query(models.User).filter(models.User.id == current_user).first()
    )
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "selected_bee": user.selected_bee,
    }


@router.post("/users/profile_picture/upload", status_code=200)
async def upload_profile_picture(
    profile_picture: UploadFile = File(...),
    db: session = Depends(get_db),
    user_id: int = Depends(auth.decode_jwt),
):
    # Check for file type
    if profile_picture.content_type not in ["image/jpeg", "image/png"]:
        raise HTTPException(status_code=400, detail="Invalid file type")

    contents = await profile_picture.read()

    # Check for file size
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File size too large")

    image = Image.open(BytesIO(contents))

    # Convert RGBA to RGB
    if image.mode == "RGBA":
        image = image.convert("RGB")

    # Convert and encode as JPEG for consistency
    buffer = BytesIO()
    image.save(buffer, format="JPEG", quality=85)  # Adjust quality if needed
    buffer.seek(0)

    # Store the binary data in the database
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.profile_picture = buffer.getvalue()

    try:
        db.commit()
        db.refresh(user)
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500, detail=f"Failed to upload profile picture: {e}"
        )

    return {"message": "Profile picture uploaded successfully"}


@router.get("/users/profile_picture/{username}", status_code=200)
async def get_profile_picture(username: str, db: session = Depends(get_db)):
    user: models.User = (
        db.query(models.User).filter(models.User.username == username).first()
    )
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    if user.profile_picture is None:
        raise HTTPException(status_code=404, detail="Profile picture not found")

    # Decode the binary data to an image
    try:
        image = Image.open(BytesIO(user.profile_picture))
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to process image")

    # Encode the image as JPEG
    buffer = BytesIO()
    image.save(buffer, format="JPEG")
    buffer.seek(0)

    # Return the JPEG image
    return Response(content=buffer.getvalue(), media_type="image/jpeg")


@router.get("/users/{user_id}", response_model=schemas.ProfileInfoResponse)
def get_profile_info(
    user_id: int,
    db: session = Depends(get_db),
    current_user: int = Depends(auth.decode_jwt),
):
    # get the user by id
    user = db.query(models.User).filter(models.User.id == user_id).first()

    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    # count the number of posts
    num_posts = db.query(models.Posts).filter(models.Posts.user_id == user_id).count()

    # count the number of likes
    num_likes = (
        db.query(models.PostReactions)
        .filter(
            models.PostReactions.user_id == user_id,
            models.PostReactions.reaction_type == "LIKE",
        )
        .count()
    )

    # count the number of achievements
    num_achievements = (
        db.query(models.UserAchievements)
        .filter(models.UserAchievements.user_id == user_id)
        .count()
    )

    # number of completed quests
    num_quests_completed = user.num_quests_completed

    # get number of friends
    num_friends = (
        db.query(models.Friends)
        .filter(
            (models.Friends.user_id == user_id) | (models.Friends.friend_id == user_id)
        )
        .count()
    )

    # get all post ids
    post_ids = [
        post.id
        for post in db.query(models.Posts).filter(models.Posts.user_id == user_id).all()
    ]

    return schemas.ProfileInfoResponse(
        username=user.username,
        selected_bee=user.selected_bee,
        num_posts=num_posts,
        num_likes=num_likes,
        num_achievements=num_achievements,
        num_quests_completed=num_quests_completed,
        num_friends=num_friends,
        post_ids=post_ids,
    )


@router.post("/users_change_bee")
def change(
    new_bee: int,
    db: session = Depends(get_db),
    current_user: int = Depends(auth.decode_jwt),
):
    # get the user by id
    user = db.query(models.User).filter(models.User.id == current_user).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    user.selected_bee = new_bee
    db.commit()
    db.refresh(user)
    return {"message:": "Bee updated successfully", "new_bee": user.selected_bee}


@router.put("/users/update/password")
async def update_user_password(
    password: str,
    db: session = Depends(get_db),
    user_id: int = Depends(auth.decode_jwt),
):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    user.password = utils.hash_password(password, user.salt)
    db.commit()
    db.refresh(user)
    return user


@router.put("/users/update/email")
async def update_user_mail(
    email: str,
    db: session = Depends(get_db),
    user_id: int = Depends(auth.decode_jwt),
):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    user.email = email
    db.commit()
    db.refresh(user)
    return user


@router.put("/users/update/username")
async def update_user_username(
    username: str,
    db: session = Depends(get_db),
    user_id: int = Depends(auth.decode_jwt),
):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    user.username = username
    db.commit()
    db.refresh(user)
    return user
