# admin_bot.py
# Requires: pip install python-telegram-bot --upgrade

import logging
from datetime import datetime, timedelta
from typing import Optional

from telegram import Update, ChatPermissions, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

# ────────────────────────────────────────────────
#  CONFIGURATION
# ────────────────────────────────────────────────

TOKEN = "8152750567:AAH71FPaotg7DE6py50XC3ykFK0rg31qKKI"          # ← CHANGE THIS

# List of user IDs that are allowed to use admin commands
# You can also manage this list inside the bot later
SUDOERS = {-1003832564393}     # ← your user id(s) here

# Bot will only respond to these commands in groups/supergroups
ALLOWED_CHATS = filters.ChatType.GROUPS | filters.ChatType.SUPERGROUPS

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ────────────────────────────────────────────────
#  HELPER FUNCTIONS
# ────────────────────────────────────────────────

async def is_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Check if the user who sent the message is admin or sudoer"""
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id

    if user_id in SUDOERS:
        return True

    admins = await context.bot.get_chat_administrators(chat_id)
    return any(admin.user.id == user_id for admin in admins)


async def reply_error(update: Update, text: str):
    if update.message:
        await update.message.reply_text(f"⚠️ {text}", quote=True)


async def get_target_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Try to find who we want to ban/kick/mute/..."""
    message = update.effective_message
    if not message:
        return None, None

    # 1. Reply to message
    if message.reply_to_message and message.reply_to_message.from_user:
        return message.reply_to_message.from_user, None

    # 2. @username in command
    if context.args:
        username = context.args[0].lstrip('@')
        try:
            chat_member = await context.bot.get_chat_member(
                message.chat_id, f"@{username}"
            )
            return chat_member.user, None
        except:
            pass

    # 3. user id as argument
    if context.args and context.args[0].isdigit():
        try:
            uid = int(context.args[0])
            chat_member = await context.bot.get_chat_member(message.chat_id, uid)
            return chat_member.user, None
        except:
            pass

    return None, "Please reply to a user or provide @username / user ID"


# ────────────────────────────────────────────────
#  ADMIN COMMANDS
# ────────────────────────────────────────────────

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type in ("private",):
        await update.message.reply_text(
            "🤖 Group Admin Bot\n\nAdd me to a group and give me admin rights!"
        )


async def ban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        return

    target, error = await get_target_user(update, context)
    if error:
        await reply_error(update, error or "No user selected.")
        return
    if not target:
        return

    try:
        await context.bot.ban_chat_member(
            update.effective_chat.id,
            target.id,
            revoke_messages=True   # delete recent messages (Telegram Premium feature)
        )
        await update.message.reply_text(
            f"🚫 {target.mention_html()} banned.",
            parse_mode=ParseMode.HTML
        )
    except Exception as e:
        await reply_error(update, f"Cannot ban: {str(e)}")


async def kick(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ban + immediate unban = kick"""
    if not await is_admin(update, context):
        return

    target, error = await get_target_user(update, context)
    if error or not target:
        await reply_error(update, error or "No user selected.")
        return

    try:
        await context.bot.ban_chat_member(update.effective_chat.id, target.id)
        await context.bot.unban_chat_member(update.effective_chat.id, target.id, only_if_banned=True)
        await update.message.reply_text(
            f"👢 {target.mention_html()} kicked.",
            parse_mode=ParseMode.HTML
        )
    except Exception as e:
        await reply_error(update, f"Cannot kick: {str(e)}")


async def mute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        return

    target, error = await get_target_user(update, context)
    if error or not target:
        await reply_error(update, error or "No target user.")
        return

    until_date = None
    if context.args and len(context.args) > 1:
        try:
            minutes = int(context.args[1])
            until_date = datetime.utcnow() + timedelta(minutes=minutes)
        except ValueError:
            await reply_error(update, "Usage: /mute @user 60   (minutes)")
            return

    permissions = ChatPermissions(
        can_send_messages=False,
        can_send_media_messages=False,
        can_send_polls=False,
        can_send_other_messages=False,
        can_add_web_page_previews=False,
        can_change_info=False,
        can_invite_users=False,
        can_pin_messages=False,
    )

    try:
        await context.bot.restrict_chat_member(
            update.effective_chat.id,
            target.id,
            permissions=permissions,
            until_date=until_date
        )

        text = f"🔇 {target.mention_html()} muted"
        if until_date:
            text += f" for {context.args[1]} minutes"
        text += "."

        await update.message.reply_text(text, parse_mode=ParseMode.HTML)
    except Exception as e:
        await reply_error(update, str(e))


async def unmute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        return

    target, error = await get_target_user(update, context)
    if error or not target:
        await reply_error(update, error or "Reply to a user or provide @username")
        return

    permissions = ChatPermissions(
        can_send_messages=True,
        can_send_media_messages=True,
        can_send_polls=True,
        can_send_other_messages=True,
        can_add_web_page_previews=True,
        can_change_info=False,          # usually keep false
        can_invite_users=True,
        can_pin_messages=False,
    )

    try:
        await context.bot.restrict_chat_member(
            update.effective_chat.id,
            target.id,
            permissions=permissions
        )
        await update.message.reply_text(
            f"🔊 {target.mention_html()} unmuted.",
            parse_mode=ParseMode.HTML
        )
    except Exception as e:
        await reply_error(update, str(e))


async def warn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        return

    target, error = await get_target_user(update, context)
    if error or not target:
        await reply_error(update, error or "No user selected.")
        return

    reason = " ".join(context.args[1:]) if len(context.args) > 1 else "No reason given"

    await update.message.reply_text(
        f"⚠️ {target.mention_html()} <b>warned</b>\nReason: {reason}",
        parse_mode=ParseMode.HTML
    )


async def clean(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Simple delete last N bot messages or all messages from replied user"""
    if not await is_admin(update, context):
        return

    if update.message.reply_to_message:
        # delete messages of that user (last 100 messages window)
        await update.message.reply_text("Not implemented yet (needs message cleanup loop)")
        # Tip: use delete_message in loop + get_chat_history if you really need it
    else:
        await update.message.reply_text("Reply to message or use /cleanme")


# ────────────────────────────────────────────────
#  MAIN
# ────────────────────────────────────────────────

def main():
    app = Application.builder().token(TOKEN).build()

    # Public commands
    app.add_handler(CommandHandler("start", start))

    # Admin commands
    admin_commands = {
        "ban": ban,
        "kick": kick,
        "mute": mute,
        "unmute": unmute,
        "warn": warn,
        # "clean": clean,     # placeholder
    }

    for cmd, handler in admin_commands.items():
        app.add_handler(CommandHandler(
            cmd,
            handler,
            filters=ALLOWED_CHATS
        ))

    print("Bot is starting... (Ctrl+C to stop)")
    app.run_polling(
        drop_pending_updates=True,
        allowed_updates=Update.ALL_TYPES
    )


if __name__ == "__main__":
    main()