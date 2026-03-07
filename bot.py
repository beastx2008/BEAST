import os
import logging
from telegram import Update, ChatPermissions
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv
import datetime
import requests

load_dotenv()
TOKEN = os.getenv("TOKEN")  # Your bot token from .env
PORT = int(os.getenv("PORT", 8443))
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # e.g., https://yourproject.up.railway.app

# ------------------------
# CONFIG
# ------------------------
ADMIN_ID = 6608532248
banned_words = ["badword1", "badword2"]  # Add banned words here
user_command_access = {}  # {user_id: ["/W", "/R", "/ST"]}

# ------------------------
# LOGGING
# ------------------------
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# ------------------------
# ADMIN COMMANDS
# ------------------------
async def give_access(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ Only admin can give access")
        return
    if len(context.args) < 2:
        await update.message.reply_text("/give_access <command> @username")
        return
    cmd = context.args[0]
    user = update.message.entities[1].user  # mention entity
    if user.id not in user_command_access:
        user_command_access[user.id] = []
    user_command_access[user.id].append(cmd)
    await update.message.reply_text(f"✅ {user.first_name} now has access to {cmd}")

async def revoke_access(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ Only admin can revoke access")
        return
    if len(context.args) < 2:
        await update.message.reply_text("/revoke_access <command> @username")
        return
    cmd = context.args[0]
    user = update.message.entities[1].user
    if user.id in user_command_access and cmd in user_command_access[user.id]:
        user_command_access[user.id].remove(cmd)
        await update.message.reply_text(f"✅ {cmd} revoked from {user.first_name}")

# ------------------------
# MENTION RESPONSE
# ------------------------
async def mention_response(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if f"@{context.bot.username}" in update.message.text:
        await update.message.reply_text("yo nigga what you need")

# ------------------------
# MUTE SPAM / BANNED WORDS
# ------------------------
async def check_banned(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.lower()
    if any(word in text for word in banned_words):
        try:
            until = datetime.datetime.now() + datetime.timedelta(hours=5)
            await context.bot.restrict_chat_member(
                chat_id=update.effective_chat.id,
                user_id=update.effective_user.id,
                permissions=ChatPermissions(can_send_messages=False),
                until_date=until,
            )
            await update.message.reply_text(
                f"⚠️ {update.effective_user.first_name} muted for 5 hours (banned word)"
            )
        except Exception as e:
            await update.message.reply_text(f"❌ Could not mute: {e}")

# ------------------------
# RUN SCRIPT COMMANDS
# ------------------------
def run_github_script(url, extra_args=None):
    """Fetch script from GitHub and execute it safely"""
    try:
        res = requests.get(url, timeout=30)
        if res.status_code != 200:
            return f"❌ Failed to fetch script: {res.status_code}"
        code = res.text
        local_vars = {"extra_args": extra_args}
        exec(code, {}, local_vars)
        return f"✅ Script executed"
    except Exception as e:
        return f"❌ Script error: {e}"

async def cmd_R(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != ADMIN_ID and "/R" not in user_command_access.get(user_id, []):
        await update.message.reply_text("❌ You do not have access to /R")
        return
    msg = run_github_script("https://raw.githubusercontent.com/beastx2008/BEAST/main/r.py")
    await update.message.reply_text(msg)

async def cmd_W(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != ADMIN_ID and "/W" not in user_command_access.get(user_id, []):
        await update.message.reply_text("❌ You do not have access to /W")
        return
    msg = run_github_script("https://raw.githubusercontent.com/beastx2008/BEAST/main/w.py")
    await update.message.reply_text(msg)

async def cmd_ST(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != ADMIN_ID and "/ST" not in user_command_access.get(user_id, []):
        await update.message.reply_text("❌ You do not have access to /ST")
        return
    if len(context.args) < 3:
        await update.message.reply_text("/ST <war_id> <country1> <country2>")
        return
    war_id = context.args[0]
    countries = context.args[1:3]
    extra_args = {"war_id": war_id, "countries": countries}
    msg = run_github_script("https://raw.githubusercontent.com/beastx2008/BEAST/main/st.py", extra_args)
    await update.message.reply_text(msg)

# ------------------------
# MAIN
# ------------------------
app = ApplicationBuilder().token(TOKEN).build()

# Admin dynamic access
app.add_handler(CommandHandler("give_access", give_access))
app.add_handler(CommandHandler("revoke_access", revoke_access))

# Core bot commands
app.add_handler(CommandHandler("R", cmd_R))
app.add_handler(CommandHandler("W", cmd_W))
app.add_handler(CommandHandler("ST", cmd_ST))

# Mention and banned words
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, mention_response))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, check_banned))

# ------------------------
# START WEBHOOK
# ------------------------
app.run_webhook(
    listen="0.0.0.0",
    port=PORT,
    webhook_url=WEBHOOK_URL,
)