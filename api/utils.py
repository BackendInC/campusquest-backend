import bcrypt
import random
from db import models, get_db
from sqlalchemy.orm import Session

SALT = b"$2b$12$oWEEctwkZY/CUopCVaM92O"


def create_salt() -> str:
    return bcrypt.gensalt().decode("utf-8")


# Hash password
def hash_password(password: str, salt: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), salt.encode("utf-8")).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(
        plain_password.encode("utf-8"), hashed_password.encode("utf-8")
    )


def get_random_string(length: int) -> str:
    return "".join(
        random.choices(
            "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789", k=length
        )
    )


def get_random_int() -> int:
    return random.randint(1, 1000)
