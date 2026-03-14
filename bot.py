import httpx
import asyncio
import time
from datetime import timedelta
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler,
    MessageHandler, ContextTypes, ConversationHandler, filters
)
from telegram.request import HTTPXRequest


###############################################################################
#                            BOT CONFIGURATION
###############################################################################
import os
TOKEN = os.environ.get("TOKEN")

###############################################################################
#                         CONVERSATION STATES
###############################################################################

WAIT_COUNTRY_WAR    = 1
WAIT_COUNTRY_DONATE = 2
WAIT_WAR_CHOICE     = 3
WAIT_COUNTRY_RES    = 4


###############################################################################
#                           HELPER FUNCTIONS
###############################################################################

def get_enc_time(n):
    sb = []
    n2 = 1
    while n > 0:
        n3 = ((n % 10) + 1) % 10
        if n2 % 2 == 0:
            sb.insert(0, str(n3 + n2 * 2))
        else:
            sb.insert(0, str((n3 + 2) * n2 * 3))
        n //= 10
        n2 += 1
    return ''.join(sb)

def fmt_name(entry, maxlen=22):
    if not entry:
        return "—"
    name = entry.get("name", "—")
    return name[:maxlen - 1] + "…" if len(name) > maxlen else name


###############################################################################
#                            API FETCH FUNCTIONS
###############################################################################

async def get_wars(country):
    c_time = int(time.time() * 1000)
    e_time = get_enc_time(c_time)
    try:
        async with httpx.AsyncClient(timeout=20) as client:
            print(f"[DEBUG] Fetching wars for: {country}")
            r = await client.get(
                "http://52.24.104.170:8086/RestSimulator",
                params={"Operation": "getWarsByCountry", "country": country},
                headers={
                    "User-Agent": "android-async-http",
                    "Connection": "Keep-Alive",
                    "Accept-Encoding": "gzip",
                    "c_time": str(c_time),
                    "e_time": e_time
                }
            )
            print(f"[DEBUG] Wars status: {r.status_code}")
            print(f"[DEBUG] Wars response: {r.text[:500]}")
            if r.status_code == 200:
                wars = r.json().get("wars", [])
                print(f"[DEBUG] Total wars: {len(wars)}")
                return sorted([w for w in wars if w.get("status") == 0], key=lambda x: x["id"])
    except httpx.TimeoutException:
        print("[DEBUG] Wars request timed out!")
    except httpx.ConnectError as e:
        print(f"[DEBUG] Wars connection failed: {e}")
    except Exception as e:
        print(f"[DEBUG] Wars error: {e}")
    return []

# ─────────────────────────────────────────────────────────────────────────────

async def get_resolutions(country):
    try:
        async with httpx.AsyncClient(timeout=20) as client:
            print(f"[DEBUG] Fetching resolutions for: {country}")
            r = await client.get(
                "http://52.24.104.170:8086/RestSimulator",
                params={
                    "Operation": "getActiveResolutions",
                    "country": country,
                    "sender_company_id": "4612624",
                    "user_id": "0DCB4DAD4A1844ADAFDDDC3BB7A413F9",
                    "version_code": 23
                },
                headers={
                    "User-Agent": "android-asynchttp://loopj.com/android-async-http",
                    "Accept": "*/*",
                    "Accept-Encoding": "gzip",
                    "Connection": "Keep-Alive"
                }
            )
            print(f"[DEBUG] Resolutions status: {r.status_code}")
            print(f"[DEBUG] Resolutions response: {r.text[:500]}")
            if r.status_code == 200:
                return [x for x in r.json().get("resolutions", []) if x.get("status") == 0]
    except httpx.TimeoutException:
        print("[DEBUG] Resolutions request timed out!")
    except httpx.ConnectError as e:
        print(f"[DEBUG] Resolutions connection failed: {e}")
    except Exception as e:
        print(f"[DEBUG] Resolutions error: {e}")
    return []

# ─────────────────────────────────────────────────────────────────────────────

async def get_contributors(war_id, country, count=2):
    try:
        async with httpx.AsyncClient(timeout=20) as client:
            r = await client.get(
                f"http://52.24.104.170:8086/wars/{war_id}/contributors",
                params={"country": country, "size": 1000}
            )
            if r.status_code == 200:
                data = r.json()
                if isinstance(data, list):
                    return (data + [{} for _ in range(count)])[:count]
    except Exception as e:
        print(f"[DEBUG] Contributors error: {e}")
    return [{} for _ in range(count)]


###############################################################################
#                              /start COMMAND
###############################################################################

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 *Salam! Bot ready.*\n\n"
        "Commands:\n"
        "🏛 /res — Active resolutions\n"
        "⚔️ /war — Active wars by country\n"
        "💨 /donate — Donation speed tracker\n"
        "❌ /cancel — Cancel current command",
        parse_mode="Markdown"
    )


###############################################################################
#                              /res COMMAND
###############################################################################

async def res_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🌍 Enter the country name to fetch resolutions:\n"
        "_(e.g. USA, Iran, Pakistan)_",
        parse_mode="Markdown"
    )
    return WAIT_COUNTRY_RES

# ─────────────────────────────────────────────────────────────────────────────

async def res_country(update: Update, context: ContextTypes.DEFAULT_TYPE):
    country = update.message.text.strip()
    await update.message.reply_text(
        f"⏳ Fetching resolutions for *{country}*...",
        parse_mode="Markdown"
    )
    try:
        active = await get_resolutions(country)

        if not active:
            await update.message.reply_text(
                f"⚠️ No active resolutions found for *{country}*.",
                parse_mode="Markdown"
            )
            return ConversationHandler.END

        await update.message.reply_text(
            f"✅ *{len(active)} Active Resolution(s) for {country}:*",
            parse_mode="Markdown"
        )
        for item in active:
            await update.message.reply_text(
                f"🆔 *ID:* {item.get('id', 'N/A')}\n"
                f"👤 *Initiator:* {item.get('init_company_name', 'N/A')}\n"
                f"🎯 *Target:* {item.get('country_to_attack', 'N/A')}\n"
                f"📊 *Votes:* ✅ {item.get('vote_for', 0)}  |  ❌ {item.get('vote_against', 0)}\n"
                f"🕒 *Started:* {item.get('start_time', 'N/A')}",
                parse_mode="Markdown"
            )

    except httpx.TimeoutException:
        await update.message.reply_text("❌ Timed out. Try again.")
    except httpx.ConnectError:
        await update.message.reply_text("❌ Connection error. Check your VPN.")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")

    return ConversationHandler.END


###############################################################################
#                              /war COMMAND
###############################################################################

async def war_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🌍 Enter the country name to check wars:\n"
        "_(e.g. Iran, USA, Pakistan)_",
        parse_mode="Markdown"
    )
    return WAIT_COUNTRY_WAR

# ─────────────────────────────────────────────────────────────────────────────

async def war_country(update: Update, context: ContextTypes.DEFAULT_TYPE):
    country = update.message.text.strip()
    await update.message.reply_text(
        f"⏳ Fetching wars for *{country}*...",
        parse_mode="Markdown"
    )
    try:
        active_wars = await get_wars(country)

        if not active_wars:
            await update.message.reply_text(
                f"⚠️ No active wars found for *{country}*.",
                parse_mode="Markdown"
            )
            return ConversationHandler.END

        lines = [f"⚔️ *Active Wars for {country}:*\n"]
        for i, w in enumerate(active_wars, 1):
            attacker = w.get("attacking_cou", "?")
            defender = w.get("attacked_country", "?")
            a_pts    = w.get("attacking_points", 0)
            d_pts    = w.get("attacked_points", 0)

            if country == attacker:
                status = "🟢 Winning" if a_pts > d_pts else "🔴 Losing" if a_pts < d_pts else "🟡 Draw"
            elif country == defender:
                status = "🟢 Winning" if d_pts > a_pts else "🔴 Losing" if d_pts < a_pts else "🟡 Draw"
            else:
                status = "👁 Observer"

            lines.append(
                f"`{i}.` 🆔 {w['id']} | ⚔️ {attacker} vs 🛡 {defender} | {status}"
            )

        lines.append(f"\n📊 Total: *{len(active_wars)}* active wars")
        await update.message.reply_text("\n".join(lines), parse_mode="Markdown")

    except httpx.TimeoutException:
        await update.message.reply_text("❌ Timed out. Try again.")
    except httpx.ConnectError:
        await update.message.reply_text("❌ Connection error. Check your VPN.")
    except Exception as e:
        await update.message.reply_text(f"❌ Unexpected error: {e}")

    return ConversationHandler.END


###############################################################################
#                            /donate COMMAND
###############################################################################

async def donate_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🌍 Enter the country name to track donation speed:"
    )
    return WAIT_COUNTRY_DONATE

# ─────────────────────────────────────────────────────────────────────────────

async def donate_country(update: Update, context: ContextTypes.DEFAULT_TYPE):
    country = update.message.text.strip()
    context.user_data["donate_country"] = country
    await update.message.reply_text(
        f"⏳ Fetching wars for *{country}*...",
        parse_mode="Markdown"
    )
    try:
        active_wars = await get_wars(country)

        if not active_wars:
            await update.message.reply_text("⚠️ No active wars found.")
            return ConversationHandler.END

        context.user_data["donate_wars"] = active_wars
        lines = ["⚔️ *Choose a war to track:*\n"]
        for i, w in enumerate(active_wars, 1):
            lines.append(
                f"`{i}.` {w.get('attacking_cou', '?')} ⚔️ "
                f"{w.get('attacked_country', '?')} (ID: {w['id']})"
            )
        lines.append("\n✏️ Reply with the number:")
        await update.message.reply_text("\n".join(lines), parse_mode="Markdown")
        return WAIT_WAR_CHOICE

    except httpx.TimeoutException:
        await update.message.reply_text("❌ Timed out. Try again.")
    except httpx.ConnectError:
        await update.message.reply_text("❌ Connection error. Check your VPN.")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")

    return ConversationHandler.END

# ─────────────────────────────────────────────────────────────────────────────

async def donate_war_chosen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    wars = context.user_data.get("donate_wars", [])
    try:
        idx = int(update.message.text.strip()) - 1
        if idx < 0 or idx >= len(wars):
            raise ValueError
    except:
        await update.message.reply_text("❌ Invalid number. Try /donate again.")
        return ConversationHandler.END

    war      = wars[idx]
    war_id   = war["id"]
    attacker = war["attacking_cou"]
    defender = war["attacked_country"]

    await update.message.reply_text(
        f"📡 *Tracking donation speed*\n"
        f"⚔️ {attacker} vs 🛡 {defender}\n\n"
        f"Running 6 checks × 10s = ~1 minute.\n⏳ Please wait...",
        parse_mode="Markdown"
    )

    last_a       = [0, 0]
    last_d       = [0, 0]
    total_a_diff = [0, 0]
    total_d_diff = [0, 0]
    top_a        = []
    top_d        = []

    for tick in range(6):
        top_a = await get_contributors(war_id, attacker)
        top_d = await get_contributors(war_id, defender)

        for i in range(2):
            a_score = top_a[i].get("score", 0)
            d_score = top_d[i].get("score", 0)
            a_diff  = a_score - last_a[i]
            d_diff  = d_score - last_d[i]

            if tick > 0:
                total_a_diff[i] += a_diff
                total_d_diff[i] += d_diff

            last_a[i] = a_score
            last_d[i] = d_score

        if tick < 5:
            await asyncio.sleep(10)

    minutes = 5 * 10 / 60
    lines = [f"📊 *Donation Speed Results*\n⚔️ {attacker} vs 🛡 {defender}\n"]

    for i in range(2):
        a_name = fmt_name(top_a[i])
        d_name = fmt_name(top_d[i])
        a_rate = int(total_a_diff[i] / minutes) if minutes > 0 else 0
        d_rate = int(total_d_diff[i] / minutes) if minutes > 0 else 0

        if a_rate > d_rate:
            a_tag, d_tag = "💨 Faster", "🐢 Slower"
        elif d_rate > a_rate:
            a_tag, d_tag = "🐢 Slower", "💨 Faster"
        else:
            a_tag, d_tag = "🟡 Equal", "🟡 Equal"

        lines.append(
            f"*#{i + 1}*\n"
            f"⚔️ `{a_name}` — {a_rate:,}/min {a_tag}\n"
            f"🛡 `{d_name}` — {d_rate:,}/min {d_tag}\n"
        )

    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")
    return ConversationHandler.END


###############################################################################
#                            /cancel COMMAND
###############################################################################

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Cancelled.")
    return ConversationHandler.END


###############################################################################
#                          BOT STARTUP & HANDLERS
###############################################################################

request = HTTPXRequest(connect_timeout=30, read_timeout=30)
app = ApplicationBuilder().token(TOKEN).request(request).build()

app.add_handler(CommandHandler("start", start))

app.add_handler(ConversationHandler(
    entry_points=[CommandHandler("res", res_start)],
    states={
        WAIT_COUNTRY_RES: [MessageHandler(filters.TEXT & ~filters.COMMAND, res_country)]
    },
    fallbacks=[CommandHandler("cancel", cancel)]
))

app.add_handler(ConversationHandler(
    entry_points=[CommandHandler("war", war_start)],
    states={
        WAIT_COUNTRY_WAR: [MessageHandler(filters.TEXT & ~filters.COMMAND, war_country)]
    },
    fallbacks=[CommandHandler("cancel", cancel)]
))

app.add_handler(ConversationHandler(
    entry_points=[CommandHandler("donate", donate_start)],
    states={
        WAIT_COUNTRY_DONATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, donate_country)],
        WAIT_WAR_CHOICE:     [MessageHandler(filters.TEXT & ~filters.COMMAND, donate_war_chosen)],
    },
    fallbacks=[CommandHandler("cancel", cancel)]
))

print("Bot is running...")
app.run_polling()