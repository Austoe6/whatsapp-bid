from __future__ import annotations
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import select
from . import models


def get_or_create_user(db: Session, phone: str, default_role: str = "buyer") -> models.User:
    stmt = select(models.User).where(models.User.phone == phone)
    user = db.execute(stmt).scalar_one_or_none()
    if user:
        return user
    user = models.User(phone=phone, role=default_role)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def set_user_role(db: Session, user: models.User, role: str) -> models.User:
    user.role = role
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def add_opt_in(db: Session, user_id: int, commodity: str, region: str) -> models.OptIn:
    opt_in = models.OptIn(user_id=user_id, commodity=commodity.upper(), region=region.upper(), active=1)
    db.add(opt_in)
    db.commit()
    db.refresh(opt_in)
    return opt_in


def get_session_state(db: Session, user_id: int) -> Optional[models.SessionState]:
    stmt = select(models.SessionState).where(models.SessionState.user_id == user_id)
    return db.execute(stmt).scalar_one_or_none()


def set_session_state(db: Session, user_id: int, flow: Optional[str], step: Optional[int], data_json: Optional[str]) -> models.SessionState:
    state = get_session_state(db, user_id)
    if state is None:
        state = models.SessionState(user_id=user_id, flow=flow, step=step, data_json=data_json)
        db.add(state)
    else:
        state.flow = flow
        state.step = step
        state.data_json = data_json
        db.add(state)
    db.commit()
    db.refresh(state)
    return state


def create_listing(
    db: Session,
    seller_id: int,
    commodity: str,
    quantity: float,
    unit: str,
    location: str,
    quality: Optional[str] = None,
    min_price: Optional[float] = None,
    deadline=None,
) -> models.Listing:
    listing = models.Listing(
        seller_id=seller_id,
        commodity=commodity.upper(),
        quantity=quantity,
        unit=unit,
        location=location,
        quality=quality,
        min_price=min_price,
        deadline=deadline,
        status="open",
    )
    db.add(listing)
    db.commit()
    db.refresh(listing)
    return listing


def get_listing(db: Session, listing_id: int) -> Optional[models.Listing]:
    stmt = select(models.Listing).where(models.Listing.id == listing_id)
    return db.execute(stmt).scalar_one_or_none()


def list_open_listings(db: Session) -> List[models.Listing]:
    stmt = select(models.Listing).where(models.Listing.status == "open").order_by(models.Listing.created_at.desc())
    return db.execute(stmt).scalars().all()


def close_listing(db: Session, listing: models.Listing) -> models.Listing:
    listing.status = "closed"
    db.add(listing)
    db.commit()
    db.refresh(listing)
    return listing


def create_bid(db: Session, listing_id: int, buyer_id: int, price_per_unit: float, quantity: float, note: Optional[str]) -> models.Bid:
    bid = models.Bid(
        listing_id=listing_id,
        buyer_id=buyer_id,
        price_per_unit=price_per_unit,
        quantity=quantity,
        note=note,
        status="placed",
    )
    db.add(bid)
    db.commit()
    db.refresh(bid)
    return bid


def get_bid(db: Session, bid_id: int) -> Optional[models.Bid]:
    stmt = select(models.Bid).where(models.Bid.id == bid_id)
    return db.execute(stmt).scalar_one_or_none()


def set_bid_status(db: Session, bid: models.Bid, status: str) -> models.Bid:
    bid.status = status
    db.add(bid)
    db.commit()
    db.refresh(bid)
    return bid


def get_opted_in_buyers_for_listing(db: Session, listing: models.Listing) -> list[models.User]:
    # buyers with matching commodity + region (use listing.location as region for MVP)
    stmt = (
        select(models.User)
        .join(models.OptIn, models.OptIn.user_id == models.User.id)
        .where(
            models.User.role == "buyer",
            models.OptIn.active == 1,
            models.OptIn.commodity == listing.commodity.upper(),
            models.OptIn.region == listing.location.upper(),
        )
    )
    return db.execute(stmt).scalars().all()
*** End Patch  المادة

