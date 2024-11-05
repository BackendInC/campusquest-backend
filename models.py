from sqlalchemy import Column, Integer, String, DateTime, Date, LargeBinary
from datetime import datetime
from db import Base

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String, nullable=False, unique=True)
    password = Column(String, nullable=False)
    email = Column(String, nullable=False, unique=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    profile_picture = Column(LargeBinary)  # Blob field for profile picture
    date_of_birth = Column(Date, nullable=True)
    num_quests_completed = Column(Integer, default=0)
    tokens = Column(Integer, default=0)
    
    def __repr__(self):
        return (f"<User(id={self.id}, username={self.username}, email={self.email}, "
                f"created_at={self.created_at}, num_quests_completed={self.num_quests_completed}, "
                f"tokens={self.tokens})>")

