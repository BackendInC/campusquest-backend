# This file includes the SQLAlchemy models for the database tables.

from sqlalchemy import Column, Integer,Float, String, DateTime, Date, LargeBinary
from datetime import datetime, timezone
from db import Base

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String, nullable=False, unique=True)
    password = Column(String, nullable=False)
    email = Column(String, nullable=False, unique=True)
    created_at = Column(DateTime, default=datetime.now(timezone.utc))
    profile_picture = Column(LargeBinary)  # Blob field for profile picture
    date_of_birth = Column(Date, nullable=True)
    num_quests_completed = Column(Integer, default=0)
    tokens = Column(Integer, default=0)

    def __repr__(self):
        return (f"<User(id={self.id}, username={self.username}, email={self.email}, "
                f"created_at={self.created_at}, num_quests_completed={self.num_quests_completed}, "
                f"tokens={self.tokens})>")


class Achievements(Base):
    __tablename__ = 'achievements'

    id = Column(Integer, primary_key=True, autoincrement=True)
    description = Column(String, nullable=False)
    award_tokens = Column(Integer, nullable=False)


    def __repr__(self):
        return (f"<Achievements(id={self.id}, description={self.description}, award_tokens={self.award_tokens})>")



class UserAchievements(Base):
    __tablename__ = 'user_achievements'

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

    def __repr__(self):
        return (f"<Quest(id={self.id}, title={self.title}, description={self.description}, "
                f"reward_tokens={self.reward_tokens}, date_posted={self.date_posted}, "
                f"date_due={self.date_due}, user_id={self.user_id})>")
