# BUET Fee Due Checker v2 🔔
Multi-user version — anyone can register via Telegram and get fee alerts.
No python-telegram-bot dependency (uses plain HTTP requests — avoids library bugs).

## How It Works
1. Users message your Telegram bot with `/register <student_id> <phone>`
2. Their info is saved in a Google Sheet
3. GitHub Actions checks all registered users every 12 hours
4. Each user gets a Telegram alert ONLY if a fee is due (silent otherwise)
5. Users can `/stop` and `/resume` anytime

---

## Setup Guide

### Step 1 — Google Sheet
1. Go to sheets.google.com → new blank sheet
2. Rename the bottom tab to exactly: `users`
3. Copy the Sheet ID from the URL:
   `https://docs.google.com/spreadsheets/d/THIS_PART/edit`

### Step 2 — Google Service Account
1. Go to console.cloud.google.com → New Project → name it anything
2. Search "Google Sheets API" → Enable
3. IAM & Admin → Service Accounts → Create Service Account → name it → Create → Done
4. Click the service account → Keys tab → Add Key → Create new key → JSON → Download

### Step 3 — Share the Sheet
1. Open the downloaded JSON in Notepad
2. Find `"client_email": "xxxx@xxxx.iam.gserviceaccount.com"`
3. Google Sheet → Share → paste that email → Editor access

### Step 4 — GitHub Repo
1. Create a new private repo
2. Upload all files keeping folder structure (`.github/workflows/` must exist)

### Step 5 — GitHub Secrets
Repo → Settings → Secrets and variables → Actions → add:

| Secret | Value |
|--------|-------|
| `TELEGRAM_BOT_TOKEN` | your bot token |
| `GOOGLE_SHEET_ID` | from Step 1 |
| `GOOGLE_CREDS_JSON` | entire content of the downloaded JSON file |

### Step 6 — Register yourself (run bot locally once)

PowerShell:
```powershell
pip install requests google-auth google-api-python-client

$env:TELEGRAM_BOT_TOKEN="your_token"
$env:GOOGLE_SHEET_ID="your_sheet_id"
$env:GOOGLE_CREDS_JSON='paste_entire_json_content_here_in_single_quotes'

python bot.py
```

You should see `Bot is running (long polling)...`. Now message your bot on Telegram:
```
/register 2204054 01521765597
```

You'll get a confirmation reply, and a new row appears in your Google Sheet.
Once confirmed, press Ctrl+C to stop the bot — it's only needed for registration.

### Step 7 — Test the checker
GitHub repo → Actions → BUET Fee Due Checker → Run workflow

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
RF, HF, DF, CF, JF, AD — Transport Fee excluded.

## Running the bot 24/7 (optional, for new registrations anytime)
Deploy `bot.py` + `sheets.py` + `requirements.txt` to Railway.app or Render.com (free tier).
Set the same 3 environment variables there, start command: `python bot.py`
