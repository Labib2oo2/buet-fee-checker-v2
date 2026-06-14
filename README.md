# BUET Fee Due Checker v2 🔔
Multi-user version — anyone can register via Telegram and get fee alerts.

## How It Works
1. Users message your Telegram bot with `/register <student_id> <phone>`
2. Their info is saved in a Google Sheet
3. GitHub Actions checks all registered users every 12 hours
4. Each user gets a Telegram alert if any fee is due
5. Users can `/stop` and `/resume` anytime

---

## Setup Guide

### Step 1 — Google Sheet
1. Go to [sheets.google.com](https://sheets.google.com) → create a new sheet
2. Name the first tab exactly: `users`
3. Copy the Sheet ID from the URL:
   `https://docs.google.com/spreadsheets/d/THIS_IS_THE_ID/edit`

### Step 2 — Google Service Account
1. Go to [console.cloud.google.com](https://console.cloud.google.com)
2. Create a new project (or use existing)
3. Enable **Google Sheets API**:
   - Search "Google Sheets API" → Enable
4. Create a Service Account:
   - Go to IAM & Admin → Service Accounts → Create
   - Name it anything → click Create
   - Skip optional steps → Done
5. Create a key:
   - Click your service account → Keys tab → Add Key → JSON
   - Download the JSON file
6. Share your Google Sheet with the service account email:
   - Open the JSON file, find `client_email` (looks like `xxx@xxx.iam.gserviceaccount.com`)
   - Open your Google Sheet → Share → paste that email → Editor access

### Step 3 — GitHub Repository
1. Create a new **private** GitHub repo
2. Upload all files (keep folder structure with `.github/workflows/`)

### Step 4 — GitHub Secrets
Go to repo → Settings → Secrets → Actions → add these:

| Secret | Value |
|--------|-------|
| `TELEGRAM_BOT_TOKEN` | Your bot token from @BotFather |
| `GOOGLE_SHEET_ID` | The Sheet ID from Step 1 |
| `GOOGLE_CREDS_JSON` | The entire content of the downloaded JSON file |

### Step 5 — Run the Bot Locally (for registration to work)
The bot needs to be running to accept user commands.
Run it on your PC while you test, or deploy to Railway/Render for free 24/7.

```bash
pip install -r requirements.txt
set TELEGRAM_BOT_TOKEN=your_token
set GOOGLE_SHEET_ID=your_sheet_id
set GOOGLE_CREDS_JSON={"type":"service_account",...}   # contents of JSON file
python bot.py
```

### Step 6 — Test
1. Message your bot: `/register 2204054 01521765597`
2. Check your Google Sheet — a row should appear
3. Run the GitHub Actions workflow manually
4. You should get a Telegram message if any fee is due

---

## Bot Commands
| Command | Description |
|---------|-------------|
| `/register <id> <phone>` | Register for fee alerts |
| `/stop` | Pause notifications |
| `/resume` | Resume notifications |
| `/status` | Check your registration |
| `/help` | Show help |

## Fees Monitored
RF (Registration), HF (Hall), DF (Dining), CF (Certificate), JF (Job Application), AD (Admission)
Transport Fee is excluded.

## Hosting the Bot (Free, 24/7)
For the bot to always accept registrations, deploy `bot.py` to:
- **Railway** (railway.app) — free tier, easy deploy
- **Render** (render.com) — free tier
- Just set the 3 environment variables and point start command to `python bot.py`
