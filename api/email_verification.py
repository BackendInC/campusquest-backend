from fastapi import Depends, HTTPException, APIRouter, File, UploadFile, Form
from sqlalchemy.orm import Session
from db import schemas, get_db, models
import api.auth as auth
import base64

router = APIRouter()  # create an instance of the APIRouter class


@router.post("/users/verification", status_code=200)
def verify(
    code_user_id: schemas.EmailVerificationInput,
    db: Session = Depends(get_db),
):
    models.EmailVerificationCode.verify(code_user_id.code, code_user_id.user_id, db)
