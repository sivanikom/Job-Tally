from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)

NOTION_KEY = os.getenv("NOTION_KEY")
NOTION_DB  = os.getenv("NOTION_DB")
NOTION_VER = "2022-06-28"
HEADERS = {
    "Authorization": f"Bearer {NOTION_KEY}",
    "Notion-Version": NOTION_VER,
    "Content-Type": "application/json"
}

@app.route("/sync", methods=["POST"])
def sync():
    data  = request.json
    today = data.get("date")
    count = data.get("count")
    goal_met = data.get("goalMet")

    # Check if row for today exists
    q = requests.post(
        f"https://api.notion.com/v1/databases/{NOTION_DB}/query",
        headers=HEADERS,
        json={"filter": {"property": "Date", "title": {"equals": today}}}
    )
    results = q.json().get("results", [])

    if results:
        # Update existing row
        page_id = results[0]["id"]
        r = requests.patch(
            f"https://api.notion.com/v1/pages/{page_id}",
            headers=HEADERS,
            json={"properties": {
                "Applications": {"number": count},
                "Goal Met?":    {"checkbox": goal_met}
            }}
        )
    else:
        # Create new row
        r = requests.post(
            "https://api.notion.com/v1/pages",
            headers=HEADERS,
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
        return jsonify({"status": "ok"})
    else:
        return jsonify({"status": "error", "detail": r.text}), 500

if __name__ == "__main__":
    app.run(port=5000)