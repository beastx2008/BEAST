import os
import logging
import asyncio
import requests
from dotenv import load_dotenv
from telegram import Update, ChatPermissions
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes,
    filters
)

# =========================
# Load environment
# =========================
load_dotenv()
TOKEN = os.getenv("TOKEN")
ADMIN_ID = 6608532248  # Your admin Telegram ID
ACCESS_LIST = {}  # user_id: list of allowed commands
BANNED_WORDS = ["🙄", "🙄"]  # add banned words here

# GitHub script links
SCRIPTS = {
    "R": "https://raw.githubusercontent.com/beastx2008/BEAST/main/r.py",
    "W": "https://raw.githubusercontent.com/beastx2008/BEAST/main/w.py",
    "ST": "https://raw.githubusercontent.com/beastx2008/BEAST/main/st.py"
}

# =========================
# Logging
# =========================
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# =========================
# Helper functions
# =========================
async def run_github_script(url):
    """Fetch and execute a GitHub script dynamically."""
    try:
        r = requests.get(url, timeout=30)
        r.raise_for_status()
        code = r.text
        exec(code, {"__name__": "__main__"})
        return "✅ Script executed successfully."
    except Exception as e:
        return f"❌ Failed to execute script: {e}"

def user_has_access(user_id, command):
    """Check if a user can run a command."""
    return user_id == ADMIN_ID or command in ACCESS_LIST.get(user_id, [])

# =========================
# Command Handlers
# =========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Beast X Bot online. Use /help to see commands.")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = """Available Commands:
/R - Run resolutions scanner
/W - Run war lock scanner
/ST <war_id> <country1> <country2> - Track contributor speed
/mute <@user> [time] - Mute user (default 1 day)
/ban <@user> - Ban user
/unban <@user> - Unban user
/giveaccess <command> <@user> - Grant command access
/revokeaccess <command> <@user> - Revoke command access
/status - Show bot status
"""
    await update.message.reply_text(msg)

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Beast X Bot is online and monitoring the group.")

# =========================
# Script commands (/R, /W, /ST)
# =========================
async def script_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cmd = update.message.text.strip().split()[0][1:].upper()  # /R -> R
    user_id = update.message.from_user.id

    if not user_has_access(user_id, cmd):
        await update.message.reply_text("❌ You don't have access to this command.")
        return

    if cmd not in SCRIPTS:
        await update.message.reply_text("❌ Unknown script command.")
        return

    msg = await run_github_script(SCRIPTS[cmd])
    await update.message.reply_text(msg)

# =========================
# Admin commands
# =========================
async def mute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if user_id != ADMIN_ID:
        await update.message.reply_text("❌ Only the admin can mute.")
        return

    if not context.args:
        await update.message.reply_text("Usage: /mute @username [time]")
        return

    target = update.message.reply_to_message.from_user if update.message.reply_to_message else None
    if not target:
        await update.message.reply_text("❌ Reply to a user to mute them.")
        return

    duration = 86400  # default 1 day in seconds
    if len(context.args) > 1:
        try:
            t = context.args[1].lower()
            if t.endswith("m"): duration = int(t[:-1]) * 60
            elif t.endswith("h"): duration = int(t[:-1]) * 3600
            elif t.endswith("d"): duration = int(t[:-1]) * 86400
        except:
            pass

    await context.bot.restrict_chat_member(
        chat_id=update.effective_chat.id,
        user_id=target.id,
        permissions=ChatPermissions(can_send_messages=False),
        until_date=int(update.message.date.timestamp()) + duration
    )
    await update.message.reply_text(f"✅ {target.full_name} muted for {duration//3600}h.")

async def giveaccess(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if user_id != ADMIN_ID:
        await update.message.reply_text("❌ Only the admin can give access.")
        return
    if len(context.args) < 2:
        await update.message.reply_text("Usage: /giveaccess <command> <@user>")
        return
    cmd = context.args[0].upper()
    target = update.message.entities[1].user
    ACCESS_LIST.setdefault(target.id, []).append(cmd)
    await update.message.reply_text(f"✅ {target.full_name} granted access to {cmd}")

async def revokeaccess(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if user_id != ADMIN_ID:
        await update.message.reply_text("❌ Only the admin can revoke access.")
        return
    if len(context.args) < 2:
        await update.message.reply_text("Usage: /revokeaccess <command> <@user>")
        return
    cmd = context.args[0].upper()
    target = update.message.entities[1].user
    if target.id in ACCESS_LIST and cmd in ACCESS_LIST[target.id]:
        ACCESS_LIST[target.id].remove(cmd)
    await update.message.reply_text(f"✅ {target.full_name} access to {cmd} revoked")

# =========================
# Respond to mentions
# =========================
async def mention_response(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.lower()
    if "beast_x_bot" in text:
        await update.message.reply_text("yo nigga what you need")

# =========================
# Spam filter
# =========================
async def spam_filter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.lower()
    if any(word in text for word in BANNED_WORDS):
        await update.message.delete()
        await update.message.reply_text(f"⚠️ {update.message.from_user.full_name}, banned word detected!")

# =========================
# Main
# =========================
async def main():
    app = ApplicationBuilder().token(TOKEN).build()

    # Core commands
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler(["R","W","ST"], script_command))

    # Admin commands
    app.add_handler(CommandHandler("mute", mute))
    app.add_handler(CommandHandler("giveaccess", giveaccess))
    app.add_handler(CommandHandler("revokeaccess", revokeaccess))

    # Messages
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, mention_response))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, spam_filter))

    await app.start()
    await app.updater.start_polling()
    await app.idle()

if __name__ == "__main__":
    asyncio.run(main())