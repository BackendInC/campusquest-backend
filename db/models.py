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
    or_,
    and_,
)
from sqlalchemy.orm import relationship
from datetime import datetime, timezone, timedelta
from db import Base
from fastapi import HTTPException



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

class Friends(Base):
    __tablename__ = "friends"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    friend_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.now(timezone.utc))

    #relationships
    user = relationship("User", foreign_keys=[user_id])
    friend = relationship("User", foreign_keys=[friend_id])

    # Ensure that a user cannot be friends with the same user twice
    __table_args__ = (UniqueConstraint("user_id", "friend_id", name="_user_friend_uc"),)

    def __repr__(self):
        return f"<Friends(id={self.id}, user_id={self.user_id}, friend_id={self.friend_id}, created_at={self.created_at})>"
    
    @staticmethod
    def are_friends(user_id, friend_id, db) -> bool:
        # Check if the users are already friends
        return db.query(Friends).filter(
            or_(
                and_(Friends.user_id == user_id, Friends.friend_id == friend_id),
                and_(Friends.user_id == friend_id, Friends.friend_id == user_id),
            )
        ).first() is not None
    
    @staticmethod
    def create_friend(user_id, friend_id, db) -> "Friends":
        #check if the friend is a user
        friend_user = db.query(User).filter(User.id == friend_id).first()

        if friend_user is None:
            raise HTTPException(status_code=404, detail="Friend not found")
        
        #prevent adding yourself as a friend
        if user_id == friend_id:
            raise HTTPException(status_code=400, detail="Cannot add yourself as a friend")
        
        #check if the user is already friends with the friend
        if Friends.are_friends(user_id, friend_id, db):
            raise HTTPException(status_code=400, detail="Already friends with this user")
        
        #create a new friend instance
        new_friend = Friends(
            user_id=user_id,
            friend_id=friend_id
        )

        #add and commit the friend to the database
        try:
            db.add(new_friend)
            db.commit()
            db.refresh(new_friend)

            return new_friend
        
        except HTTPException as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to create friend {e}")
    
    @staticmethod
    def remove_friend(user_id, friend_id, db):
        #check if the user is a user
        user = db.query(User).filter(User.id == user_id).first()

        #check if the friend is a user
        friend_user = db.query(User).filter(User.id == friend_id).first()

        if not (friend_user or user):
            raise HTTPException(status_code=404, detail="Friend not found")
        
        #prevent removing yourself as a friend
        if user_id == friend_id:
            raise HTTPException(status_code=400, detail="Cannot remove yourself as a friend")
        
        #check if the user is already friends with the friend
        friend = Friends.are_friends(user_id, friend_id, db)
        if friend is None:
            raise HTTPException(status_code=400, detail="Not friends with this user")
        
        #remove the friend
        try:
            db.delete(friend)
            db.commit()
        
        except HTTPException as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to remove friend {e}")
        

    @staticmethod
    def get_friends(user_id, db):
        #check if the user is a user
        user = db.query(User).filter(User.id == user_id).first()

        if user is None:
            raise HTTPException(status_code=404, detail="User not found")

        #get all friends of the user
        friends = db.query(Friends).filter(Friends.user_id == user_id).all()
        return friends
    
    @staticmethod
    def get_mutual_friends(user_id, friend_id, db):
        #check if the user is a user
        user = db.query(User).filter(User.id == user_id).first()

        #check if the friend is a user
        friend_user = db.query(User).filter(User.id == friend_id).first()

        if not (friend_user or user):
            raise HTTPException(status_code=404, detail="Friend not found")
        
        #get all friends of the user
        user_friends = db.query(Friends).filter(Friends.user_id == user_id).all()
        friend_friends = db.query(Friends).filter(Friends.user_id == friend_id).all()

        #get mutual friends
        mutual_friends = [friend for friend in user_friends if friend in friend_friends]
        return mutual_friends
