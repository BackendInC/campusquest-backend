# This file includes the SQLAlchemy models for the database tables.
from random import randint
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


from fastapi import HTTPException
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
    Boolean,
    or_,
    and_,
)

from sqlalchemy.orm import Session, relationship
from datetime import datetime, timezone, timedelta
from db import Base
import base64
import api.utils as utils
import db.schemas as schemas


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String, nullable=False, unique=True)
    password = Column(String, nullable=False)
    salt = Column(String, nullable=False)
    email = Column(String, nullable=False, unique=True)
    created_at = Column(DateTime, default=datetime.now(timezone.utc))
    profile_picture = Column(
        LargeBinary, nullable=True
    )  # Blob field for profile picture
    date_of_birth = Column(Date, nullable=True)
    num_quests_completed = Column(Integer, default=0)
    tokens = Column(Integer, default=0)

    posts = relationship("Posts", back_populates="user")
    likes = relationship("PostLikes", back_populates="user")
    comments = relationship("PostComments", back_populates="user")

    # relationships
    quests = relationship("UserQuests", back_populates="user")

    is_email_verified = Column(Boolean, nullable=False, default=False)

    def __repr__(self):
        return (
            f"<User(id={self.id}, username={self.username}, email={self.email}, "
            f"created_at={self.created_at}, num_quests_completed={self.num_quests_completed}, "
            f"tokens={self.tokens})>"
        )

    @staticmethod
    def create_user(new_user_params: schemas.UserCreate, db):
        salt = utils.create_salt()
        hashed_password = utils.hash_password(new_user_params.password, salt)

        new_user = User(
            username=new_user_params.username,
            email=new_user_params.email,
            password=hashed_password,
            salt=salt,
            num_quests_completed=0,
            tokens=0,
        )

        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        return new_user

    @staticmethod
    def get_user(user_id, db):
        return db.query(User).filter(User.id == user_id).first()


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
        return (
            f"<UserAchievements(id={self.id}, user_id={self.user_id}, achievement_id={self.achievement_id}, "
            f"date_achieved={self.date_achieved})>"
        )


class Quests(Base):
    __tablename__ = "quests"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=False)

    location_long = Column(Float, nullable=True)
    location_lat = Column(Float, nullable=True)
    image = Column(LargeBinary, nullable=True)  # put base64 encoded image here
    points = Column(Integer, nullable=False)  # Points awarded for completing the quest
    start_date = Column(Date, nullable=False, default=datetime.now(timezone.utc))
    end_date = Column(DateTime, nullable=True)
    date_posted = Column(DateTime, default=datetime.now(timezone.utc))

    # Relationships
    users = relationship("UserQuests", back_populates="quest")

    def __repr__(self):
        return (
            f"<Quest(id={self.id}, title={self.title}, description={self.description}, "
            f"reward_tokens={self.reward_tokens}, date_posted={self.date_posted}, "
            f"date_due={self.date_due}, user_id={self.user_id})>"
        )


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

    @staticmethod
    def create(new_post, db):
        try:
            db.add(new_post)
            db.commit()
            db.refresh(new_post)

            return {
                "id": new_post.id,
                "user_id": new_post.user_id,
                "caption": new_post.caption,
                "created_at": new_post.created_at,
                "image": base64.b64encode(new_post.image).decode(
                    "utf-8"
                ),  # encode the image as base64
            }

        except Exception as e:
            raise HTTPException(
                status_code=400, detail=f"Failed to create post: {str(e)}"
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


class EmailVerificationCode(Base):
    __tablename__ = "verfication_codes"
    code = Column(Integer, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    valid_until = Column(
        DateTime, default=datetime.now(timezone.utc) + timedelta(minutes=15)
    )

    @staticmethod
    def create(verificationInstance, db: Session) -> int:
        verificationInstance.code = randint(100000, 1000000)
        try:
            # check if previous code for this user exists that is still valid
            old_code = (
                db.query(EmailVerificationCode)
                .filter(EmailVerificationCode.user_id == verificationInstance.user_id)
                .first()
            )

            # if exists and valid return the same code
            if old_code is not None and old_code.valid_until > datetime.now(
                timezone.utc
            ):
                raise HTTPException(500, "A valid verification code exists.")

            # if exists and invalid then destroy the old one and save the new verificationInstance
            if old_code is not None and old_code.valid_until < datetime.now(
                timezone.utc
            ):
                db.delete(old_code)
                db.commit()

            # if doesnt exist then save and return the new verificationInstance
            db.add(verificationInstance)
            db.commit()

        except Exception as e:
            raise HTTPException(status_code=500, detail=e)

    @staticmethod
    def verify(code: int, user_id: int, db: Session):
        try:
            old_code = (
                db.query(EmailVerificationCode)
                .filter(EmailVerificationCode.user_id == user_id)
                .first()
            )
            if old_code:
                if old_code.code == code:
                    user = db.query(User).filter(User.id == user_id).first()
                    user.is_email_verified = True
                    db.commit()
                    db.refresh(user)
                    return {"messsage": f"{code} {user} "}
                else:
                    raise HTTPException(
                        status_code=500, detail="Wrong verication code."
                    )
            else:
                raise HTTPException(
                    status_code=500,
                    detail="There is no verification code for this user.",
                )

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"{e}")

    @staticmethod
    def send_email(code: int, email: str):
        # me == my email address
        # you == recipient's email address
        fromaddr = "campus.quest.itu@gmail.com"
        toaddrs = email

        # Create message container - the correct MIME type is multipart/alternative.
        msg = MIMEMultipart("alternative")
        msg["Subject"] = "Campus Quest Verification Code"
        msg["From"] = fromaddr
        msg["To"] = toaddrs

        # Create the body of the message (a plain-text and an HTML version).
        html = f"""\
        <html>
          <head></head>
          <body>
            <h1>Your verification code is: {code}</h1>
          </body>
        </html>
        """

        # Record the MIME types of both parts - text/plain and text/html.
        part2 = MIMEText(html, "html")

        # Attach parts into message container.
        # According to RFC 2046, the last part of a multipart message, in this case
        # the HTML message, is best and preferred.
        msg.attach(part2)

        server = smtplib.SMTP("smtp.gmail.com:587")
        server.starttls()
        server.login(fromaddr, "ksgk jaid xekg sdft")
        server.sendmail(fromaddr, toaddrs, msg.as_string())
        server.quit()


class UserQuests(Base):
    __tablename__ = "user_quests"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    quest_id = Column(Integer, ForeignKey("quests.id"), nullable=False)
    is_done = Column(Boolean, default=False, nullable=False)
    date_completed = Column(DateTime, default=datetime.now(timezone.utc))
    is_verified = Column(Boolean, default=False, nullable=False)

    # Relationships
    user = relationship("User", back_populates="quests")
    quest = relationship("Quests", back_populates="users")

    def __repr__(self):
        return (
            f"<UserQuests(id={self.id}, user_id={self.user_id}, quest_id={self.quest_id}, is_done={self.is_done}, "
            f"date_completed={self.date_completed}, is_verified={self.is_verified} )>"
        )


class QuestVerification(Base):
    __tablename__ = "quests_verification"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_quest_id = Column(Integer, ForeignKey("user_quests.id"), nullable=False)
    verifier_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    verified_at = Column(DateTime, default=datetime.now(timezone.utc))

    def __repr__(self):
        return (
            f"<QuestsVerification(id={self.id}, user_id={self.user_id}, quest_id={self.quest_id}, "
            f"verifier_id={self.verifier_id}, verified_at={self.verified_at})>"
        )


class Friends(Base):
    __tablename__ = "friends"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    friend_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.now(timezone.utc))

    # relationships
    user = relationship("User", foreign_keys=[user_id])
    friend = relationship("User", foreign_keys=[friend_id])

    # Ensure that a user cannot be friends with the same user twice
    __table_args__ = (UniqueConstraint("user_id", "friend_id", name="_user_friend_uc"),)

    def __repr__(self):
        return f"<Friends(id={self.id}, user_id={self.user_id}, friend_id={self.friend_id}, created_at={self.created_at})>"

    @staticmethod
    def are_friends(user_id, friend_id, db) -> bool:
        # Check if the users are already friends
        return (
            db.query(Friends)
            .filter(
                or_(
                    and_(Friends.user_id == user_id, Friends.friend_id == friend_id),
                    and_(Friends.user_id == friend_id, Friends.friend_id == user_id),
                )
            )
            .first()
            is not None
        )

    @staticmethod
    def create_friend(user_id, friend_id, db) -> "Friends":
        # check if the friend is a user
        friend_user = db.query(User).filter(User.id == friend_id).first()

        if friend_user is None:
            raise HTTPException(status_code=404, detail="Friend not found")

        # prevent adding yourself as a friend
        if user_id == friend_id:
            raise HTTPException(
                status_code=400, detail="Cannot add yourself as a friend"
            )

        # check if the user is already friends with the friend
        if Friends.are_friends(user_id, friend_id, db):
            raise HTTPException(
                status_code=400, detail="Already friends with this user"
            )

        # create a new friend instance
        new_friend = Friends(user_id=user_id, friend_id=friend_id)

        # add and commit the friend to the database
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
        # check if the user is a user
        user = db.query(User).filter(User.id == user_id).first()

        # check if the friend is a user
        friend_user = db.query(User).filter(User.id == friend_id).first()

        if not (friend_user or user):
            raise HTTPException(status_code=404, detail="Friend not found")

        # prevent removing yourself as a friend
        if user_id == friend_id:
            raise HTTPException(
                status_code=400, detail="Cannot remove yourself as a friend"
            )

        # check if the user is already friends with the friend
        friend = Friends.are_friends(user_id, friend_id, db)
        if friend is None:
            raise HTTPException(status_code=400, detail="Not friends with this user")

        # remove the friend
        try:
            db.delete(friend)
            db.commit()

        except HTTPException as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to remove friend {e}")

    @staticmethod
    def get_friends(user_id, db):
        # check if the user is a user
        user = db.query(User).filter(User.id == user_id).first()

        if user is None:
            raise HTTPException(status_code=404, detail="User not found")

        # get all friends of the user
        friends = db.query(Friends).filter(Friends.user_id == user_id).all()
        return friends

    @staticmethod
    def get_mutual_friends(user_id, friend_id, db):
        # check if the user is a user
        user = db.query(User).filter(User.id == user_id).first()

        # check if the friend is a user
        friend_user = db.query(User).filter(User.id == friend_id).first()

        if not (friend_user or user):
            raise HTTPException(status_code=404, detail="Friend not found")

        # get all friends of the user
        user_friends = db.query(Friends).filter(Friends.user_id == user_id).all()
        friend_friends = db.query(Friends).filter(Friends.user_id == friend_id).all()

        # get mutual friends
        mutual_friends = [friend for friend in user_friends if friend in friend_friends]
        return mutual_friends
