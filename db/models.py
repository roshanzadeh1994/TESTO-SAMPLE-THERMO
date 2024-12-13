from sqlalchemy import Column, String, Integer, ForeignKey, JSON
from sqlalchemy.orm import relationship
from db.database import Base

# Benutzer-Modell
class DbUser(Base):
    __tablename__ = "user"
    id = Column(Integer, index=True, primary_key=True)
    username = Column(String, nullable=False)
    password = Column(String, nullable=False)
    email = Column(String, nullable=False)
    items = relationship("DeviceInspection", back_populates="user")

# Inspektionsmodell
class DeviceInspection(Base):
    __tablename__ = "device_inspection"
    id = Column(Integer, primary_key=True, index=True)
    data = Column(JSON, nullable=False)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship("DbUser", back_populates="items")
