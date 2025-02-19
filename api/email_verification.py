from fastapi import Depends, HTTPException, APIRouter, File, UploadFile, Form
from sqlalchemy.orm import Session
from db import schemas, get_db, models
import api.auth as auth
import base64

router = APIRouter(tags=["users"])  # create an instance of the APIRouter class


@router.post("/users/verify", status_code=200)
def verify(
    code_user: schemas.EmailVerificationInput,
    db: Session = Depends(get_db),
):
    models.EmailVerificationCode.verify(code_user.code, code_user.username, db)
    return {"message": f"{code_user}"}
