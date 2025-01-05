# This file includes the SQLAlchemy models for the database tables.
from random import randint
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from io import BytesIO
from PIL import Image
from sqlalchemy import func, case, text
from sqlalchemy.dialects.postgresql import ENUM
import enum


from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Response
from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Date,
    LargeBinary,
    ForeignKey,
    UniqueConstraint,
    CheckConstraint,
    Float,
    Boolean,
    or_,
    and_,
)

from sqlalchemy.orm import Session, relationship, aliased
from datetime import datetime, timezone, timedelta
from db import Base
import base64
import api.utils as utils
import db.schemas as schemas

MAX_FILE_SIZE = 5 * 1024 * 1024
ALLOWED_CONTENT_TYPES = ["image/jpeg", "image/png"]


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
    is_email_verified = Column(Boolean, nullable=False, default=False)

    selected_bee: int = Column(Integer, nullable=False, default=0)

    is_email_verified = Column(Boolean, nullable=False, default=False)

    # Relationships
    posts = relationship("Posts", back_populates="user", cascade="all, delete-orphan")
    reactions = relationship(
        "PostReactions", back_populates="user", cascade="all, delete-orphan"
    )

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

        return new_user

    @staticmethod
    def get_user(user_id, db):
        return db.query(User).filter(User.id == user_id).first()


class BannedUsers(Base):
    __tablename__ = "banned_users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    banned_at = Column(DateTime, default=datetime.now(timezone.utc))

    reason = Column(String, nullable=False)

    @staticmethod
    def ban_user(user_id, reason, db):
        if BannedUsers.is_banned(user_id, db):
            raise HTTPException(status_code=400, detail="User is already banned")
        banned_user = BannedUsers(user_id=user_id, reason=reason)
        db.add(banned_user)
        db.commit()
        db.refresh(banned_user)
        return banned_user

    @staticmethod
    def is_banned(user_id, db):
        return (
            db.query(BannedUsers).filter(BannedUsers.user_id == user_id).first()
            is not None
        )

    def __repr__(self):
        return (
            f"<BannedUsers(id={self.id}, user_id={self.user_id}, banned_at={self.banned_at}, "
            f"reason={self.reason})>"
        )


class Admin(Base):
    __tablename__ = "admins"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    def __repr__(self):
        return f"<Admin(id={self.id}, user_id={self.user_id})>"

    @staticmethod
    def verify_admin(user_id, db):
        return db.query(Admin).filter(Admin.user_id == user_id).first() is not None


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

    @staticmethod
    def load_achievements(milestones: dict, db: Session):
        for milestone, achievement in milestones.items():
            new_achievement = Achievements(
                id=achievement["id"],
                description=achievement["description"],
                award_tokens=achievement["award_tokens"],
            )
            db.add(new_achievement)

        # Commit the achievements
        db.commit()

        # Update the sequence to the maximum ID value
        # This ensures future auto-incremented IDs start after your manually set IDs
        db.execute(
            text(
                """
            SELECT setval(
                pg_get_serial_sequence('achievements', 'id'),
                COALESCE((SELECT MAX(id) FROM achievements), 0)
            );
        """
            )
        )
        db.commit()


class UserAchievements(Base):
    __tablename__ = "user_achievements"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    achievement_id = Column(Integer, ForeignKey("achievements.id"), nullable=False)
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
    image = Column(LargeBinary, nullable=True)  # put base64 encoded image here
    location_long = Column(Float, nullable=True)
    location_lat = Column(Float, nullable=True)
    points = Column(Integer, nullable=False)  # Points awarded for completing the quest
    start_date = Column(Date, nullable=False, default=datetime.now(timezone.utc))
    end_date = Column(DateTime, nullable=True)
    date_posted = Column(DateTime, default=datetime.now(timezone.utc))

    # Relationships

    def __repr__(self):
        return (
            f"<Quest(id={self.id}, title={self.name}, description={self.description}, "
            f"reward_tokens={self.points}, date_posted={self.date_posted}, "
            f"date_due={self.end_date}"
        )


class Posts(Base):
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    caption = Column(String(255), nullable=False)
    image = Column(LargeBinary, nullable=True)
    created_at = Column(DateTime, default=datetime.now(timezone.utc))
    user_quest_id = Column(Integer, ForeignKey("user_quests.id"), nullable=False)

    user = relationship("User", back_populates="posts")
    user_quest = relationship("UserQuests", back_populates="post")
    reactions = relationship(
        "PostReactions", back_populates="post", cascade="all, delete-orphan"
    )

    __table_args__ = (
        UniqueConstraint("user_quest_id", "user_id", name="_user_quest_user_post_uc"),
    )

    def __repr__(self):
        return (
            f"<Posts(id={self.id}, caption={self.caption}, user_id={self.user_id}, "
            f"created_at={self.created_at}, user_quest_id={self.user_quest_id})>"
        )

    @staticmethod
    def check_posted(user_id, quest_id, db):
        user_quest_id = (
            db.query(UserQuests.id)
            .filter(
                UserQuests.user_id == user_id,
                UserQuests.quest_id == quest_id,
            )
            .first()
        )

        if user_quest_id:
            return True

        post = (
            db.query(Posts)
            .filter(
                Posts.user_quest_id == user_quest_id,
            )
            .first()
        )

        if post:
            return True

        return False

    @staticmethod
    async def upload_image(image: UploadFile = File(...)):
        # validate image type
        if image.content_type not in ALLOWED_CONTENT_TYPES:
            raise HTTPException(
                status_code=400, detail="Only JPEG and PNG images are allowed"
            )

        # read the raw file contents
        contents = await image.read()

        # validate file size
        if len(contents) > MAX_FILE_SIZE:
            raise HTTPException(status_code=400, detail="File size too large")

        # Try to open the image using Pillow
        try:
            image = Image.open(BytesIO(contents))
            if image.format not in ["JPEG", "PNG"]:
                raise HTTPException(status_code=400, detail="Invalid file format")
        except Exception as e:
            raise HTTPException(status_code=400, detail="Invalid image file")

        # Convert RGBA to RGB
        if image.mode == "RGBA":
            image = image.convert("RGB")

        # convert and encode as JPEG for consistency
        buffer = BytesIO()
        image.save(buffer, format="JPEG", quality=85)
        buffer.seek(0)
        image_data = buffer.getvalue()

        return image_data

    @staticmethod
    def create_post_transcation(user_id, quest_id, caption, image_data, db):
        try:
            # create a new user quest and flush to get the id
            new_user_quest = UserQuests(
                user_id=user_id,
                quest_id=quest_id,
                is_done=True,
            )

            db.add(new_user_quest)
            db.flush()

            # create a new post
            new_post = Posts(
                user_id=user_id,
                caption=caption,
                image=image_data,
                user_quest_id=new_user_quest.id,
            )

            db.add(new_post)
            db.commit()
            db.refresh(new_post)

            return new_post

        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=500, detail=f"Failed to create post: {str(e)}"
            )

    @staticmethod
    def get_all(db):
        posts = (
            db.query(
                Posts.id,
                Posts.user_id,
                Posts.caption,
                Posts.created_at,
                Posts.user_quest_id,
                func.count(case((PostReactions.reaction_type == "LIKE", 1))).label(
                    "likes_count"
                ),
                func.count(case((PostReactions.reaction_type == "DISLIKE", 1))).label(
                    "dislikes_count"
                ),
                User.username,  # Directly joining User to fetch the username
            )
            .outerjoin(PostReactions, PostReactions.post_id == Posts.id)
            .join(User, User.id == Posts.user_id)  # Join the User table directly
            .group_by(Posts.id, User.id)  # Group by both Posts and User
            .all()
        )

        return posts

    @staticmethod
    def get_by_id(post_id, db):
        # Get the post by ID
        post = db.query(Posts).filter(Posts.id == post_id).first()

        # Check if post exists
        if not post:
            raise HTTPException(status_code=404, detail="Post not found")

        # Count likes and dislikes for the post
        likes_count = (
            db.query(func.count(PostReactions.id))
            .filter(
                PostReactions.post_id == post.id, PostReactions.reaction_type == "LIKE"
            )
            .scalar()
        )

        dislikes_count = (
            db.query(func.count(PostReactions.id))
            .filter(
                PostReactions.post_id == post.id,
                PostReactions.reaction_type == "DISLIKE",
            )
            .scalar()
        )

        # Get user info
        username = (db.query(User.username).filter(User.id == post.user_id)).scalar()

        # Get quest name
        quest_name = (
            db.query(Quests.name)
            .join(UserQuests, UserQuests.quest_id == Quests.id)
            .filter(UserQuests.id == post.user_quest_id)
            .scalar()
        )

        return post, likes_count, dislikes_count, username, quest_name

    @staticmethod
    def get_by_user(user_id, db):
        # Check if user exists
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Query posts with aggregated likes and dislikes count
        posts = (
            db.query(
                Posts.id,
                Posts.user_id,
                Posts.caption,
                Posts.created_at,
                Posts.user_quest_id,
                func.count(case((PostReactions.reaction_type == "LIKE", 1))).label(
                    "likes_count"
                ),
                func.count(case((PostReactions.reaction_type == "DISLIKE", 1))).label(
                    "dislikes_count"
                ),
                User.username,
            )
            .filter(Posts.user_id == user_id)
            .outerjoin(PostReactions, PostReactions.post_id == Posts.id)
            .join(User, User.id == Posts.user_id)
            .group_by(
                Posts.id, User.id
            )  # Add User.id here to group by both Posts and User
            .all()
        )

        return posts

    @staticmethod
    def update(post_id, caption, current_user, db):
        # get the post by id
        post_db = db.query(Posts).filter(Posts.id == post_id).first()

        # check if post exists
        if not post_db:
            raise HTTPException(status_code=404, detail="Post not found")

        # check if the user owns the post
        if post_db.user_id != current_user:
            raise HTTPException(
                status_code=403, detail="You are not the owner of this post"
            )

        # update the post
        try:
            post_db.caption = caption
            db.commit()
            db.refresh(post_db)

            return schemas.PostUpdateResponse(
                id=post_db.id,
                user_id=post_db.user_id,
                caption=post_db.caption,
            )

        except Exception as e:
            raise HTTPException(
                status_code=400, detail=f"Failed to update post: {str(e)}"
            )


class ReactionType(enum.Enum):
    LIKE = "LIKE"
    DISLIKE = "DISLIKE"


reaction_type_enum = ENUM(ReactionType, name="reactiontype")


class PostReactions(Base):
    __tablename__ = "post_reactions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    post_id = Column(Integer, ForeignKey("posts.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    reaction_type = Column(reaction_type_enum, nullable=False)
    created_at = Column(DateTime, default=datetime.now(timezone.utc))

    __table_args__ = (UniqueConstraint("post_id", "user_id", name="_post_user_uc"),)

    post = relationship("Posts", back_populates="reactions")
    user = relationship("User", back_populates="reactions")

    def __repr__(self):
        return (
            f"<PostReactions(id={self.id}, post_id={self.post_id}, user_id={self.user_id}, "
            f"reaction_type={self.reaction_type}, created_at={self.created_at})>"
        )

    @staticmethod
    def is_liked(post_id, user_id, db):
        like = (
            db.query(PostReactions)
            .filter(
                PostReactions.user_id == user_id,
                PostReactions.post_id == post_id,
                PostReactions.reaction_type == "LIKE",
            )
            .first()
        )

        return like

    def unlike_post(self, db):
        try:
            response = schemas.PostReactionResponse(
                id=self.id,
                user_id=self.user_id,
                post_id=self.post_id,
                message="Post unliked successfully",
            )
            db.delete(self)
            db.commit()
            return response
        except Exception as e:
            raise HTTPException(
                status_code=400, detail=f"Failed to unlike post: {str(e)}"
            )

    @staticmethod
    def is_disliked(post_id, user_id, db):
        dislike = (
            db.query(PostReactions)
            .filter(
                PostReactions.user_id == user_id,
                PostReactions.post_id == post_id,
                PostReactions.reaction_type == "DISLIKE",
            )
            .first()
        )

        return dislike

    def remove_dislike(self, db):
        try:
            response = schemas.PostReactionResponse(
                id=self.id,
                user_id=self.user_id,
                post_id=self.post_id,
                message="Dislike removed successfully",
            )
            db.delete(self)
            db.commit()
            return response
        except Exception as e:
            raise HTTPException(
                status_code=400, detail=f"Failed to remove dislike: {str(e)}"
            )

    @staticmethod
    def like_post(post_id, user_id, db):
        new_like = PostReactions(user_id=user_id, post_id=post_id, reaction_type="LIKE")

        try:
            db.add(new_like)
            db.commit()
            db.refresh(new_like)

            response = schemas.PostReactionResponse(
                id=new_like.id,
                user_id=new_like.user_id,
                post_id=new_like.post_id,
                message="Post liked successfully",
            )
            return response

        except Exception as e:
            raise HTTPException(
                status_code=400, detail=f"Failed to like post: {str(e)}"
            )

    @staticmethod
    def dislike_post(post_id, user_id, db):
        new_dislike = PostReactions(
            user_id=user_id, post_id=post_id, reaction_type="DISLIKE"
        )

        try:
            db.add(new_dislike)
            db.commit()
            db.refresh(new_dislike)

            response = schemas.PostReactionResponse(
                id=new_dislike.id,
                user_id=new_dislike.user_id,
                post_id=new_dislike.post_id,
                message="Post disliked successfully",
            )
            return response

        except Exception as e:
            raise HTTPException(
                status_code=400, detail=f"Failed to dislike post: {str(e)}"
            )

    @staticmethod
    def get_likedby(post_id, db):
        users = (
            db.query(User)
            .join(PostReactions)
            .filter(
                PostReactions.post_id == post_id,
                PostReactions.reaction_type == "LIKE",
            )
            .all()
        )

        return users

    @staticmethod
    def get_dislikedby(post_id, db):
        users = (
            db.query(User)
            .join(PostReactions)
            .filter(
                PostReactions.post_id == post_id,
                PostReactions.reaction_type == "DISLIKE",
            )
            .all()
        )

        return users

    @staticmethod
    def get_likes_count(post_id, db):
        # check if post exists
        post = db.query(Posts).filter(Posts.id == post_id).first()
        if not post:
            raise HTTPException(status_code=404, detail="Post not found")

        # count the number of likes for a post
        try:
            count = (
                db.query(PostReactions)
                .filter(
                    PostReactions.post_id == post_id,
                    PostReactions.reaction_type == "LIKE",
                )
                .count()
            )
            return count

        except Exception as e:
            raise HTTPException(
                status_code=400, detail=f"Failed to get likes count: {str(e)}"
            )

    @staticmethod
    def get_dislikes_count(post_id, db):
        # check if post exists
        post = db.query(Posts).filter(Posts.id == post_id).first()
        if not post:
            raise HTTPException(status_code=404, detail="Post not found")

        # count the number of dislikes for a post
        try:
            count = (
                db.query(PostReactions)
                .filter(
                    PostReactions.post_id == post_id,
                    PostReactions.reaction_type == "DISLIKE",
                )
                .count()
            )
            return count

        except Exception as e:
            raise HTTPException(
                status_code=400, detail=f"Failed to get dislikes count: {str(e)}"
            )


class EmailVerificationCode(Base):
    __tablename__ = "verfication_codes"
    code = Column(Integer, nullable=False)
    username = Column(String, primary_key=True)
    valid_until = Column(
        DateTime(timezone=True),
        default=datetime.now(timezone.utc) + timedelta(minutes=15),
    )

    @staticmethod
    def create(verificationInstance, db: Session) -> int:
        verificationInstance.code = randint(100000, 1000000)
        try:
            # check if previous code for this user exists that is still valid
            old_code = (
                db.query(EmailVerificationCode)
                .filter(EmailVerificationCode.username == verificationInstance.username)
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

            # if doesnt exist then save and return the new verificationInstance
            db.add(verificationInstance)

        except Exception as e:
            raise HTTPException(status_code=500, detail=e)

    @staticmethod
    def verify(code: int, username: str, db: Session):
        try:
            old_code = (
                db.query(EmailVerificationCode)
                .filter(EmailVerificationCode.username == username)
                .first()
            )
            if old_code:
                if old_code.code == code:
                    user = db.query(User).filter(User.username == username).first()
                    user.is_email_verified = True
                    db.delete(old_code)
                    db.commit()
                    db.refresh(user)
                    return {"messsage": f"{code} {user}"}
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

    post = relationship(
        "Posts", back_populates="user_quest", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return (
            f"<UserQuests(id={self.id}, user_id={self.user_id}, quest_id={self.quest_id}, is_done={self.is_done}, "
            f"date_completed={self.date_completed}, is_verified={self.is_verified} )>"
        )

    @staticmethod
    def get_quest_id(user_quest_id: int, db: Session):
        # get user quest object
        user_quest = db.query(UserQuests).filter(UserQuests.id == user_quest_id).first()
        return user_quest.quest_id

    @staticmethod
    def delete(post_id: int, user_id: int, db: Session):
        # get the post by id
        post = db.query(Posts).filter(Posts.id == post_id).first()
        if not post:
            raise HTTPException(status_code=404, detail="Post not found")

        # check if the user is the owner of the post
        if post.user_id != user_id:
            raise HTTPException(
                status_code=403, detail="You are not the owner of this post"
            )

        # get the user_quest
        user_quest = (
            db.query(UserQuests).filter(UserQuests.id == post.user_quest_id).first()
        )

        if not user_quest:
            raise HTTPException(status_code=404, detail="UserQuest not found")

        # delete the post
        try:
            db.delete(user_quest)
            db.commit()
            return {"detail": "Post and UserQuest deleted successfully"}

        except Exception as e:
            raise HTTPException(
                status_code=400, detail=f"Failed to delete post: {str(e)}"
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
    __table_args__ = (
        UniqueConstraint("user_id", "friend_id", name="_user_friend_uc"),
        CheckConstraint("user_id < friend_id", name="_user_not_friend"),
        CheckConstraint("user_id != friend_id", name="_user_not_self"),
    )

    def __repr__(self):
        return f"<Friends(id={self.id}, user_id={self.user_id}, friend_id={self.friend_id}, created_at={self.created_at})>"

    @staticmethod
    def are_friends(user_id: int, friend_id: int, db: Session) -> bool:
        # Ensure that the user and friend are not the same
        if user_id == friend_id:
            return False

        # sort the user and friend IDs to ensure consistency
        user, friend = sorted([user_id, friend_id])

        # Check if the users are already friends
        response = (
            db.query(Friends)
            .filter(Friends.user_id == user, Friends.friend_id == friend)
            .first()
        )

        if response is None:
            return False

        return True

    @staticmethod
    def create_friend(user_id, friend_id, db) -> "Friends":
        # check if the user is a user
        user = db.query(User).filter(User.id == user_id).first()

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

        # sort the user and friend IDs to ensure consistency
        user_id, friend_id = sorted([user_id, friend_id])

        # create a new friend instance
        new_friendship = Friends(user_id=user_id, friend_id=friend_id)

        # add and commit the friend to the database
        try:
            db.add(new_friendship)
            db.commit()
            db.refresh(new_friendship)

            return new_friendship

        except HTTPException as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to create friend {e}")

    @staticmethod
    def remove_friend(user_id, friend_id, db):
        # check if the user is a user
        user = db.query(User).filter(User.id == user_id).first()

        # check if the friend is a user
        friend_user = db.query(User).filter(User.id == friend_id).first()

        if not (friend_user and user):
            raise HTTPException(status_code=404, detail="Friend not found")

        # prevent removing yourself as a friend
        if user_id == friend_id:
            raise HTTPException(
                status_code=400, detail="Cannot remove yourself as a friend"
            )

        # sort the user and friend IDs to ensure consistency
        user_id, friend_id = sorted([user_id, friend_id])

        # Query the Friend instance from the database
        friendship = (
            db.query(Friends)
            .filter(
                or_(
                    and_(Friends.user_id == user_id, Friends.friend_id == friend_id),
                    and_(Friends.user_id == friend_id, Friends.friend_id == user_id),
                )
            )
            .first()
        )

        if friendship is None:
            raise HTTPException(status_code=400, detail="Not friends with this user")

        # remove the friend
        try:
            db.delete(friendship)
            db.commit()
            return {"detail": "Friend removed successfully"}

        except HTTPException as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to remove friend {e}")

    @staticmethod
    def get_friends(user_id, db):
        # Check if the user exists
        user = db.query(User).filter(User.id == user_id).first()

        if user is None:
            raise HTTPException(status_code=404, detail="User not found")

        # Get all friends with additional details
        friendships = (
            db.query(Friends)
            .filter((Friends.user_id == user_id) | (Friends.friend_id == user_id))
            .all()
        )

        # Process friends to include binary profile picture
        friends_details = []
        for friendship in friendships:
            if friendship.user_id == user_id:
                friend_id = friendship.friend.id
                username = friendship.friend.username
            else:
                friend_id = friendship.user.id
                username = friendship.user.username

            # Append the processed friend data
            friends_details.append(
                {
                    "id": friendship.id,
                    "friend_id": friend_id,
                    "username": username,
                    "profile_picture_url": f"/users/profile_picture/{username}",
                }
            )

        return friends_details

    @staticmethod
    def get_mutuals(user_id, friend_id, db):
        # Check if both users exist
        users_exist = (
            db.query(User.id).filter(User.id.in_([user_id, friend_id])).count()
        )
        if users_exist < 2:
            raise HTTPException(status_code=404, detail="One or both users not found")

        # Get friend IDs for the first user
        user_friend_ids = (
            db.query(Friends.user_id, Friends.friend_id)
            .filter((Friends.user_id == user_id) | (Friends.friend_id == user_id))
            .all()
        )
        # Correct the set comprehension
        user_friend_ids = {f1 if f1 != user_id else f2 for f1, f2 in user_friend_ids}

        # Get friend IDs for the second user
        friend_friend_ids = (
            db.query(Friends.user_id, Friends.friend_id)
            .filter((Friends.user_id == friend_id) | (Friends.friend_id == friend_id))
            .all()
        )
        # Correct the set comprehension
        friend_friend_ids = {
            f1 if f1 != friend_id else f2 for f1, f2 in friend_friend_ids
        }

        # Get mutual friend IDs
        mutual_friend_ids = user_friend_ids.intersection(friend_friend_ids)

        # Fetch mutual friend details
        mutual_friends = db.query(User).filter(User.id.in_(mutual_friend_ids)).all()

        if not mutual_friends:
            return []

        # Return mutual friends as a list of dictionaries
        return [
            schemas.MutualFriendResponse(
                friend_id=mf.id,
                username=mf.username,
                profile_picture_url=f"/users/profile_picture/{mf.username}",
            )
            for mf in mutual_friends
        ]
