import logging
import requests
from telegram import Update, ChatPermissions
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)

# =========================
# CONFIG
# =========================
TOKEN = "8152750567:AAH71FPaotg7DE6py50XC3ykFK0rg31qKKI"  # <-- Put your bot token here
ADMIN_ID = 6608532248
ACCESS_LIST = {}
BANNED_WORDS = ["spamword1", "🙄"]

# GitHub raw script links
SCRIPTS = {
    "R": "https://raw.githubusercontent.com/beastx2008/BEAST/main/r.py",
    "W": "https://raw.githubusercontent.com/beastx2008/BEAST/main/w.py",
    "ST": "https://raw.githubusercontent.com/beastx2008/BEAST/main/st.py",
    "D": "https://raw.githubusercontent.com/beastx2008/BEAST/main/d.py",
    "D1":
"https://github.com/beastx2008/BEAST/blob/main/D1.py"
}

# =========================
# Logging
# =========================
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# =========================
# Helper functions
# =========================
async def run_github_script(url):
    try:
        r = requests.get(url, timeout=30)
        r.raise_for_status()
        code = r.text
        exec(code, {"__name__": "__main__"})
        return "✅ Script executed successfully."
    except Exception as e:
        return f"❌ Script failed: {e}"

def user_has_access(user_id, command):
    return user_id == ADMIN_ID or command in ACCESS_LIST.get(user_id, [])

# =========================
# Command Handlers
# =========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        await update.message.reply_text("ELITE X online. Use /help to see commands.")
    except Exception as e:
        logger.warning(f"Start command failed: {e}")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        msg = """
Available Commands:
/R - Run resolutions scanner
/W - Run war lock scanner
/ST - Track contributor speed
/mute - Mute user
/giveaccess - Grant command
/revokeaccess - Remove command
/status - Bot status
"""
        await update.message.reply_text(msg)
    except Exception as e:
        logger.warning(f"Help command failed: {e}")

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        await update.message.reply_text("Beast X Bot is running.")
    except Exception as e:
        logger.warning(f"Status command failed: {e}")

async def script_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        cmd = update.message.text.split()[0][1:].upper()
        user_id = update.message.from_user.id

        if not user_has_access(user_id, cmd):
            await update.message.reply_text("❌ You don't have access.")
            return

        if cmd not in SCRIPTS:
            await update.message.reply_text("❌ Unknown command.")
            return

        msg = await run_github_script(SCRIPTS[cmd])
        await update.message.reply_text(msg)
    except Exception as e:
        logger.warning(f"Script command failed: {e}")

# =========================
# Admin Commands
# =========================
async def mute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if update.message.from_user.id != ADMIN_ID:
            await update.message.reply_text("❌ Admin only.")
            return

        if not update.message.reply_to_message:
            await update.message.reply_text("Reply to a user to mute them.")
            return

        target = update.message.reply_to_message.from_user
        duration = 86400  # default 1 day

        if context.args:
            t = context.args[0]
            if t.endswith("m"):
                duration = int(t[:-1]) * 60
            elif t.endswith("h"):
                duration = int(t[:-1]) * 3600
            elif t.endswith("d"):
                duration = int(t[:-1]) * 86400

        await context.bot.restrict_chat_member(
            chat_id=update.effective_chat.id,
            user_id=target.id,
            permissions=ChatPermissions(can_send_messages=False),
            until_date=int(update.message.date.timestamp()) + duration
        )
        await update.message.reply_text(f"🔇 {target.full_name} muted.")
    except Exception as e:
        logger.warning(f"Mute failed: {e}")

async def giveaccess(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if update.message.from_user.id != ADMIN_ID:
            return

        if not update.message.reply_to_message or not context.args:
            await update.message.reply_text("Usage: reply + /giveaccess COMMAND")
            return

        cmd = context.args[0].upper()
        target = update.message.reply_to_message.from_user
        ACCESS_LIST.setdefault(target.id, []).append(cmd)
        await update.message.reply_text(f"✅ {target.full_name} granted {cmd}")
    except Exception as e:
        logger.warning(f"GiveAccess failed: {e}")

async def revokeaccess(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if update.message.from_user.id != ADMIN_ID:
            return

        if not update.message.reply_to_message or not context.args:
            await update.message.reply_text("Usage: reply + /revokeaccess COMMAND")
            return

        cmd = context.args[0].upper()
        target = update.message.reply_to_message.from_user

        if target.id in ACCESS_LIST and cmd in ACCESS_LIST[target.id]:
            ACCESS_LIST[target.id].remove(cmd)

        await update.message.reply_text(f"❌ {cmd} removed from {target.full_name}")
    except Exception as e:
        logger.warning(f"RevokeAccess failed: {e}")

# =========================
# Message Handlers
# =========================
async def mention_response(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if not update.message or not update.message.text:
            return
        if "beast_x_bot" in update.message.text.lower():
            await update.message.reply_text("Yes? What do you need?")
    except Exception as e:
        logger.warning(f"Mention response failed: {e}")

async def spam_filter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if not update.message or not update.message.text:
            return
        text = update.message.text.lower()
        if any(word in text for word in BANNED_WORDS):
            await update.message.delete()
            await update.message.reply_text("⚠️ Banned word detected.")
    except Exception as e:
        logger.warning(f"Spam filter failed: {e}")

# =========================
# Main
# =========================
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    # Command handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler(["R", "W", "ST", "D"], script_command))
    app.add_handler(CommandHandler("mute", mute))
    app.add_handler(CommandHandler("giveaccess", giveaccess))
    app.add_handler(CommandHandler("revokeaccess", revokeaccess))

    # Message handlers
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, mention_response))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, spam_filter))

    app.run_polling()

if __name__ == "__main__":
    main()