import http.client
import json
import urllib.parse
from datetime import datetime

COUNTRIES = [
    "Russia","Germany","France","Spain","Argentina","Japan","Portugal","Pakistan","Iran"
]

SENDER_COMPANY_ID = "3521724"
USER_ID = "D31C0B83672E475A9C3373C376BF6DD9"
VERSION_CODE = "15"

def fetch_wars(country):
    try:
        conn = http.client.HTTPConnection("52.24.104.170", 8086, timeout=30)
        headers = {"User-Agent": "android-async-http"}

        path = (
            f"/RestSimulator?Operation=getWarsByCountry"
            f"&country={urllib.parse.quote(country)}"
            f"&sender_company_id={SENDER_COMPANY_ID}"
            f"&user_id={USER_ID}"
            f"&version_code={VERSION_CODE}"
        )

        conn.request("GET", path, headers=headers)
        data = conn.getresponse().read().decode("utf-8")

        if "no_operation_found" in data.lower():
            return []

        return json.loads(data).get("wars", [])

    except:
        return []
    finally:
        try:
            conn.close()
        except:
            pass

def check_war_lock(war_id, country):
    try:
        conn = http.client.HTTPConnection("52.24.104.170", 8086, timeout=30)
        headers = {"User-Agent": "android-async-http"}
        path = f"/wars/{war_id}/contributors?country={urllib.parse.quote(country)}&size=1000"
        conn.request("GET", path, headers=headers)
        resp = conn.getresponse()
        if resp.status == 500:
            return "LOCKED"
        elif resp.status == 200:
            return "OPEN"
        else:
            return "UNKNOWN"
    except:
        return "ERROR"
    finally:
        try:
            conn.close()
        except:
            pass

async def run(update, context):
    msg = f"🔒 *Elite War Lock Scanner*\nScan Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    all_wars = []

    for country in COUNTRIES:
        wars = fetch_wars(country)
        for war in wars:
            war_id = war.get("id")
            status = check_war_lock(war_id, country)
            attacker = war.get("attacking_cou", "?")
            defender = war.get("attacked_country", "?")
            attacker_points = war.get("attacking_points", 0)
            defender_points = war.get("attacked_points", 0)

            if attacker_points > defender_points:
                winner = f"{attacker} winning"
            elif defender_points > attacker_points:
                winner = f"{defender} winning"
            else:
                winner = "Tied"

            all_wars.append({
                "attacker": attacker,
                "defender": defender,
                "status": status,
                "winner": winner,
                "id": war_id
            })

    if not all_wars:
        msg += "⚠️ No ongoing wars detected."
        await update.message.reply_text(msg)
        return

    for w in all_wars[:20]:  # limit to first 20 for readability
        color_emoji = "🟢" if w["status"] == "OPEN" else "🔴"
        msg += (
            f"{color_emoji} *{w['status']}* | {w['attacker']} vs {w['defender']}\n"
            f"Winner: {w['winner']}\n"
            f"WAR ID: {w['id']}\n\n"
        )

    await update.message.reply_text(msg)