import jwt
from datetime import datetime, timedelta
from fastapi import HTTPException, Security, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from db import models, get_db, Session

# Secret key to sign the token
SECRET_KEY = "your-secret-key"
FORMAT = "%Y-%m-%d %H:%M:%S"


# Function to generate a JWT
def generate_jwt(user_id, secret_key=SECRET_KEY):
    payload = {
        "user_id": user_id,
        "expires": (datetime.utcnow() + timedelta(days=1)).strftime(FORMAT),
    }

    token = jwt.encode(payload, secret_key, algorithm="HS256")
    return token


# HTTP Bearer token scheme
security = HTTPBearer()


# Function to decode a JWT
def decode_jwt(credentials: HTTPAuthorizationCredentials = Security(security)) -> int:
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=["HS256"])
        if datetime.strptime(payload["expires"], FORMAT) < datetime.utcnow():
            raise HTTPException(status_code=401, detail="Token has expired!")
        return payload["user_id"]
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired!")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token!")


# Same as decode_jwt but for admin users only
def verify_admin(
    credentials: HTTPAuthorizationCredentials = Security(security),
    db: Session = Depends(get_db),
) -> int:
    user_id = decode_jwt(credentials)

    # Check if the user is an admin
    if models.Admin.verify_admin(user_id, db):
        return user_id
    else:
        raise HTTPException(
            status_code=401, detail="User is not authorized to perform this action"
        )
