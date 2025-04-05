from datetime import datetime

from .base import Base
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey


class Task(Base):
    __tablename__ = 'task'

    id = Column(Integer, primary_key=True)
    title = Column(String(200), nullable=False)
    room = Column(String(100), nullable=False)
    points = Column(Integer, default=1)
    completed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    family_member_id = Column(Integer, ForeignKey('family_member.id'))
    cost = Column(Integer, default=0)
