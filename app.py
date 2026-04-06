from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app, origins="*")

NOTION_KEY = os.getenv("NOTION_KEY")
NOTION_DB  = os.getenv("NOTION_DB")
NOTION_VER = "2022-06-28"

def get_headers():
    return {
        "Authorization": f"Bearer {NOTION_KEY}",
        "Notion-Version": NOTION_VER,
        "Content-Type": "application/json"
    }

@app.route("/")
def home():
    return "Job Tally API is running!"

@app.route("/debug")
def debug():
    # Shows if env vars are loaded (hides actual key for safety)
    return jsonify({
        "NOTION_KEY_set": bool(NOTION_KEY),
        "NOTION_KEY_prefix": NOTION_KEY[:10] + "..." if NOTION_KEY else None,
        "NOTION_DB_set": bool(NOTION_DB),
        "NOTION_DB": NOTION_DB
    })

@app.route("/sync", methods=["POST", "OPTIONS"])
def sync():
    if request.method == "OPTIONS":
        response = jsonify({})
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type"
        response.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
        return response, 200

    data     = request.json
    today    = data.get("date")
    count    = data.get("count")
    goal_met = data.get("goalMet")

    q = requests.post(
        f"https://api.notion.com/v1/databases/{NOTION_DB}/query",
        headers=get_headers(),
        json={"filter": {"property": "Date", "title": {"equals": today}}}
    )
    results = q.json().get("results", [])

    if results:
        page_id = results[0]["id"]
        r = requests.patch(
            f"https://api.notion.com/v1/pages/{page_id}",
            headers=get_headers(),
            json={"properties": {
                "Applications": {"number": count},
                "Goal Met?":    {"checkbox": goal_met}
            }}
        )
    else:
        r = requests.post(
            "https://api.notion.com/v1/pages",
            headers=get_headers(),
            json={
                "parent": {"database_id": NOTION_DB},
                "properties": {
                    "Date":         {"title": [{"text": {"content": today}}]},
                    "Applications": {"number": count},
                    "Goal Met?":    {"checkbox": goal_met}
                }
            }
        )

    if r.ok:
        response = jsonify({"status": "ok"})
        response.headers["Access-Control-Allow-Origin"] = "*"
        return response
    else:
        response = jsonify({"status": "error", "detail": r.text})
        response.headers["Access-Control-Allow-Origin"] = "*"
        return response, 500

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)