# This folder contains the schemes for the responses and requests of the API

from pydantic import BaseModel
from typing import Optional
from datetime import datetime, date

class UserBase(BaseModel):
    username: str
    email: str
    date_of_birth: Optional[date] = None
    num_quests_completed: int = 0
    tokens: int = 0

    class Config:
        orm_mode = True  # Enable compatibility with SQLAlchemy


class UserCreate(BaseModel):
    username: str
    email: str
    password: str
    date_of_birth: date

    class Config:
        orm_mode = True


class UserResponse(UserBase):
    id: int
    created_at: datetime


class AchievementBase(BaseModel):
    description: str
    award_tokens: int

    class Config:
        orm_mode = True


class AchievementResponse(AchievementBase):
    id: int


class UserAchievementBase(BaseModel):
    user_id: int
    achievement_id: int

    class Config:
        orm_mode = True

class UserAchievementResponse(UserAchievementBase):
    id: int


class QuestBase(BaseModel):
    name: str
    description: str

    location_long: float
    location_lat: float
    points: int
    start_date: date
    end_date: date
    image: bytes

class QuestCreate(QuestBase):
    class Config:
        orm_mode = True


class QuestDelete(BaseModel):
    id: int

    class Config:
        orm_mode = True
