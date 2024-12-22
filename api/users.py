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

MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

router = APIRouter()


@router.post("/users", response_model=schemas.UserResponse)
def create_user(user: schemas.UserCreate, db: session = Depends(get_db)):
    # create a new user instance

    salt = utils.create_salt()
    hashed_password = utils.hash_password(user.password, salt)

    new_user = models.User(
        username=user.username,
        email=user.email,
        password=hashed_password,
        salt=salt,
        num_quests_completed=0,
        tokens=0,
    )

    try:
        # add and commit the user to the database
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        verificationInstance = models.EmailVerificationCode(user_id=new_user.id)

        models.EmailVerificationCode.create(verificationInstance, db)
        models.EmailVerificationCode.send_email(
            verificationInstance.code, new_user.email
        )

        return new_user

    except exc.sa_exc.IntegrityError:
        raise HTTPException(status_code=400, detail="username or email already exists")


@router.post("/user/login", status_code=200)
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

        print(new_session)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create session {e}")

    return {"jwt_token": new_session.session_token}


@router.post("/user/profile_picture/upload", status_code=200)
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


@router.get("/user/profile_picture/{username}", status_code=200)
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


@router.get("/user/{user_id}", response_model=schemas.ProfileInfoResponse)
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
        db.query(models.PostLikes).filter(models.PostLikes.user_id == user_id).count()
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
        num_posts=num_posts,
        num_likes=num_likes,
        num_achievements=num_achievements,
        num_quests_completed=num_quests_completed,
        num_friends=num_friends,
        post_ids=post_ids,
    )
