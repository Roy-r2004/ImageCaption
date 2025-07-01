from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime
from .database import Base

class ImageCaption(Base):
    __tablename__ = "captions"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), unique=True, nullable=False)
    caption = Column(String(1000), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
