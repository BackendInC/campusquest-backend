from fastapi import Depends, HTTPException, APIRouter
from db import schemas, get_db
from sqlalchemy.orm import Session
from datetime import datetime, timezone
import db.models as models

sessionRouter = APIRouter()


def create_session(user_id: int, db: Session):
    # Create a new session token
    session_token = f"{user_id}-{datetime.now(timezone.utc).isoformat()}"
    new_session = models.Sessions(user_id=user_id, session_token=session_token)
    db.add(new_session)
    db.commit()
    db.refresh(new_session)
    return new_session
