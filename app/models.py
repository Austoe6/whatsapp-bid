from datetime import datetime
from typing import Optional
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float, Text
from sqlalchemy.orm import relationship
from .db import Base


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    phone = Column(String(32), unique=True, index=True, nullable=False)
    role = Column(String(16), nullable=False, default="buyer")  # buyer | seller
    region = Column(String(64), nullable=True)
    status = Column(String(16), nullable=False, default="active")
    created_at = Column(DateTime, default=datetime.utcnow)

    opt_ins = relationship("OptIn", back_populates="user", cascade="all, delete-orphan")
    listings = relationship("Listing", back_populates="seller", cascade="all, delete-orphan")
    bids = relationship("Bid", back_populates="buyer", cascade="all, delete-orphan")


class OptIn(Base):
    __tablename__ = "opt_ins"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    commodity = Column(String(64), nullable=False)
    region = Column(String(64), nullable=False)
    active = Column(Integer, nullable=False, default=1)  # 1 true, 0 false
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="opt_ins")


class Listing(Base):
    __tablename__ = "listings"
    id = Column(Integer, primary_key=True, index=True)
    seller_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    commodity = Column(String(64), nullable=False)
    quantity = Column(Float, nullable=False)
    unit = Column(String(32), nullable=False)
    quality = Column(String(64), nullable=True)
    location = Column(String(128), nullable=False)
    min_price = Column(Float, nullable=True)
    deadline = Column(DateTime, nullable=True)
    status = Column(String(16), nullable=False, default="open")  # open | closed
    created_at = Column(DateTime, default=datetime.utcnow)

    seller = relationship("User", back_populates="listings")
    bids = relationship("Bid", back_populates="listing", cascade="all, delete-orphan")


class Bid(Base):
    __tablename__ = "bids"
    id = Column(Integer, primary_key=True, index=True)
    listing_id = Column(Integer, ForeignKey("listings.id"), nullable=False)
    buyer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    price_per_unit = Column(Float, nullable=False)
    quantity = Column(Float, nullable=False)
    note = Column(Text, nullable=True)
    status = Column(String(16), nullable=False, default="placed")  # placed | accepted | rejected
    created_at = Column(DateTime, default=datetime.utcnow)

    listing = relationship("Listing", back_populates="bids")
    buyer = relationship("User", back_populates="bids")


class SessionState(Base):
    __tablename__ = "session_states"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)
    flow = Column(String(32), nullable=True)  # e.g., 'list'
    step = Column(Integer, nullable=True)
    data_json = Column(Text, nullable=True)  # JSON-encoded state data
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)