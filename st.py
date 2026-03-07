import requests
from urllib.parse import quote
from telegram import Update
from telegram.ext import ContextTypes

SECONDS_IN_MINUTE = 60

async def run(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Parse command arguments
    if len(context.args) < 3:
        await update.message.reply_text(
            "Usage: /ST <WAR_ID> <COUNTRY1> <COUNTRY2>\nExample: /ST 57855 Germany Laos"
        )
        return

    war_id = context.args[0]
    country1 = context.args[1]
    country2 = context.args[2]
    countries = [country1, country2]
    SIZE = 1000

    BASE_URL = f"http://52.24.104.170:8086/wars/{war_id}/contributors"

    def fetch_contributors(country):
        try:
            country_encoded = quote(country)
            url = f"{BASE_URL}?country={country_encoded}&size={SIZE}"
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            data = response.json()
            if not isinstance(data, list):
                return {}
            return {c['name']: c['score'] for c in data}
        except:
            return {}

    def calculate_score_diff(prev, curr):
        diff = {}
        for name, score in curr.items():
            prev_score = prev.get(name, 0)
            points_gained = score - prev_score
            diff[name] = points_gained  # points per snapshot (1 command)
        return diff

    # Take a single snapshot
    previous_scores = {country: fetch_contributors(country) for country in countries}

    # Take another snapshot immediately (simulate short interval)
    current_scores = {country: fetch_contributors(country) for country in countries}

    msg = f"🇪🇺 *BEAST X War Tracker*\nWar ID: {war_id}\n\n"

    for country in countries:
        curr = current_scores[country]
        prev = previous_scores[country]
        if not curr:
            msg += f"⚠️ No contributors for {country}\n\n"
            continue

        score_diff = calculate_score_diff(prev, curr)
        sorted_contributors = sorted(curr.items(), key=lambda x: x[1], reverse=True)

        msg += f"🌟 *[{country}]* Total points: {sum(curr.values())}\n"
        msg += "🔥 Contributor | 💎 Score | ⚡ Speed\n"
        msg += "─"*40 + "\n"

        for i, (name, score) in enumerate(sorted_contributors[:10], start=1):
            speed = score_diff.get(name, 0)
            diff_emoji = "🔺" if speed > 0 else "➡️" if speed == 0 else "🔻"
            medal = "🥇" if i==1 else "🥈" if i==2 else "🥉" if i==3 else ""
            msg += f"{diff_emoji} {name:<15} {score:<6} {speed:<4} {medal}\n"

        msg += "\n"

    await update.message.reply_text(msg)