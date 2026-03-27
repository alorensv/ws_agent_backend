from sqlalchemy import Column, Integer, Float, String, DateTime
from app.infrastructure.db.base import Base
import datetime

class Quote(Base):
    __tablename__ = "quotes"

    id = Column(Integer, primary_key=True, index=True)
    total = Column(Float)
    client_phone = Column(String)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
