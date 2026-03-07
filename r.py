import http.client
import json
import urllib.parse
from datetime import datetime

COUNTRIES = [
    "China","United States","United Kingdom","Russia","Germany","France",
    "Italy","Spain","Canada","Mexico","Brazil","Argentina","Nigeria","Ghana",
    "Kenya","Japan","Portugal","Pakistan","Ireland","Uganda","Denmark","Iran"
]

def format_time(ms):
    s = ms // 1000
    m, s = divmod(s, 60)
    h, m = divmod(m, 60)
    d, h = divmod(h, 24)
    return f"{d}d {h}h {m}m"

def fetch_resolutions(country):
    conn = http.client.HTTPConnection("52.24.104.170", 8086, timeout=60)
    headers = {"User-Agent": "android-async-http"}

    path = (
        f"/RestSimulator?Operation=getActiveResolutions"
        f"&country={urllib.parse.quote(country)}"
        f"&sender_company_id=3521724"
        f"&user_id=D31C0B83672E475A9C3373C376BF6DD9"
        f"&version_code=15"
    )

    conn.request("GET", path, headers=headers)
    data = conn.getresponse().read().decode("utf-8")

    try:
        return json.loads(data).get("resolutions", [])
    except:
        return []

async def run(update, context):

    msg = "🗳️ *Elite Resolution Radar*\n"
    msg += f"Scan Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"

    all_resolutions = []

    for country in COUNTRIES:

        result = fetch_resolutions(country)

        for r in result:
            all_resolutions.append({
                "from": r.get("country_name", "?"),
                "target": r.get("country_to_attack", "?"),
                "yes": int(r.get("vote_for", 0)),
                "no": int(r.get("vote_against", 0)),
                "end": int(r.get("end_time", 0)),
                "id": r.get("id", "?")
            })

    if not all_resolutions:
        msg += "⚠️ No active resolutions found."
        await update.message.reply_text(msg)
        return

    all_resolutions.sort(key=lambda x: x["end"])

    for r in all_resolutions[:20]:
        msg += (
            f"\n⏳ {format_time(r['end'])}"
            f"\nFrom: {r['from']}"
            f"\nTarget: {r['target']}"
            f"\nYes: {r['yes']} | No: {r['no']}"
            f"\nID: {r['id']}\n"
        )

    await update.message.reply_text(msg)