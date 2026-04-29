import json
from pathlib import Path
import pandas as pd

OUTPUT = Path("outputs/public_daily.json")

def safe_label(row):
    stage = row.get("stage", "")
    label = row.get("label", "")

    if stage == "Stage 2" and label == "Strong":
        return "Strong Structure"
    if stage == "Stage 2":
        return "Developing Structure"
    if stage == "Stage 3":
        return "Transition Structure"
    if stage == "Stage 4":
        return "Weak Structure"
    return "Emerging Structure"

def reason(row):
    parts = []

    if row.get("stage") == "Stage 2":
        parts.append("advancing structure")

    if pd.notna(row.get("rs_3m_pct")):
        parts.append(f"RS 3M {row['rs_3m_pct']:+.1f}%")

    if pd.notna(row.get("rs_6m_pct")):
        parts.append(f"RS 6M {row['rs_6m_pct']:+.1f}%")

    if pd.notna(row.get("rank_change")) and row["rank_change"] > 0:
        parts.append(f"rank ↑ {int(row['rank_change'])}")

    return " • ".join(parts[:3])

def export_json(df: pd.DataFrame):
    df = df.copy().sort_values("current_rank").head(30)

    items = []
    for _, row in df.iterrows():
        items.append({
            "ticker": row["ticker"],
            "company": row["Company Name"],
            "sector": row.get("Industry"),
            "stage": row.get("stage"),
            "label": safe_label(row),
            "rank": int(row.get("current_rank", 0)),
            "rank_change": int(row.get("rank_change", 0)),
            "reason": reason(row),
            "chart": f"charts/{row['ticker'].replace('.NS','')}.png"
        })

    payload = {
        "title": "Post-Close Market Reset",
        "top_stocks": items
    }

    OUTPUT.parent.mkdir(exist_ok=True)
    OUTPUT.write_text(json.dumps(payload, indent=2))

    return payload
