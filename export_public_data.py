from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd


DEFAULT_OUTPUT_PATH = Path("outputs/public_daily.json")


SENSITIVE_COLUMNS = {
    "action", "portfolio_action", "trade_action", "decision", "recommendation",
    "entry", "entry_price", "target", "stop_loss", "sl", "position_size",
    "allocation", "weight", "risk_reward", "buy", "sell", "short", "long",
    "action_confidence", "decision_priority", "decision_score", "rationale",
}


def _first_value(row: pd.Series, columns: List[str], default: Any = None) -> Any:
    for col in columns:
        if col in row.index:
            val = row.get(col)
            if pd.notna(val):
                return val
    return default


def _num(value: Any, default: Optional[float] = None) -> Optional[float]:
    val = pd.to_numeric(value, errors="coerce")
    if pd.isna(val):
        return default
    return float(val)


def _int(value: Any, default: Optional[int] = None) -> Optional[int]:
    val = _num(value, None)
    if val is None:
        return default
    return int(round(val))


def _safe_text(value: Any, default: str = "") -> str:
    if value is None or pd.isna(value):
        return default
    return str(value).strip()


def _stage_label(stage: str) -> str:
    return {
        "Stage 1": "Base Formation",
        "Stage 2": "Advancing Structure",
        "Stage 3": "Transition Structure",
        "Stage 4": "Declining Structure",
    }.get(stage, stage or "Mixed Structure")


def _public_structure_label(row: pd.Series) -> str:
    stage = _safe_text(row.get("stage"))
    label = _safe_text(_first_value(row, ["label", "classification"], ""))
    score = _num(_first_value(row, ["final_combined_score", "avg_combined_score", "combined_score", "decision_score"], None), None)

    if stage == "Stage 2" and label == "Strong":
        return "Strong Structure"
    if stage == "Stage 2":
        return "Improving Structure" if score is not None and score >= 60 else "Developing Structure"
    if stage == "Stage 1":
        return "Base Formation"
    if stage == "Stage 3":
        return "Transition Structure"
    if stage == "Stage 4":
        return "Weak Structure"
    return "Mixed Structure"


def _reason(row: pd.Series) -> str:
    parts: List[str] = []
    stage = _safe_text(row.get("stage"))

    if stage:
        parts.append(_stage_label(stage))

    rs3 = _num(row.get("rs_3m_pct"), None)
    rs6 = _num(row.get("rs_6m_pct"), None)
    if rs3 is not None:
        parts.append(f"RS 3M {rs3:+.1f}%")
    if rs6 is not None:
        parts.append(f"RS 6M {rs6:+.1f}%")

    rank_change = _num(row.get("rank_change"), None)
    if rank_change is not None and rank_change != 0:
        arrow = "↑" if rank_change > 0 else "↓"
        parts.append(f"Rank {arrow} {abs(int(rank_change))}")

    if bool(row.get("new_weekly_breakout", False)):
        parts.append("Weekly breakout flag")
    elif bool(row.get("new_daily_breakout", False)):
        parts.append("Daily breakout flag")

    return " • ".join(parts[:4])


def _chart_path(ticker: str, chart_type: str = "daily") -> str:
    raw = ticker.replace(".NS", "").strip()
    if chart_type == "weekly":
        return f"charts/weekly/{raw}_weekly.png"
    return f"charts/daily/{raw}_daily.png"


def _prepare_df(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()

    if "Company Name" not in out.columns:
        for alt in ["company", "company_name", "name", "Company"]:
            if alt in out.columns:
                out["Company Name"] = out[alt]
                break
    if "Industry" not in out.columns:
        for alt in ["sector", "industry", "Sector"]:
            if alt in out.columns:
                out["Industry"] = out[alt]
                break
    if "ticker" not in out.columns:
        for alt in ["Ticker", "symbol", "Symbol"]:
            if alt in out.columns:
                out["ticker"] = out[alt]
                break

    if "current_rank" not in out.columns:
        for alt in ["rank", "rs_rank", "daily_rank", "weekly_rank", "final_rank", "combined_rank", "stock_rank"]:
            if alt in out.columns:
                out["current_rank"] = pd.to_numeric(out[alt], errors="coerce")
                break

    if "current_rank" not in out.columns:
        out["current_rank"] = range(1, len(out) + 1)

    out["current_rank"] = pd.to_numeric(out["current_rank"], errors="coerce")
    out = out.dropna(subset=["ticker", "Company Name"])
    out = out.sort_values(["current_rank", "Company Name"], ascending=[True, True])
    return out


def build_public_payload(
    df: pd.DataFrame,
    *,
    max_items: int = 30,
    title: str = "Post-Close Market Structure Reset",
) -> Dict[str, Any]:
    out = _prepare_df(df)
    public_df = out.head(max_items).copy()

    items: List[Dict[str, Any]] = []
    for _, row in public_df.iterrows():
        ticker = _safe_text(row.get("ticker"))
        rank = _int(row.get("current_rank"), None)
        item = {
            "ticker": ticker,
            "company": _safe_text(row.get("Company Name")),
            "sector": _safe_text(row.get("Industry")),
            "stage": _safe_text(row.get("stage")),
            "phase": _stage_label(_safe_text(row.get("stage"))),
            "structure_label": _public_structure_label(row),
            "rank": rank,
            "rank_change": _int(row.get("rank_change"), 0),
            "rs_3m_pct": _num(row.get("rs_3m_pct"), None),
            "rs_6m_pct": _num(row.get("rs_6m_pct"), None),
            "reason": _reason(row),
            "daily_chart": _chart_path(ticker, "daily"),
            "weekly_chart": _chart_path(ticker, "weekly"),
        }
        items.append(item)

    stage_distribution = []
    if "stage" in out.columns:
        for stage, count in out["stage"].value_counts(dropna=False).sort_index().items():
            stage_distribution.append({"stage": _safe_text(stage, "Unknown"), "count": int(count)})

    sector_strength = []
    if "Industry" in out.columns and "stage" in out.columns:
        sector_strength = (
            out[out["stage"].eq("Stage 2")]
            .groupby("Industry")
            .size()
            .reset_index(name="stage_2_count")
            .sort_values("stage_2_count", ascending=False)
            .head(10)
            .rename(columns={"Industry": "sector"})
            .to_dict(orient="records")
        )

    leader_sector = sector_strength[0]["sector"] if sector_strength else None

    return {
        "title": title,
        "updated_at": datetime.now().isoformat(timespec="seconds"),
        "updated_after_close": True,
        "disclaimer": "This is rule-based market structure analytics and visualization only. It is not investment advice or a recommendation.",
        "summary": {
            "total_stocks": int(len(out)),
            "published_items": int(len(items)),
            "stage_distribution": stage_distribution,
            "leader_sector": leader_sector,
        },
        "top_stocks": items,
        "sector_strength": sector_strength,
    }


def export_json(
    df: pd.DataFrame,
    output_path: str | Path = DEFAULT_OUTPUT_PATH,
    *,
    max_items: int = 30,
) -> Path:
    path = Path(output_path)
    payload = build_public_payload(df, max_items=max_items)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return path
