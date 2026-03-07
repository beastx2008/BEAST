import os
import re
import httpx
import logging
from datetime import datetime, timedelta
from telegram import Update, ChatPermissions
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    MessageHandler,
    filters
)

BOT_TOKEN = os.getenv("8152750567:AAH71FPaotg7DE6py50XC3ykFK0rg31qKKI")
OWNER_ID = 6608532248

logging.basicConfig(level=logging.INFO)

# ===============================
# GitHub script sources
# ===============================

SCRIPTS = {
    "R": "https://raw.githubusercontent.com/beastx2008/BEAST/main/r.py",
    "W": "https://raw.githubusercontent.com/beastx2008/BEAST/main/w.py",
    "ST": "https://raw.githubusercontent.com/beastx2008/BEAST/main/st.py"
}

# command permissions
command_access = {
    "R": set(),
    "W": set(),
    "ST": set()
}

# banned words
banned_words = {"spamword1", "spamword2"}

# ===============================
# Tag response
# ===============================

async def mention_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.lower()
    bot_username = context.bot.username.lower()

    if f"@{bot_username}" in text:
        await update.message.reply_text("yo nigga what you need")

# ===============================
# Script Runner
# ===============================

async def run_script(update: Update, context: ContextTypes.DEFAULT_TYPE):

    command = update.message.text.split()[0][1:].upper()
    user_id = update.effective_user.id

    if user_id != OWNER_ID and user_id not in command_access.get(command, set()):
        await update.message.reply_text("❌ You don't have permission for this command")
        return

    url = SCRIPTS.get(command)

    try:
        async with httpx.AsyncClient() as client:
            r = await client.get(url, timeout=30)

        scope = {}
        exec(r.text, scope)

        if "run" in scope:
            await scope["run"](update, context)
        else:
            await update.message.reply_text("Script missing run() function")

    except Exception as e:
        await update.message.reply_text(f"Script error: {e}")

# ===============================
# Grant access
# ===============================

async def grant(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.effective_user.id != OWNER_ID:
        return

    if not update.message.reply_to_message:
        await update.message.reply_text("Reply to a user to grant access")
        return

    cmd = context.args[0].upper()
    user_id = update.message.reply_to_message.from_user.id

    command_access.setdefault(cmd, set()).add(user_id)

    await update.message.reply_text(f"Access granted for /{cmd}")

# ===============================
# Revoke access
# ===============================

async def revoke(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.effective_user.id != OWNER_ID:
        return

    if not update.message.reply_to_message:
        await update.message.reply_text("Reply to user")
        return

    cmd = context.args[0].upper()
    user_id = update.message.reply_to_message.from_user.id

    command_access.get(cmd, set()).discard(user_id)

    await update.message.reply_text(f"Access revoked for /{cmd}")

# ===============================
# Mute system
# ===============================

def parse_time(time_str):

    if time_str.endswith("m"):
        return timedelta(minutes=int(time_str[:-1]))

    if time_str.endswith("h"):
        return timedelta(hours=int(time_str[:-1]))

    if time_str.endswith("d"):
        return timedelta(days=int(time_str[:-1]))

    return timedelta(days=1)

async def mute(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.effective_user.id != OWNER_ID:
        return

    if not update.message.reply_to_message:
        await update.message.reply_text("Reply to user to mute")
        return

    user = update.message.reply_to_message.from_user

    duration = timedelta(days=1)

    if context.args:
        duration = parse_time(context.args[0])

    until = datetime.utcnow() + duration

    await context.bot.restrict_chat_member(
        chat_id=update.effective_chat.id,
        user_id=user.id,
        permissions=ChatPermissions(can_send_messages=False),
        until_date=until
    )

    await update.message.reply_text(f"🔇 Muted for {duration}")

# ===============================
# Spam filter
# ===============================

async def spam_filter(update: Update, context: ContextTypes.DEFAULT_TYPE):

    text = update.message.text.lower()

    for word in banned_words:
        if word in text:

            await update.message.delete()

            await update.message.reply_text(
                f"{update.effective_user.first_name} watch your language."
            )
            return

# ===============================
# Main
# ===============================

def main():

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("grant", grant))
    app.add_handler(CommandHandler("revoke", revoke))
    app.add_handler(CommandHandler("mute", mute))

    app.add_handler(MessageHandler(filters.Regex("^/(R|W|ST)"), run_script))

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, spam_filter))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, mention_reply))

    print("Bot running...")

    app.run_polling()

if __name__ == "__main__":
    main()