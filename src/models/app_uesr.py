from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from .base import Base

class FamilyMember(Base):
    __tablename__ = 'family_member'
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    points = Column(Integer, default=0)
    tasks = relationship('Task', backref='assignee', lazy=True)
    splitwise_user_id = Column(Integer, nullable=True)

