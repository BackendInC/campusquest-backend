# This file includes the SQLAlchemy models for the database tables.

from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Date,
    LargeBinary,
    ForeignKey,
    UniqueConstraint,
    Float,
)
from sqlalchemy.orm import relationship
from datetime import datetime, timezone, timedelta
from db import Base



class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String, nullable=False, unique=True)
    password = Column(String, nullable=False)
    salt = Column(String, nullable=False)
    email = Column(String, nullable=False, unique=True)
    created_at = Column(DateTime, default=datetime.now(timezone.utc))
    profile_picture = Column(LargeBinary, nullable=True)  # Blob field for profile picture
    date_of_birth = Column(Date, nullable=True)
    num_quests_completed = Column(Integer, default=0)
    tokens = Column(Integer, default=0)

    posts = relationship("Posts", back_populates="user")
    likes = relationship("PostLikes", back_populates="user")
    comments = relationship("PostComments", back_populates="user")

    # relationships
    quests = relationship("UserQuests", back_populates="user")

    def __repr__(self):
        return (
            f"<User(id={self.id}, username={self.username}, email={self.email}, "
            f"created_at={self.created_at}, num_quests_completed={self.num_quests_completed}, "
            f"tokens={self.tokens})>"
        )

class Sessions(Base):
    __tablename__ = "sessions"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False)
    session_token = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.now(timezone.utc))
    expires_at = Column(
        DateTime, default=datetime.now(timezone.utc) + timedelta(days=1)
    )

    def __repr__(self):
        return (
            f"<Sessions(id={self.id}, user_id={self.user_id}, session_token={self.session_token}, "
            f"created_at={self.created_at}, expires_at={self.expires_at})>"
        )

class Achievements(Base):
    __tablename__ = "achievements"

    id = Column(Integer, primary_key=True, autoincrement=True)
    description = Column(String, nullable=False)
    award_tokens = Column(Integer, nullable=False)

    def __repr__(self):
        return f"<Achievements(id={self.id}, description={self.description}, award_tokens={self.award_tokens})>"
        return f"<Achievements(id={self.id}, description={self.description}, award_tokens={self.award_tokens})>"


class UserAchievements(Base):
    __tablename__ = "user_achievements"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False)
    achievement_id = Column(Integer, nullable=False)
    date_achieved = Column(DateTime, default=datetime.now(timezone.utc))


    def __repr__(self):
        return (f"<UserAchievements(id={self.id}, user_id={self.user_id}, achievement_id={self.achievement_id}, "
            f"date_achieved={self.date_achieved})>")


class Quests(Base):
    __tablename__ = 'quests'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=False)

    location_long = Column(Float, nullable=True)
    location_lat = Column(Float, nullable=True)
    image = Column(LargeBinary, nullable=True) #put base64 encoded image here
    points = Column(Integer, nullable=False) # Points awarded for completing the quest
    start_date = Column(Date, nullable=False, default=datetime.now(timezone.utc))
    end_date = Column(DateTime, nullable=True)
    date_posted = Column(DateTime, default=datetime.now(timezone.utc))

    # Relationships
    users = relationship("UserQuests", back_populates="quest")

    def __repr__(self):
        return (f"<Quest(id={self.id}, title={self.title}, description={self.description}, "
                f"reward_tokens={self.reward_tokens}, date_posted={self.date_posted}, "
                f"date_due={self.date_due}, user_id={self.user_id})>")

class Posts(Base):
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    caption = Column(String(255), nullable=False)
    image = Column(LargeBinary, nullable=True)
    created_at = Column(DateTime, default=datetime.now(timezone.utc))

    user = relationship("User", back_populates="posts")
    likes = relationship(
        "PostLikes", back_populates="post", cascade="all, delete-orphan"
    )
    comments = relationship(
        "PostComments", back_populates="post", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return (
            f"<Posts(id={self.id}, caption={self.caption}, user_id={self.user_id}, "
            f"created_at={self.created_at})>"
        )


class PostLikes(Base):
    __tablename__ = "post_likes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    post_id = Column(Integer, ForeignKey("posts.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.now(timezone.utc))

    __table_args__ = (UniqueConstraint("post_id", "user_id", name="_post_user_uc"),)

    post = relationship("Posts", back_populates="likes")
    user = relationship("User", back_populates="likes")

    def __repr__(self):
        return (
            f"<PostLikes(id={self.id}, post_id={self.post_id}, user_id={self.user_id}, "
            f"created_at={self.created_at})>"
        )


class PostComments(Base):
    __tablename__ = "post_comments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    post_id = Column(Integer, ForeignKey("posts.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    content = Column(String(500), nullable=False)
    created_at = Column(DateTime, default=datetime.now(timezone.utc))

    post = relationship("Posts", back_populates="comments")
    user = relationship("User", back_populates="comments")

    def __repr__(self):
        return (
            f"<PostComments(id={self.id}, post_id={self.post_id}, user_id={self.user_id}, "
            f"content={self.content}, created_at={self.created_at})>"
        )

class UserQuests(Base):
    __tablename__ = 'user_quests'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer,ForeignKey('users.id'), nullable=False)
    quest_id = Column(Integer,ForeignKey('quests.id'), nullable=False)
    date_completed = Column(DateTime, default=datetime.now(timezone.utc))

    # Relationships
    user = relationship("User", back_populates="quests")
    quest = relationship("Quests", back_populates="users")


    def __repr__(self):
        return (f"<UserQuests(id={self.id}, user_id={self.user_id}, quest_id={self.quest_id}, "
                f"date_completed={self.date_completed})>")
