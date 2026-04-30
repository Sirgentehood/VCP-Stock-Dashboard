import json
import requests
import streamlit as st

def export_json(df, max_items=30):
    df = df.sort_values("current_rank").head(max_items)

    items = []

    for _, row in df.iterrows():
        items.append({
            "ticker": row["ticker"],
            "company": row["Company Name"],
            "sector": row.get("Industry"),
            "stage": row.get("stage"),
            "label": row.get("label"),
            "rank": int(row.get("current_rank", 0)),
            "rank_change": int(row.get("rank_change", 0)),
            "reason": "structure improving"
        })

    payload = {
        "title": "Post-Close Market Reset",
        "top_stocks": items
    }

    json_content = json.dumps(payload, indent=2)

    # 🔥 PUSH TO GITHUB
    token = st.secrets["GITHUB_TOKEN"]
    username = st.secrets["GITHUB_USERNAME"]
    repo = st.secrets["GITHUB_REPO"]

    url = f"https://api.github.com/repos/{username}/{repo}/contents/outputs/public_daily.json"

    headers = {
        "Authorization": f"token {token}"
    }

    # Get current file SHA
    r = requests.get(url, headers=headers)

    sha = None
    if r.status_code == 200:
        sha = r.json()["sha"]

    data = {
        "message": "update public json",
        "content": json_content.encode("utf-8").decode("utf-8"),
        "branch": "main"
    }

    if sha:
        data["sha"] = sha

    requests.put(url, headers=headers, json=data)

    return payload
