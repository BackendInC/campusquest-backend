from db import models
from db import get_db
from api import auth
from fastapi import APIRouter, Depends

router = APIRouter(tags=["admin"])


@router.post("/ban_user/{user_id}")
def ban_user(
    user_id: int,
    reason: str,
    admin_id: int = Depends(auth.verify_admin),
    db=Depends(get_db),
):
    models.BannedUsers.ban_user(user_id, reason, db)
    return {"message": "User has been banned!"}
