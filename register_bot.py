#!/usr/bin/env python3
"""
BUET Fee Checker — Registration Bot (single-pass version for GitHub Actions)
Checks for new Telegram messages once, processes commands, then exits.
Run on a schedule (every 5 min) via GitHub Actions — no PC or server needed.
"""

import os, logging, requests
from sheets import get_user, register_user, set_user_active, get_offset, set_offset

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
API_URL   = f"https://api.telegram.org/bot{BOT_TOKEN}"

logging.basicConfig(level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)


def send_message(chat_id, text):
    try:
        requests.post(f"{API_URL}/sendMessage", json={
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "HTML"
        }, timeout=10)
    except Exception as e:
        log.error(f"send_message failed: {e}")


HELP_TEXT = (
    "👋 Welcome to the BUET Fee Due Checker!\n\n"
    "I'll automatically check your BUET fees every 12 hours and notify you if anything is due.\n\n"
    "To get started:\n"
    "👉 /register <student_id> <phone_number>\n\n"
    "Example:\n"
    "/register 2204054 01521765597\n\n"
    "Other commands:\n"
    "/stop — Pause notifications\n"
    "/resume — Resume notifications\n"
    "/status — Check your registration\n"
    "/help — Show this message"
)


def handle_message(chat_id, text):
    text = text.strip()
    parts = text.split()
    cmd = parts[0].lower() if parts else ""

    if cmd in ("/start", "/help"):
        send_message(chat_id, HELP_TEXT)

    elif cmd == "/register":
        if len(parts) != 3:
            send_message(chat_id,
                "❌ Wrong format. Use:\n/register <student_id> <phone_number>\n\n"
                "Example: /register 2204054 01521765597")
            return
        student_id, phone = parts[1].strip(), parts[2].strip()
        if not student_id.isdigit():
            send_message(chat_id, "❌ Student ID should be numbers only.")
            return
        if not phone.isdigit() or len(phone) < 10:
            send_message(chat_id, "❌ Invalid phone number.")
            return

        register_user(str(chat_id), student_id, phone)
        send_message(chat_id,
            f"✅ You're registered!\n\n"
            f"🆔 Student ID: {student_id}\n"
            f"📱 Phone: {phone}\n\n"
            f"I'll check your fees every 12 hours and notify you of any dues.\n"
            f"Use /stop anytime to pause notifications.")

    elif cmd == "/stop":
        user = get_user(str(chat_id))
        if not user:
            send_message(chat_id, "⚠️ You're not registered yet. Use /register first.")
            return
        set_user_active(str(chat_id), False)
        send_message(chat_id, "🔕 Notifications paused.\nUse /resume to turn them back on anytime.")

    elif cmd == "/resume":
        user = get_user(str(chat_id))
        if not user:
            send_message(chat_id, "⚠️ You're not registered yet. Use /register first.")
            return
        set_user_active(str(chat_id), True)
        send_message(chat_id, "🔔 Notifications resumed!\nI'll notify you next time a fee is due.")

    elif cmd == "/status":
        user = get_user(str(chat_id))
        if not user:
            send_message(chat_id, "⚠️ You're not registered.\nUse /register <student_id> <phone> to sign up.")
            return
        status_icon = "🔔 Active" if user["active"] == "TRUE" else "🔕 Paused"
        send_message(chat_id,
            f"📋 Your Registration:\n\n"
            f"🆔 Student ID: {user['student_id']}\n"
            f"📱 Phone: {user['phone']}\n"
            f"Status: {status_icon}\n\n"
            f"Fees monitored: RF, HF, DF, CF, JF, AD\n"
            f"Check frequency: every 12 hours")

    else:
        send_message(chat_id, "Unknown command. Send /help to see what I can do.")


def main():
    if not BOT_TOKEN:
        raise ValueError("TELEGRAM_BOT_TOKEN not set!")

    offset = get_offset()
    log.info(f"Starting from offset: {offset}")

    params = {"timeout": 0}
    if offset:
        params["offset"] = offset + 1

    resp = requests.get(f"{API_URL}/getUpdates", params=params, timeout=15)
    data = resp.json()

    if not data.get("ok"):
        log.error(f"getUpdates error: {data}")
        return

    updates = data.get("result", [])
    log.info(f"Found {len(updates)} new update(s)")

    max_offset = offset
    for update in updates:
        max_offset = max(max_offset, update["update_id"])
        msg = update.get("message")
        if not msg:
            continue
        chat_id = msg["chat"]["id"]
        text    = msg.get("text", "")
        if text:
            log.info(f"Processing from {chat_id}: {text}")
            handle_message(chat_id, text)

    if max_offset != offset:
        set_offset(max_offset)
        log.info(f"Updated offset to: {max_offset}")
    else:
        log.info("No new messages.")


if __name__ == "__main__":
    main()
