import jwt
from datetime import datetime, timedelta
from fastapi import HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

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


def check_admin(credentials: HTTPAuthorizationCredentials = Security(security)):
    user_id = decode_jwt(credentials)
    if user_id != 1:
        raise HTTPException(status_code=403, detail="You are not an admin!")
    return user_id
