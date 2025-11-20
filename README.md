## WhatsApp Bid App (MVP, no payments)

This is a FastAPI backend that drives a WhatsApp-based marketplace where sellers post listings and buyers bid via WhatsApp messages. It uses the WhatsApp Cloud API webhooks for inbound messages and the Graph API to send replies/broadcasts.

### Features (MVP)
- Buyer opt-in by commodity/region (simple text commands)
- Seller creates a listing via a guided chat flow
- Broadcast listing announcements to opted-in buyers
- Buyers place bids using a structured message
- Seller accepts a bid and closes the listing

### Tech
- FastAPI
- SQLAlchemy (SQLite by default)
- httpx for WhatsApp Graph API calls

### Setup
1) Create a `.env` from `.env.example` and fill in values:
   - `WA_ACCESS_TOKEN` (WhatsApp Cloud API token)
   - `WA_PHONE_NUMBER_ID` (sender number ID)
   - `WA_VERIFY_TOKEN` (arbitrary string you set for webhook verify)
   - `APP_BASE_URL` (public URL for the webhook, e.g., Ngrok/Render)

2) Create venv and install:

```bash
cd whatsapp-bid
python -m venv .venv
.\.venv\Scripts\activate   # Windows PowerShell
pip install -r requirements.txt
```

3) Run the server:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

4) Expose your local server for webhooks (during development):

```bash
ngrok http 8000
```

5) Set WhatsApp webhook in your Meta App (replace placeholders):

```bash
curl -X POST \
  "https://graph.facebook.com/v20.0/<APP_ID>/subscriptions" \
  -H "Authorization: Bearer <SYSTEM_USER_ACCESS_TOKEN>" \
  -d "object=whatsapp_business_account" \
  -d "callback_url=<APP_BASE_URL>/webhook/whatsapp" \
  -d "fields=messages,message_template_status" \
  -d "verify_token=<WA_VERIFY_TOKEN>"
```

Alternatively, use the WhatsApp > Configuration in Meta App dashboard.

### Deploy to Vercel
This repo is prepared to run on Vercel Python Functions (serverless) with the handler at `api/webhook/whatsapp.py` exposing `/api/webhook/whatsapp`:

1) Push code to GitHub.
2) In Vercel, “New Project” → Import your repo.
3) Set “Root Directory” to `whatsapp-bid`.
4) Framework preset: Python.
5) Environment Variables (Project Settings → Environment Variables):
   - `WA_ACCESS_TOKEN`, `WA_PHONE_NUMBER_ID`, `WA_VERIFY_TOKEN`
   - `APP_BASE_URL` set to your Vercel deployment URL (e.g., `https://your-project.vercel.app`)
   - `DATABASE_URL` set to a hosted Postgres (e.g., Neon/Supabase). Do not use SQLite on Vercel.
6) After deploy, set your WhatsApp webhook callback URL to: `https://<your-project>.vercel.app/api/webhook/whatsapp` and use your `WA_VERIFY_TOKEN`.

Notes:
- Serverless functions are stateless. Use an external database (Neon/Supabase) for persistence.
- Local development still uses `uvicorn` with FastAPI (see steps above).

### WhatsApp Commands (MVP)
- HELP
- JOIN buyer        → registers you as buyer
- JOIN seller       → registers you as seller
- SUBSCRIBE <commodity> <region>
- LIST              → start seller listing flow
- BID <listingId> <pricePerUnit> <quantity>
- ACCEPT <bidId>    → seller accepts a bid and closes the listing

### Notes
- For production, use Postgres and secure the config appropriately.
- WhatsApp interactive/list templates can replace text commands later.
- Payments are intentionally omitted in this MVP.


