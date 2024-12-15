from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import session, exc

from db import get_db
from db import schemas
from db import models

import api.utils as utils
import api.auth as auth


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
    user = (
        db.query(models.User)
        .filter(models.User.username == userRequest.username)
        .first()
    )

    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

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

