import json
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from .. import crud
from ..models import Listing, Bid, User
from .. import whatsapp as wa


HELP_TEXT = (
    "Commands:\n"
    "- HELP\n"
    "- JOIN buyer | JOIN seller\n"
    "- SUBSCRIBE <commodity> <region>\n"
    "- LISTINGS (see open listings)\n"
    "- LIST (seller listing flow)\n"
    "- BID <listingId> <pricePerUnit> <quantity>\n"
    "- ACCEPT <bidId> (seller)\n"
)


def handle_text_message(db: Session, from_phone: str, text: str) -> None:
    user = crud.get_or_create_user(db, phone=from_phone)
    msg = (text or "").strip()

    if msg.upper().startswith("HELP") or msg == "?":
        wa.send_text(from_phone, HELP_TEXT)
        return

    if msg.upper().startswith("LISTINGS"):
        # Show ALL relevant open listings based on user's opt-ins; fallback to all open listings
        listings = crud.list_open_listings_for_user(db, user_id=user.id, limit=None)
        if not listings:
            listings = crud.list_open_listings(db)
        if not listings:
            wa.send_text(from_phone, "No open listings right now.")
            return
        # Chunk results to avoid overly long WhatsApp messages
        header = f"Open listings ({len(listings)}):"
        chunk_size = 15
        lines_chunk: list[str] = []
        for idx, lst in enumerate(listings, start=1):
            minp = "N/A" if lst.min_price is None else f"{lst.min_price}"
            lines_chunk.append(f"- ID {lst.id}: {lst.commodity} {lst.quantity} {lst.unit} @ {lst.location} | Min: {minp}")
            if len(lines_chunk) >= chunk_size:
                wa.send_text(from_phone, header + "\n" + "\n".join(lines_chunk))
                lines_chunk = []
        if lines_chunk:
            wa.send_text(from_phone, header + "\n" + "\n".join(lines_chunk))
        wa.send_text(from_phone, "To bid: BID <listingId> <pricePerUnit> <quantity>")
        return

    if msg.upper().startswith("JOIN"):
        parts = msg.split()
        if len(parts) >= 2 and parts[1].lower() in ("buyer", "seller"):
            crud.set_user_role(db, user, parts[1].lower())
            wa.send_text(from_phone, f"You are registered as {parts[1].lower()}. Send HELP for commands.")
        else:
            wa.send_text(from_phone, "Usage: JOIN buyer | JOIN seller")
        return

    if msg.upper().startswith("SUBSCRIBE"):
        parts = msg.split()
        if len(parts) >= 3:
            commodity = parts[1]
            region = " ".join(parts[2:])
            crud.add_opt_in(db, user.id, commodity=commodity, region=region)
            wa.send_text(from_phone, f"Subscribed to {commodity.upper()} in {region.upper()}.")
        else:
            wa.send_text(from_phone, "Usage: SUBSCRIBE <commodity> <region>")
        return

    if msg.upper().startswith("LIST"):
        # start seller flow
        if user.role != "seller":
            wa.send_text(from_phone, "Only sellers can list. Send 'JOIN seller' to switch.")
            return
        data = {"commodity": None, "quantity": None, "unit": None, "location": None, "quality": None, "min_price": None, "deadline_hours": None}
        crud.set_session_state(db, user_id=user.id, flow="list", step=0, data_json=json.dumps(data))
        wa.send_text(from_phone, "Listing flow started.\n1) Commodity? (e.g., MAIZE)")
        return

    # Check if in listing flow
    state = crud.get_session_state(db, user_id=user.id)
    if state and state.flow == "list":
        data = json.loads(state.data_json or "{}")
        step = state.step or 0

        if step == 0:
            data["commodity"] = msg.strip().upper()
            crud.set_session_state(db, user_id=user.id, flow="list", step=1, data_json=json.dumps(data))
            wa.send_text(from_phone, "2) Quantity? (number)")
            return

        if step == 1:
            try:
                data["quantity"] = float(msg.strip())
            except ValueError:
                wa.send_text(from_phone, "Please enter a number for quantity.")
                return
            crud.set_session_state(db, user_id=user.id, flow="list", step=2, data_json=json.dumps(data))
            wa.send_text(from_phone, "3) Unit? (e.g., KG, TON, CRATE)")
            return

        if step == 2:
            data["unit"] = msg.strip().upper()
            crud.set_session_state(db, user_id=user.id, flow="list", step=3, data_json=json.dumps(data))
            wa.send_text(from_phone, "4) Location/Region? (e.g., NAIROBI)")
            return

        if step == 3:
            data["location"] = msg.strip().upper()
            crud.set_session_state(db, user_id=user.id, flow="list", step=4, data_json=json.dumps(data))
            wa.send_text(from_phone, "5) Quality grade? (or type 'skip')")
            return

        if step == 4:
            data["quality"] = None if msg.lower() == "skip" else msg.strip()
            crud.set_session_state(db, user_id=user.id, flow="list", step=5, data_json=json.dumps(data))
            wa.send_text(from_phone, "6) Minimum price per unit? (number or 'skip')")
            return

        if step == 5:
            if msg.lower() == "skip":
                data["min_price"] = None
            else:
                try:
                    data["min_price"] = float(msg.strip())
                except ValueError:
                    wa.send_text(from_phone, "Please enter a number or 'skip'.")
                    return
            crud.set_session_state(db, user_id=user.id, flow="list", step=6, data_json=json.dumps(data))
            wa.send_text(from_phone, "7) Bidding deadline in hours from now? (number, or 'skip')")
            return

        if step == 6:
            deadline = None
            if msg.lower() != "skip":
                try:
                    hours = float(msg.strip())
                    deadline = datetime.utcnow() + timedelta(hours=hours)
                except ValueError:
                    wa.send_text(from_phone, "Please enter a number or 'skip'.")
                    return

            listing = crud.create_listing(
                db,
                seller_id=user.id,
                commodity=data["commodity"],
                quantity=data["quantity"],
                unit=data["unit"],
                location=data["location"],
                quality=data.get("quality"),
                min_price=data.get("min_price"),
                deadline=deadline,
            )

            # clear state
            crud.set_session_state(db, user_id=user.id, flow=None, step=None, data_json=None)

            wa.send_text(
                from_phone,
                f"Listing created (ID {listing.id}): {listing.commodity} {listing.quantity} {listing.unit} at {listing.location}. "
                f"Min price: {listing.min_price if listing.min_price is not None else 'N/A'}."
            )

            # Broadcast announcement to opted-in buyers
            buyers = crud.get_opted_in_buyers_for_listing(db, listing)
            body = (
                f"New listing #{listing.id}: {listing.commodity} {listing.quantity} {listing.unit} at {listing.location}.\n"
                f"To bid: BID {listing.id} <pricePerUnit> <quantity>"
            )
            if buyers:
                wa.broadcast_text([b.phone for b in buyers if b.phone != from_phone], body)
            else:
                # Fallback: broadcast to all active buyers
                all_buyers = crud.get_all_buyers(db)
                if all_buyers:
                    wa.broadcast_text([b.phone for b in all_buyers if b.phone != from_phone], body)
                else:
                    wa.send_text(from_phone, "No buyers registered yet.")
            return

    # Bidding
    if msg.upper().startswith("BID"):
        parts = msg.split()
        if len(parts) >= 4:
            try:
                listing_id = int(parts[1])
                price = float(parts[2])
                qty = float(parts[3])
            except ValueError:
                wa.send_text(from_phone, "Usage: BID <listingId> <pricePerUnit> <quantity>")
                return
            listing = crud.get_listing(db, listing_id)
            if not listing or listing.status != "open":
                wa.send_text(from_phone, "Listing not found or closed.")
                return
            bid = crud.create_bid(db, listing_id=listing_id, buyer_id=user.id, price_per_unit=price, quantity=qty, note=None)
            wa.send_text(from_phone, f"Bid placed. ID {bid.id}.")
            # Notify seller about new bid
            seller = crud.get_user_by_id(db, listing.seller_id)
            if seller and seller.phone:
                wa.send_text(
                    seller.phone,
                    f"New bid #{bid.id} on your listing {listing.id}: {price} per {listing.unit}, qty {qty} from {from_phone}.\n"
                    f"To accept: ACCEPT {bid.id}"
                )
        else:
            wa.send_text(from_phone, "Usage: BID <listingId> <pricePerUnit> <quantity>")
        return

    # Seller accepts a bid
    if msg.upper().startswith("ACCEPT"):
        if user.role != "seller":
            wa.send_text(from_phone, "Only sellers can accept bids.")
            return
        parts = msg.split()
        if len(parts) >= 2:
            try:
                bid_id = int(parts[1])
            except ValueError:
                wa.send_text(from_phone, "Usage: ACCEPT <bidId>")
                return
            bid = crud.get_bid(db, bid_id)
            if not bid:
                wa.send_text(from_phone, "Bid not found.")
                return
            listing = bid.listing
            if listing.seller_id != user.id:
                wa.send_text(from_phone, "You can only accept bids on your listings.")
                return
            crud.set_bid_status(db, bid, "accepted")
            # mark others rejected
            for other in listing.bids:
                if other.id != bid.id and other.status == "placed":
                    crud.set_bid_status(db, other, "rejected")
            crud.close_listing(db, listing)
            wa.send_text(from_phone, f"Accepted bid {bid.id} for listing {listing.id}. Listing closed.")
            # notify buyer
            wa.send_text(bid.buyer.phone, f"Your bid {bid.id} for listing {listing.id} was accepted. Seller will contact you.")
        else:
            wa.send_text(from_phone, "Usage: ACCEPT <bidId>")
        return

    # Default response
    wa.send_text(from_phone, "Unrecognized command. Send HELP for available commands.")