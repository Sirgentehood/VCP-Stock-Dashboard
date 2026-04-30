import json
import base64
import requests
import streamlit as st


def export_json(df, max_items=30):
    try:
        # ----------------------------
        # 1. Prepare data
        # ----------------------------
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
                "reason": build_reason(row),
                "chart": f"charts/{row['ticker'].replace('.NS','')}.png"
            })

        payload = {
            "title": "Post-Close Market Reset",
            "disclaimer": "This is data-driven market structure. Not investment advice.",
            "top_stocks": items
        }

        # ----------------------------
        # 2. Convert to base64
        # ----------------------------
        json_str = json.dumps(payload, indent=2)
        encoded_content = base64.b64encode(json_str.encode()).decode()

        # ----------------------------
        # 3. GitHub config
        # ----------------------------
        token = st.secrets["GITHUB_TOKEN"]
        username = st.secrets["GITHUB_USERNAME"]
        repo = st.secrets["GITHUB_REPO"]

        path = "outputs/public_daily.json"

        url = f"https://api.github.com/repos/{username}/{repo}/contents/{path}"

        headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github+json"
        }

        # ----------------------------
        # 4. Get existing file SHA
        # ----------------------------
        response = requests.get(url, headers=headers)

        sha = None
        if response.status_code == 200:
            sha = response.json()["sha"]

        # ----------------------------
        # 5. Push update
        # ----------------------------
        data = {
            "message": "auto update public json",
            "content": encoded_content,
            "branch": "main"
        }

        if sha:
            data["sha"] = sha

        push_response = requests.put(url, headers=headers, json=data)

        # ----------------------------
        # 6. Error handling
        # ----------------------------
        if push_response.status_code not in [200, 201]:
            st.error(f"GitHub push failed: {push_response.text}")
            return None

        st.success("✅ Public JSON updated on GitHub")

        return payload

    except Exception as e:
        st.error(f"Export failed: {str(e)}")
        return None


# ----------------------------
# Helper (same logic as before)
# ----------------------------
def build_reason(row):
    parts = []

    if row.get("stage") == "Stage 2":
        parts.append("advancing structure")

    if row.get("stage") == "Stage 3":
        parts.append("transition phase")

    if row.get("rs_3m_pct") is not None:
        parts.append(f"RS 3M {row.get('rs_3m_pct'):+.1f}%")

    if row.get("rs_6m_pct") is not None:
        parts.append(f"RS 6M {row.get('rs_6m_pct'):+.1f}%")

    if row.get("rank_change", 0) > 0:
        parts.append(f"rank ↑ {int(row['rank_change'])}")

    return " • ".join(parts[:3])
