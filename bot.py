import os
from dotenv import load_dotenv
from telegram import Update, ChatPermissions
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

# =========================
# Commands
# =========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hello! I am your admin bot 🤖.")

# Welcome new members
async def welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    for member in update.message.new_chat_members:
        await update.message.reply_text(f"Welcome {member.full_name} to the group!")

# Kick a member
async def kick(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /kick <user_id>")
        return
    user_id = int(context.args[0])
    await update.effective_chat.kick_member(user_id)
    await update.message.reply_text(f"User {user_id} has been kicked.")

# Ban a member
async def ban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /ban <user_id>")
        return
    user_id = int(context.args[0])
    await update.effective_chat.kick_member(user_id)
    await update.message.reply_text(f"User {user_id} has been banned permanently.")

# Mute a member
async def mute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /mute <user_id>")
        return
    user_id = int(context.args[0])
    await update.effective_chat.restrict_member(
        user_id, permissions=ChatPermissions(can_send_messages=False)
    )
    await update.message.reply_text(f"User {user_id} has been muted.")

# Unmute
async def unmute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /unmute <user_id>")
        return
    user_id = int(context.args[0])
    await update.effective_chat.restrict_member(
        user_id, permissions=ChatPermissions(can_send_messages=True)
    )
    await update.message.reply_text(f"User {user_id} has been unmuted.")

# List members (simplified)
async def members(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    member_count = await chat.get_member_count()
    await update.message.reply_text(f"This group has {member_count} members.")

# =========================
# Main
# =========================
if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome))
    app.add_handler(CommandHandler("kick", kick))
    app.add_handler(CommandHandler("ban", ban))
    app.add_handler(CommandHandler("mute", mute))
    app.add_handler(CommandHandler("unmute", unmute))
    app.add_handler(CommandHandler("members", members))

    print("Bot is running...")
    app.run_polling()