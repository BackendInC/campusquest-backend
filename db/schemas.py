# This folder contains the schemes for the responses and requests of the API

from pydantic import BaseModel
from typing import Optional, List
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


class UserLogin(BaseModel):
    username: str
    password: str


class ProfileInfoResponse(BaseModel):
    username: str
    num_posts: int
    num_likes: int
    num_achievements: int
    num_quests_completed: int
    num_friends: int
    post_ids: List[int]

    class Config:
        orm_mode = True


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


class PostBase(BaseModel):
    user_id: int
    image: bytes
    caption: str
    created_at: datetime

    class Config:
        orm_mode = True


class PostCreate(BaseModel):
    user_id: int
    image: bytes
    caption: str

    class Config:
        orm_mode = True


class PostResponse(PostBase):
    id: int  # autoincrement id
    user_id: int
    image: str
    caption: str
    created_at: datetime

    class Config:
        orm_mode = True


class PostUpdate(BaseModel):
    caption: str

    class Config:
        orm_mode = True


class PostLikeBase(BaseModel):
    user_id: int
    post_id: int

    class Config:
        orm_mode = True


class PostLikeCreate(BaseModel):
    user_id: int
    post_id: int

    class Config:
        orm_mode = True


class PostLikeResponse(PostLikeBase):
    id: int  # autoincrement id
    message: Optional[str] = None


class PostCommentBase(BaseModel):
    user_id: int
    post_id: int
    content: str
    created_at: datetime

    class Config:
        orm_mode = True


class PostCommentCreate(BaseModel):
    content: str

    class Config:
        orm_mode = True


class PostCommentResponse(PostCommentBase):
    id: int  # autoincrement id


class EmailVerificationInput(BaseModel):
    username: str
    code: int

    class Config:
        orm_mode = True


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


class QuestRead(QuestBase):
    id: int

    class Config:
        orm_mode = True


class QuestDelete(BaseModel):
    id: int

    class Config:
        orm_mode = True


class UserQuestsBase(BaseModel):
    user_id: int
    quest_id: int

    class Config:
        orm_mode = True


class UserQuestsResponse(UserQuestsBase):
    id: int


class QuestVerification(BaseModel):
    user_quest_id: int

    class Config:
        orm_mode = True


class FriendBase(BaseModel):
    user_id: int
    friend_id: int

    class Config:
        orm_mode = True


class FriendCreate(FriendBase):
    id: int  # autoincrement id

    class Config:
        orm_mode = True


class FriendResponse(FriendBase):
    id: int  # autoincrement id

    class Config:
        orm_mode = True
