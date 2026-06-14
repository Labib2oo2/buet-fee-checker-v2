#!/usr/bin/env python3
"""
BUET Fee Checker Bot
Handles user registration via Telegram commands.
Run this locally or on a free server (Railway, Render) to keep it alive.

Commands:
  /register <student_id> <phone>  — Register for fee alerts
  /stop                           — Pause notifications
  /resume                         — Resume notifications
  /status                         — Check your registration status
  /help                           — Show help
"""

import os, logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from sheets import (
    get_user, register_user, set_user_active, get_all_users
)

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")

logging.basicConfig(level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)


# ── /start ─────────────────────────────────────────────────────────────────────
async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
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


# ── /help ──────────────────────────────────────────────────────────────────────
async def cmd_help(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await cmd_start(update, ctx)


# ── /register ──────────────────────────────────────────────────────────────────
async def cmd_register(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    args    = ctx.args

    if len(args) != 2:
        await update.message.reply_text(
            "❌ Wrong format. Use:\n/register <student_id> <phone_number>\n\n"
            "Example: /register 2204054 01521765597"
        )
        return

    student_id, phone = args[0].strip(), args[1].strip()

    if not student_id.isdigit():
        await update.message.reply_text("❌ Student ID should be numbers only.")
        return
    if not phone.isdigit() or len(phone) < 10:
        await update.message.reply_text("❌ Invalid phone number.")
        return

    existing = get_user(chat_id)
    if existing:
        # Update existing registration
        register_user(chat_id, student_id, phone)
        await update.message.reply_text(
            f"✅ Registration updated!\n\n"
            f"🆔 Student ID: {student_id}\n"
            f"📱 Phone: {phone}\n\n"
            f"I'll check your fees every 12 hours and notify you of any dues."
        )
    else:
        register_user(chat_id, student_id, phone)
        await update.message.reply_text(
            f"✅ You're registered!\n\n"
            f"🆔 Student ID: {student_id}\n"
            f"📱 Phone: {phone}\n\n"
            f"I'll check your fees every 12 hours and notify you of any dues.\n"
            f"Use /stop anytime to pause notifications."
        )


# ── /stop ──────────────────────────────────────────────────────────────────────
async def cmd_stop(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    user = get_user(chat_id)
    if not user:
        await update.message.reply_text(
            "⚠️ You're not registered yet. Use /register first."
        )
        return
    set_user_active(chat_id, False)
    await update.message.reply_text(
        "🔕 Notifications paused.\n"
        "Use /resume to turn them back on anytime."
    )


# ── /resume ────────────────────────────────────────────────────────────────────
async def cmd_resume(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    user = get_user(chat_id)
    if not user:
        await update.message.reply_text(
            "⚠️ You're not registered yet. Use /register first."
        )
        return
    set_user_active(chat_id, True)
    await update.message.reply_text(
        "🔔 Notifications resumed!\n"
        "I'll notify you next time a fee is due."
    )


# ── /status ────────────────────────────────────────────────────────────────────
async def cmd_status(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    user = get_user(chat_id)
    if not user:
        await update.message.reply_text(
            "⚠️ You're not registered.\nUse /register <student_id> <phone> to sign up."
        )
        return
    status_icon = "🔔 Active" if user["active"] == "TRUE" else "🔕 Paused"
    await update.message.reply_text(
        f"📋 Your Registration:\n\n"
        f"🆔 Student ID: {user['student_id']}\n"
        f"📱 Phone: {user['phone']}\n"
        f"Status: {status_icon}\n\n"
        f"Fees monitored: RF, HF, DF, CF, JF, AD\n"
        f"Check frequency: every 12 hours"
    )


# ── Main ───────────────────────────────────────────────────────────────────────
def main():
    if not BOT_TOKEN:
        raise ValueError("TELEGRAM_BOT_TOKEN not set!")

    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start",    cmd_start))
    app.add_handler(CommandHandler("help",     cmd_help))
    app.add_handler(CommandHandler("register", cmd_register))
    app.add_handler(CommandHandler("stop",     cmd_stop))
    app.add_handler(CommandHandler("resume",   cmd_resume))
    app.add_handler(CommandHandler("status",   cmd_status))

    log.info("Bot is running...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
