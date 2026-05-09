from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.sql import func
from database import Base

class WatchedStock(Base):
    __tablename__ = "watched_stocks"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    added_at = Column(DateTime(timezone=True), server_default=func.now())
