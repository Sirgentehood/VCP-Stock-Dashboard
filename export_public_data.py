import json
from pathlib import Path
import pandas as pd

OUTPUT = Path("outputs/public_daily.json")

def safe_label(row):
    stage = str(row.get("stage", ""))

    if stage == "Stage 2":
        return "Strong Structure"
    if stage == "Stage 3":
        return "Transition Structure"
    if stage == "Stage 4":
        return "Weak Structure"
    return "Developing Structure"


def build_reason(row):
    parts = []

    if row.get("stage") == "Stage 2":
        parts.append("advancing structure")

    if row.get("stage") == "Stage 3":
        parts.append("transition phase")

    rs3 = pd.to_numeric(row.get("rs_3m_pct"), errors="coerce")
    rs6 = pd.to_numeric(row.get("rs_6m_pct"), errors="coerce")

    if pd.notna(rs3):
        parts.append(f"RS 3M {rs3:+.1f}%")

    if pd.notna(rs6):
        parts.append(f"RS 6M {rs6:+.1f}%")

    rank_change = pd.to_numeric(row.get("rank_change"), errors="coerce")
    if pd.notna(rank_change) and rank_change > 0:
        parts.append(f"rank ↑ {int(rank_change)}")

    return " • ".join(parts[:3])


def export_json(df: pd.DataFrame, max_items: int = 30):
    df = df.copy()

    # Protect your moat: only export top 30
    df = df.sort_values("current_rank").head(max_items)
    items = []

    for _, row in df.iterrows():
        items.append({
            "ticker": row.get("ticker"),
            "company": row.get("Company Name"),
            "sector": row.get("Industry"),
            "stage": row.get("stage"),
            "label": safe_label(row),
            "rank": int(row.get("current_rank", 0)),
            "rank_change": int(row.get("rank_change", 0)),
            "reason": build_reason(row),
            "chart": f"charts/{str(row.get('ticker','')).replace('.NS','')}.png"
        })

    payload = {
        "title": "Post-Close Market Reset",
        "disclaimer": "This is data-driven market structure. Not investment advice.",
        "top_stocks": items
    }

    OUTPUT.parent.mkdir(exist_ok=True)
    OUTPUT.write_text(json.dumps(payload, indent=2))

    return payload
