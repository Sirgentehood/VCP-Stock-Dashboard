import streamlit as st
import pandas as pd
from pathlib import Path
import math
import re
from html import escape
import html

st.set_page_config(page_title="Market Structure Radar", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
<style>
:root {
  --card-border: rgba(128,128,128,0.16);
  --muted: rgba(255,255,255,0.72);
  --strong: #1ec977;
  --developing: #f0b429;
  --weak: #ff6b6b;
  --cautious: #ff9f43;
  --up: #1ec977;
  --down: #ff6b6b;
  --stage1-bg: rgba(55,95,220,0.14);
  --stage2-bg: rgba(0,179,179,0.12);
  --stage3-bg: rgba(212,160,23,0.12);
  --stage4-bg: rgba(170,80,180,0.14);
  --stage1-border: rgba(55,95,220,0.34);
  --stage2-border: rgba(0,179,179,0.28);
  --stage3-border: rgba(212,160,23,0.28);
  --stage4-border: rgba(170,80,180,0.34);
}
.block-container {padding-top: 0.45rem; padding-bottom: 1.2rem; padding-left: 0.7rem; padding-right: 0.7rem; max-width: 1400px;}
[data-testid="stSidebar"], section[data-testid="stSidebar"], [data-testid="collapsedControl"] {display:none;}
.stTabs [data-baseweb="tab"] {font-size: 1.15rem; font-weight: 700;}
.stTabs [data-baseweb="tab-list"] {gap: 0.55rem; margin-top: 0.1rem;}
.hero-card, .stock-card, .list-card, .learn-card {
  border: 2px solid var(--card-border);
  border-radius: 16px;
  padding: 0.8rem 0.9rem;
}
.hero-card {padding: 0.95rem 1rem; background: rgba(255,255,255,0.03);}
.kicker {font-size: 0.76rem; text-transform: uppercase; letter-spacing: 0.06em; color: var(--muted);}
.big-number {font-size: 1.34rem; font-weight: 800; margin-top: 0.08rem; margin-bottom: 0.1rem;}
.muted {color: var(--muted);}
.status-pill {display:inline-block; font-size:0.74rem; font-weight:700; padding:0.18rem 0.5rem; border-radius:999px; white-space:nowrap;}
.status-strong {background: rgba(30,201,119,0.14); color: var(--strong); border:1px solid rgba(30,201,119,0.35);}
.status-developing {background: rgba(240,180,41,0.14); color: var(--developing); border:1px solid rgba(240,180,41,0.35);}
.status-weak {background: rgba(255,107,107,0.14); color: var(--weak); border:1px solid rgba(255,107,107,0.35);}
.status-cautious {background: rgba(255,159,67,0.14); color: var(--cautious); border:1px solid rgba(255,159,67,0.35);}
.action-pill {display:inline-block; font-size:0.74rem; font-weight:800; padding:0.18rem 0.5rem; border-radius:999px; white-space:nowrap; margin-top:0.22rem;}
.action-opportunity {background: rgba(30,201,119,0.12); color: var(--strong); border:1px solid rgba(30,201,119,0.35);}
.action-watch {background: rgba(55,95,220,0.12); color: #8ab4ff; border:1px solid rgba(55,95,220,0.35);}
.action-caution {background: rgba(255,159,67,0.12); color: var(--cautious); border:1px solid rgba(255,159,67,0.35);}
.action-avoid {background: rgba(255,107,107,0.12); color: var(--weak); border:1px solid rgba(255,107,107,0.35);}
.assist-box {border:1px solid var(--card-border); border-radius:16px; padding:0.85rem 0.95rem; background:rgba(255,255,255,0.03); margin-bottom:0.55rem;}
.assist-title {font-size:1rem; font-weight:800; margin-bottom:0.28rem;}
.assist-text {font-size:0.98rem; color: #f3f6fb; line-height:1.55;}
.stock-title {font-size: 1.02rem; font-weight: 700; margin-bottom: 0.06rem; line-height: 1.2;}
.meta-line {font-size: 0.93rem; font-weight: 600; line-height: 1.18; margin-top: 0.06rem; margin-bottom: 0.02rem;}
.stock-subtitle {font-size: 0.92rem; color: var(--muted); margin-top: 0.04rem; line-height: 1.1;}
.stock-card {margin-bottom: 0.42rem; background: rgba(255,255,255,0.03); padding-top: 0.72rem; padding-bottom: 0.72rem;}
.stage-card-1 {background: var(--stage1-bg); border-color: var(--stage1-border);}
.stage-card-2 {background: var(--stage2-bg); border-color: var(--stage2-border);}
.stage-card-3 {background: var(--stage3-bg); border-color: var(--stage3-border);}
.stage-card-4 {background: var(--stage4-bg); border-color: var(--stage4-border);}
.change-badge-up {font-size: 1.12rem; font-weight: 900; margin-top: 0.1rem; color: var(--up);}
.change-badge-down {font-size: 1.12rem; font-weight: 900; margin-top: 0.1rem; color: var(--down);}
.rank-text {font-size: 0.84rem; font-weight: 700; color: var(--muted); margin-top: 0.18rem;}
.disclosure {border-left: 4px solid rgba(240,180,41,0.55); background: rgba(240,180,41,0.08); border-radius: 12px; padding: 0.7rem 0.85rem; font-size: 0.86rem; margin-bottom: 0.7rem; margin-top: 1rem;}
.simple-list-item {border-bottom: 1px solid rgba(255,255,255,0.06); padding: 0.55rem 0;}
.simple-list-item:last-child {border-bottom:none;}
.list-tight {margin: 0.2rem 0 0 1rem; padding: 0;}
.change-text {font-size: 0.88rem; margin-top: 0.06rem; line-height: 1.18;}
@media (max-width: 768px) {
  .block-container {padding-top: 0.35rem; padding-left: 0.35rem; padding-right: 0.35rem;}
  .stTabs [data-baseweb="tab"] {font-size: 0.93rem;}
  .detail-grid {grid-template-columns: 1fr; gap:0.65rem;}
  .stock-title {font-size: 0.96rem;}
  .meta-line {font-size: 0.88rem; line-height:1.28;}
  .assist-text, .signal-line, .change-text {font-size: 0.95rem; line-height:1.45;}
  .detail-box b {display:block; margin-bottom:0.14rem; color:#cfe0ff;}
}
</style>
""", unsafe_allow_html=True)

LABELS = {
    "Strong": {"css": "status-strong"},
    "Developing": {"css": "status-developing"},
    "Weak": {"css": "status-weak"},
    "Cautious": {"css": "status-cautious"},
}

MAX_PORTFOLIO_STOCKS = 25

@st.cache_data(show_spinner=False)
def load_csv(path: str, mtime_ns: int) -> pd.DataFrame:
    return pd.read_csv(path)

def safe_read(path: str) -> pd.DataFrame:
    p = Path(path)
    if not p.exists():
        return pd.DataFrame()
    try:
        return load_csv(str(p), p.stat().st_mtime_ns)
    except Exception:
        return pd.DataFrame()

def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    out = df.copy()
    if "Company Name" not in out.columns:
        for col in ["Company Name_x", "Company Name_y"]:
            if col in out.columns:
                out["Company Name"] = out[col]
                break
    if "Industry" not in out.columns:
        for col in ["Industry_x", "Industry_y"]:
            if col in out.columns:
                out["Industry"] = out[col]
                break
    drop_cols = [c for c in ["Company Name_x", "Company Name_y", "Industry_x", "Industry_y", "Ticker"] if c in out.columns]
    if drop_cols:
        out = out.drop(columns=drop_cols)
    return out

def classify_stock(row: pd.Series) -> str:
    stage = str(row.get("stage", ""))
    score = pd.to_numeric(row.get("final_combined_score", row.get("combined_score")), errors="coerce")
    rs3 = pd.to_numeric(row.get("rs_3m_pct"), errors="coerce")
    rs6 = pd.to_numeric(row.get("rs_6m_pct"), errors="coerce")

    if stage == "Stage 2":
        if pd.notna(score) and score >= 70:
            return "Strong"
        return "Developing"

    if stage == "Stage 1":
        if pd.notna(rs3) and pd.notna(rs6) and rs3 < 0 and rs6 < 0:
            return "Cautious"
        return "Developing"

    if stage == "Stage 3":
        if pd.notna(score) and score >= 65:
            return "Cautious"
        if pd.notna(rs3) and rs3 > 0 and pd.notna(rs6) and rs6 >= 0:
            return "Cautious"
        return "Weak"

    if stage == "Stage 4":
        return "Weak"

    if pd.notna(rs3) and pd.notna(rs6) and rs3 < 0 and rs6 < 0:
        return "Weak"
    return "Developing"

def ensure_label(df: pd.DataFrame) -> pd.DataFrame:
    out = normalize_columns(df)
    numeric_cols = [
        "final_combined_score", "avg_combined_score", "current_rank", "prev_rank", "rank_change",
        "combined_score_change", "change_1d_pct", "change_1w_pct", "change_1m_pct", "change_ytd_pct", "rs_rank"
    ]
    for col in numeric_cols:
        if col in out.columns:
            out[col] = pd.to_numeric(out[col], errors="coerce")
    if not out.empty and "label" not in out.columns and "classification" not in out.columns:
        out["label"] = out.apply(classify_stock, axis=1)
    elif "classification" in out.columns and "label" not in out.columns:
        out["label"] = out["classification"]
    return out



def _decision_css(decision: str) -> str:
    return {
        "Ready": "decision-ready",
        "Near Ready": "decision-near-ready",
        "Needs Confirmation": "decision-needs-confirmation",
        "Too Early": "decision-too-early",
        "Avoid": "decision-avoid",
    }.get(decision, "decision-too-early")


def decision_score(row: pd.Series) -> int:
    stage = str(row.get("stage", ""))
    label = str(row.get("label", row.get("classification", "Developing")))
    score = pd.to_numeric(row.get("final_combined_score", row.get("avg_combined_score", row.get("combined_score"))), errors="coerce")
    rank = pd.to_numeric(row.get("current_rank"), errors="coerce")
    rank_change = pd.to_numeric(row.get("rank_change"), errors="coerce")
    rs3 = pd.to_numeric(row.get("rs_3m_pct"), errors="coerce")
    rs6 = pd.to_numeric(row.get("rs_6m_pct"), errors="coerce")

    value = 0.0
    value += {"Stage 1": 18, "Stage 2": 42, "Stage 3": 10, "Stage 4": -12}.get(stage, 12)
    value += {"Strong": 24, "Developing": 14, "Cautious": -6, "Weak": -18}.get(label, 10)
    if pd.notna(score):
        value += min(24, max(0, score * 0.28))
    if pd.notna(rank):
        value += max(0, 18 - min(rank, 18))
    if pd.notna(rank_change) and rank_change > 0:
        value += min(10, rank_change * 1.4)
    if bool(row.get("entered_stage_2", False)):
        value += 12
    if bool(row.get("new_weekly_breakout", False)):
        value += 10
    if bool(row.get("new_daily_breakout", False)):
        value += 8
    if pd.notna(rs3) and rs3 > 0:
        value += 4
    if pd.notna(rs6) and rs6 > 0:
        value += 4
    if stage == "Stage 3":
        value -= 8
    if stage == "Stage 4":
        value -= 15
    return int(max(0, min(100, round(value))))


def decision_state(row: pd.Series) -> str:
    stage = str(row.get("stage", ""))
    label = str(row.get("label", row.get("classification", "Developing")))
    score = decision_score(row)
    rank = pd.to_numeric(row.get("current_rank"), errors="coerce")
    breakout = bool(row.get("new_daily_breakout", False) or row.get("new_weekly_breakout", False))

    if stage == "Stage 4" or label == "Weak":
        return "Avoid"
    if stage == "Stage 2" and label == "Strong" and score >= 72 and (pd.isna(rank) or rank <= 20 or breakout):
        return "Ready"
    if stage == "Stage 2" and score >= 58:
        return "Near Ready"
    if stage == "Stage 1" and score >= 48:
        return "Needs Confirmation"
    if stage == "Stage 3" or label == "Cautious":
        return "Avoid" if score < 32 else "Too Early"
    return "Too Early"


def build_decision_board_sections(combined_df: pd.DataFrame, changes_df: pd.DataFrame) -> dict:
    empty = {"all": pd.DataFrame(), "top": pd.DataFrame()}
    if combined_df.empty:
        return {
            "Top Names that Changed": empty,
            "Ready Now": empty,
            "Improving Fast": empty,
            "Watchlist": empty,
        }

    work = combined_df.copy()
    top_changed, _ = build_today_changes(changes_df.copy(), pd.DataFrame()) if 'build_today_changes' in globals() else (pd.DataFrame(), {})

    if not changes_df.empty and "ticker" in changes_df.columns:
        enrich_cols = [c for c in ["ticker", "entered_stage_2", "new_daily_breakout", "new_weekly_breakout", "rank_change", "combined_score_change"] if c in changes_df.columns]
        if enrich_cols:
            work = work.merge(changes_df[enrich_cols], on="ticker", how="left", suffixes=("", "_chg"))
            for src in ["entered_stage_2", "new_daily_breakout", "new_weekly_breakout", "rank_change", "combined_score_change"]:
                chg = f"{src}_chg"
                if chg in work.columns:
                    if src in work.columns:
                        work[src] = work[src].where(work[src].notna(), work[chg])
                    else:
                        work[src] = work[chg]

    work["decision_score"] = work.apply(decision_score, axis=1)
    work["decision_state"] = work.apply(decision_state, axis=1)

    used = set()

    def unique_top(df: pd.DataFrame, limit: int = 3):
        nonlocal used
        if df.empty:
            return pd.DataFrame()
        temp = df.copy()
        temp = temp[~temp["ticker"].astype(str).isin(used)]
        top = temp.head(limit).copy()
        if not top.empty:
            used.update(top["ticker"].astype(str).tolist())
        return top

    changed_all = top_changed.copy() if not top_changed.empty else pd.DataFrame(columns=work.columns)

    ready_all = work[work["decision_state"] == "Ready"].sort_values(["decision_score", "final_combined_score"], ascending=[False, False]).copy()

    rank_change_series = pd.to_numeric(work.get("rank_change"), errors="coerce").fillna(0)
    improving_mask = rank_change_series.gt(0) | work["decision_state"].isin(["Ready", "Near Ready"])
    if "new_daily_breakout" in work.columns:
        improving_mask = improving_mask | work["new_daily_breakout"].fillna(False)
    if "new_weekly_breakout" in work.columns:
        improving_mask = improving_mask | work["new_weekly_breakout"].fillna(False)
    improving_all = work[improving_mask].sort_values(["decision_score", "final_combined_score"], ascending=[False, False]).copy()

    watchlist_all = work[work["decision_state"].isin(["Near Ready", "Needs Confirmation", "Too Early"])].sort_values(["decision_score", "final_combined_score"], ascending=[False, False]).copy()

    sections = {
        "Top Names that Changed": {"all": changed_all, "top": unique_top(changed_all, 3)},
        "Ready Now": {"all": ready_all, "top": unique_top(ready_all, 3)},
        "Improving Fast": {"all": improving_all, "top": unique_top(improving_all, 3)},
        "Watchlist": {"all": watchlist_all, "top": unique_top(watchlist_all, 3)},
    }
    return sections

def resolve_chart_path(charts_dir: str, ticker: str, suffix: str):
    chart_dir = Path(charts_dir)
    if not chart_dir.exists():
        return None
    ticker = str(ticker).strip()
    raw = ticker.replace(".NS", "")
    candidates = []
    for candidate in {
        ticker, raw,
        ticker.replace(".", "_"), raw.replace(".", "_"),
        ticker.replace("&", "_"), raw.replace("&", "_"),
        ticker.replace("&", "AND"), raw.replace("&", "AND"),
        ticker.replace("&", "and"), raw.replace("&", "and"),
        re.sub(r"[^A-Za-z0-9]+", "_", ticker),
        re.sub(r"[^A-Za-z0-9]+", "_", raw),
        re.sub(r"[^A-Za-z0-9]+", "", ticker),
        re.sub(r"[^A-Za-z0-9]+", "", raw),
    }:
        if candidate:
            candidates.append(candidate + suffix)
    for name in candidates:
        path = chart_dir / name
        if path.exists():
            return path
    raw_key = re.sub(r"[^A-Za-z0-9]+", "", raw).lower()
    for path in chart_dir.glob(f"*{suffix}"):
        stem_key = re.sub(r"[^A-Za-z0-9]+", "", path.stem).lower()
        if raw_key and raw_key in stem_key:
            return path
    return None

@st.cache_data(show_spinner=False)
def load_image_bytes(path: str, mtime_ns: int) -> bytes:
    return Path(path).read_bytes()

def safe_image_bytes(path):
    if not path or not path.exists():
        return None
    return load_image_bytes(str(path), path.stat().st_mtime_ns)

def stage_display(stage: str) -> str:
    return {
        "Stage 1": "Base",
        "Stage 2": "Advancing",
        "Stage 3": "Topping",
        "Stage 4": "Declining",
    }.get(stage, stage or "Unknown")

def trend_text(row: pd.Series) -> str:
    label = str(row.get("label", row.get("classification", "Developing")))
    if label == "Strong":
        return "Strong trend"
    if label == "Weak":
        return "Weak trend"
    if label == "Cautious":
        return "Cautious trend"
    return "Developing trend"

def stage_primary_label(stage: str) -> str:
    return {
        "Stage 1": "Preparing",
        "Stage 2": "Advancing",
        "Stage 3": "Under Pressure",
        "Stage 4": "Weakening",
    }.get(stage, stage or "Unknown")


def stage_short_description(stage: str) -> str:
    return {
        "Stage 1": "Base forming, early structure",
        "Stage 2": "Uptrend with strength",
        "Stage 3": "Trend slowing, mixed signals",
        "Stage 4": "Downtrend, declining structure",
    }.get(stage, "Mixed structure")


def stage_condition_text(row: pd.Series) -> str:
    stage = str(row.get("stage", ""))
    label = str(row.get("label", row.get("classification", "Developing")))
    score = pd.to_numeric(row.get("final_combined_score", row.get("avg_combined_score", row.get("combined_score"))), errors="coerce")
    rank_change = pd.to_numeric(row.get("rank_change"), errors="coerce")
    if stage == "Stage 1":
        return "Improving" if pd.notna(score) and score >= 65 else "Early"
    if stage == "Stage 2":
        if label == "Strong" and pd.notna(rank_change) and rank_change > 0:
            return "Strong"
        if label == "Strong":
            return "Stable"
        return "Slowing" if pd.notna(rank_change) and rank_change < 0 else "Developing"
    if stage == "Stage 3":
        if label == "Cautious" and pd.notna(score) and score >= 65:
            return "Resilient"
        if label == "Weak":
            return "Breaking"
        return "Vulnerable"
    if stage == "Stage 4":
        return "Stabilizing" if pd.notna(rank_change) and rank_change > 0 else "Weak"
    return "Mixed"


def stock_display_label(row: pd.Series) -> str:
    company = str(row.get("Company Name", row.get("ticker", "Stock"))).strip()
    ticker = str(row.get("ticker", "")).replace(".NS", "").strip()
    return f"{company} ({ticker})" if ticker else company


def signal_summary(row: pd.Series) -> str:
    parts = []
    rank_change = pd.to_numeric(row.get("rank_change"), errors="coerce")
    rank = pd.to_numeric(row.get("current_rank"), errors="coerce")

    if pd.notna(rank_change):
        if rank_change > 0:
            parts.append(f"↑ Improving by {int(rank_change)}")
        elif rank_change < 0:
            parts.append(f"↓ Weakening by {abs(int(rank_change))}")

    if bool(row.get("new_weekly_breakout", False)):
        parts.append("⚡ Weekly breakout")
    elif bool(row.get("new_daily_breakout", False)):
        parts.append("⚡ Daily breakout")

    stage = str(row.get("stage", ""))
    if stage == "Stage 1":
        parts.append("⏳ Base forming")
    elif stage == "Stage 2":
        parts.append("🧭 Trend intact")
    elif stage == "Stage 3":
        parts.append("⚠ Under pressure")
    elif stage == "Stage 4":
        parts.append("⚠ Weak structure")

    if pd.notna(rank) and rank <= 10:
        parts.append(f"🏁 Top rank #{int(rank)}")

    industry = str(row.get("Industry", "")).strip()
    if industry:
        parts.append(f"🏭 {industry}")

    return " | ".join(parts[:3]) if parts else "Mixed signals | Monitor structure"


def one_line_explanation(row: pd.Series) -> str:
    label = str(row.get("label", row.get("classification", "Developing")))
    stage = str(row.get("stage", ""))
    industry = str(row.get("Industry", "its industry")).strip() or "its industry"
    rank = pd.to_numeric(row.get("current_rank"), errors="coerce")
    prev_rank = pd.to_numeric(row.get("prev_rank"), errors="coerce")
    rank_change = pd.to_numeric(row.get("rank_change"), errors="coerce")
    rs3 = pd.to_numeric(row.get("rs_3m_pct"), errors="coerce")
    rs6 = pd.to_numeric(row.get("rs_6m_pct"), errors="coerce")
    score = pd.to_numeric(row.get("final_combined_score", row.get("avg_combined_score", row.get("combined_score"))), errors="coerce")

    if stage == "Stage 2" and label == "Strong":
        if pd.notna(rank_change) and rank_change > 0:
            return f"Advancing trend is intact and relative position improved by {int(rank_change)} places."
        if pd.notna(rank) and rank <= 10:
            return "This is a top-ranked Stage 2 leader in the current scan."
        if pd.notna(rs3) and rs3 > 0 and pd.notna(rs6) and rs6 > 0:
            return "Trend and medium-term relative strength are aligned on the upside."
        return "Structure is acting like a leadership candidate rather than a repair candidate."

    if stage == "Stage 1":
        if pd.notna(score) and score >= 65:
            return "Base is tightening, but this is still a watchlist setup until a cleaner Stage 2 transition appears."
        if pd.notna(rs3) and rs3 < 0:
            return "The stock is still repairing after weakness, so the base needs more time."
        return "This looks like a base or repair zone, not a confirmed advancing trend yet."

    if label == "Developing" and stage == "Stage 2":
        return "Trend is positive, but conviction is still lower than the strongest Stage 2 leaders."

    if stage == "Stage 3" or label == "Cautious":
        if pd.notna(prev_rank) and pd.notna(rank) and rank > prev_rank:
            return "Structure is losing momentum and rank is slipping versus peers."
        return "This is a transition or distribution-type structure, so failed rallies are a risk here."

    if stage == "Stage 4":
        return "Declining structure remains dominant, so this is better treated as avoid-for-now."

    if pd.notna(rs3) and pd.notna(rs6) and rs3 < 0 and rs6 < 0:
        return f"Relative strength is weak across timeframes and lagging {industry} peers."

    if pd.notna(score) and score >= 50:
        return "Mixed signals are present, so keep it on a watchlist rather than treating it like leadership."

    return "Current structure is weak or incomplete, so it is not a priority candidate right now."


def guided_workflow_steps(market_label: str) -> list:
    first_step = {
        "Risk On": "Start with Stage 2 names and the strongest industries.",
        "Mixed": "Be selective and focus on top-ranked Stage 2 names or the tightest Stage 1 bases.",
        "Risk Off": "Use the dashboard mainly to track improving bases and avoid forcing Stage 2 labels.",
    }.get(market_label, "Start with the highest-ranked names and confirm on both timeframes.")
    return [
        f"Step 1: Read market tone first. Today the model reads: {market_label}. {first_step}",
        "Step 2: Treat Stage 1 as a base or repair zone, and treat Stage 2 as the primary leadership phase.",
        "Step 3: Prefer improving ranks, stronger industries, and daily-weekly alignment over isolated laggards.",
        "Step 4: Use Portfolio and Alerts tabs to monitor stage transitions over time.",
    ]

def portfolio_assistant(current: pd.DataFrame) -> list:
    if current.empty:
        return ["Portfolio is empty. Add stocks to see a structure summary."]
    total = len(current)
    stage2 = int((current["stage"] == "Stage 2").sum()) if "stage" in current.columns else 0
    weak = int((current["label"].isin(["Weak", "Cautious"])).sum()) if "label" in current.columns else 0
    stage4 = int((current["stage"] == "Stage 4").sum()) if "stage" in current.columns else 0
    msgs = []
    if stage2 >= max(3, math.ceil(total * 0.45)):
        msgs.append(f"{stage2} of {total} stocks are in Stage 2, so the basket has decent trend participation.")
    else:
        msgs.append(f"Only {stage2} of {total} stocks are in Stage 2, so leadership inside the basket is limited.")
    if weak >= max(2, math.ceil(total * 0.4)):
        msgs.append(f"{weak} names are in Weak or Cautious territory, so risk is concentrated in lagging names.")
    else:
        msgs.append("Weak and Cautious names are contained, so the basket is not heavily tilted to laggards.")
    if stage4 > 0:
        msgs.append(f"{stage4} names are already in Stage 4, so these deserve extra review first.")
    top_industries = current["Industry"].dropna().astype(str).value_counts().head(2).index.tolist() if "Industry" in current.columns else []
    if top_industries:
        msgs.append(f"The basket is most exposed to {', '.join(top_industries)}.")
    return msgs

def market_tone(regime_df: pd.DataFrame, combined_df: pd.DataFrame) -> str:
    if not regime_df.empty and "regime_label" in regime_df.columns:
        label = str(regime_df.iloc[0]["regime_label"])
        return {"risk_on": "Risk On", "mixed": "Mixed", "risk_off": "Risk Off"}.get(label, "Mixed")
    strong_count = int((combined_df["label"] == "Strong").sum()) if not combined_df.empty and "label" in combined_df.columns else 0
    if strong_count >= 15:
        return "Risk On"
    if strong_count >= 6:
        return "Mixed"
    return "Risk Off"

def top_industry_text(industry_df: pd.DataFrame, n: int = 3) -> str:
    if industry_df.empty or "Industry" not in industry_df.columns:
        return "Not available"
    return ", ".join(industry_df.head(n)["Industry"].astype(str).tolist())


def company_choices(df: pd.DataFrame):
    if df.empty:
        return {}
    tmp = df.dropna(subset=["Company Name", "ticker"]).copy()
    tmp["Company Name"] = tmp["Company Name"].astype(str).str.strip()
    tmp = tmp.sort_values(["final_combined_score", "Company Name"], ascending=[False, True])
    tmp = tmp.drop_duplicates(subset=["Company Name"], keep="first")
    return dict(zip(tmp["Company Name"], tmp["ticker"]))


def chart_dropdown_options(df: pd.DataFrame):
    if df.empty:
        return {}
    tmp = df.dropna(subset=["Company Name", "ticker"]).copy()
    tmp["display_label"] = tmp.apply(stock_display_label, axis=1)
    tmp = tmp.sort_values(["final_combined_score", "display_label"], ascending=[False, True])
    tmp = tmp.drop_duplicates(subset=["ticker"], keep="first")
    return dict(zip(tmp["display_label"], tmp["ticker"]))


def render_disclosure():
    st.markdown("""
<div class="disclosure">
This dashboard is an informational analytics tool. It shows rule-based stage classifications and market summaries. In this model, Stage 1 means a base or repair zone, not an actionable uptrend by itself. Stage 2 is the primary leadership phase. The tool does not provide personalized investment advice, suitability analysis, buy calls, sell calls, or allocation recommendations.
</div>
""", unsafe_allow_html=True)

def render_summary_card(title: str, value: str, subtitle: str):
    st.markdown(f"""
<div class="hero-card">
  <div class="kicker">{title}</div>
  <div class="big-number">{value}</div>
  <div class="muted">{subtitle}</div>
</div>
""", unsafe_allow_html=True)

def _stage_card_class(stage_raw: str) -> str:
    return {
        "Stage 1": "stage-card-1",
        "Stage 2": "stage-card-2",
        "Stage 3": "stage-card-3",
        "Stage 4": "stage-card-4",
    }.get(stage_raw, "")

def auto_rank(df: pd.DataFrame, preferred_cols: list) -> str:
    if df.empty:
        return "n/a"
    work = df.copy()
    candidate_score_cols = [
        "final_combined_score", "avg_combined_score", "combined_score",
        "final_daily_score", "daily_score", "final_weekly_score", "weekly_score",
        "score"
    ]
    for score_col in candidate_score_cols:
        if score_col in work.columns:
            scores = pd.to_numeric(work[score_col], errors="coerce")
            if scores.notna().any():
                val = scores.rank(method="min", ascending=False).iloc[0]
                if pd.notna(val):
                    return str(int(val))
    return "n/a"

def rank_lookup(df: pd.DataFrame, ticker: str, preferred_cols: list) -> str:
    if df.empty:
        return "n/a"

    work = df.copy()
    ticker_col = None
    for cand in ["ticker", "Ticker", "symbol", "Symbol"]:
        if cand in work.columns:
            ticker_col = cand
            break

    if ticker_col is None:
        return auto_rank(work, preferred_cols)

    work[ticker_col] = work[ticker_col].astype(str).str.strip()
    ticker_norm = str(ticker).strip()

    match = work[work[ticker_col] == ticker_norm]
    if match.empty:
        match = work[work[ticker_col].str.replace(".NS", "", regex=False) == ticker_norm.replace(".NS", "")]

    if match.empty:
        return auto_rank(work, preferred_cols)

    row = match.iloc[0]
    search_cols = preferred_cols + [
        "current_rank", "rank", "rs_rank", "daily_rank", "weekly_rank",
        "final_rank", "combined_rank", "stock_rank"
    ]
    for col in search_cols:
        if col in match.columns:
            val = pd.to_numeric(row.get(col), errors="coerce")
            if pd.notna(val):
                return str(int(val))

    return auto_rank(match, preferred_cols)




def build_simple_rank_map(df: pd.DataFrame) -> dict:
    if df.empty:
        return {}
    ticker_col = None
    for cand in ["ticker", "Ticker", "symbol", "Symbol"]:
        if cand in df.columns:
            ticker_col = cand
            break
    if ticker_col is None:
        return {}
    rank_col = None
    for cand in ["current_rank", "rank", "rs_rank", "daily_rank", "weekly_rank", "final_rank", "combined_rank", "stock_rank"]:
        if cand in df.columns:
            rank_col = cand
            break
    if rank_col is None:
        return {}
    temp = df[[ticker_col, rank_col]].copy()
    temp[ticker_col] = temp[ticker_col].astype(str).str.strip()
    temp[rank_col] = pd.to_numeric(temp[rank_col], errors="coerce")
    temp = temp.dropna(subset=[ticker_col, rank_col]).drop_duplicates(subset=[ticker_col], keep="first")
    out = {}
    for _, r in temp.iterrows():
        t = str(r[ticker_col]).strip()
        out[t] = str(int(r[rank_col]))
        out[t.replace(".NS", "")] = str(int(r[rank_col]))
    return out

def card(row: pd.Series, pct=None, use_stage_color=False, show_change_text: str = "", stock_rank: str = "n/a", show_quick_read: bool = False):
    label = row.get("label", row.get("classification", "Developing"))
    style = LABELS.get(label, LABELS["Developing"])
    stage_raw = str(row.get("stage", "Unknown"))
    stage_label = stage_primary_label(stage_raw)
    stage_desc = stage_short_description(stage_raw)
    stage_condition = stage_condition_text(row)
    display_name = stock_display_label(row)
    decision = decision_state(row)
    dscore = decision_score(row)
    signals = signal_summary(row)
    classes = []
    if use_stage_color:
        stage_cls = _stage_card_class(stage_raw)
        if stage_cls:
            classes.append(stage_cls)
    change_html = ""
    if pct is not None:
        cls = "change-badge-up" if pct > 0 else "change-badge-down"
        change_html = f"<div class='{cls}'>{pct:+.2f}%</div>"
    extra_change = f"<div class='change-text'>{show_change_text}</div>" if show_change_text else ""
    class_attr = " ".join(classes)
    status_html = f"<div class='status-pill {style['css']}'>{label}</div>"
    decision_html = f"<div class='decision-pill {_decision_css(decision)}'>Decision: {decision} · Score {dscore}</div>"
    rank_html = f"<div class='rank-text'>Rank {stock_rank}</div>"
    html = (
        f"<div class='stock-card {class_attr}'>"
        f"<div style='display:flex; justify-content:space-between; align-items:flex-start; gap:0.55rem;'>"
        f"<div style='min-width:0;'>"
        f"<div class='stock-title'>{display_name}</div>"
        f"<div class='meta-line'>{stage_raw} • {stage_label} • {stage_condition}</div>"
        f"<div class='stock-subtitle'>{stage_desc}</div>"
        f"{decision_html}"
        f"<div class='signal-line'>{signals}</div>"
        f"</div>"
        f"<div style='display:flex; flex-direction:column; align-items:flex-end; gap:0.05rem;'>"
        f"{status_html}{rank_html}{change_html}"
        f"</div>"
        f"</div>"
        f"{extra_change}"
        f"</div>"
    )
    st.markdown(html, unsafe_allow_html=True)

def stage_count_summary(combined_df: pd.DataFrame):
    counts = combined_df["stage"].value_counts() if "stage" in combined_df.columns else pd.Series(dtype=int)
    return {
        "Stage 1": int(counts.get("Stage 1", 0)),
        "Stage 2": int(counts.get("Stage 2", 0)),
        "Stage 3": int(counts.get("Stage 3", 0)),
        "Stage 4": int(counts.get("Stage 4", 0)),
    }

def stage2_count_by_industry(combined_df: pd.DataFrame) -> pd.DataFrame:
    if combined_df.empty or "Industry" not in combined_df.columns or "stage" not in combined_df.columns:
        return pd.DataFrame(columns=["Industry", "Stage 2 Stocks"])
    return combined_df.groupby("Industry", dropna=True)["stage"].apply(lambda s: int((s == "Stage 2").sum())).reset_index(name="Stage 2 Stocks")

def build_today_changes(changes_df: pd.DataFrame, industry_changes_df: pd.DataFrame):
    summary = {"New Strong": 0, "Entered Stage 2": 0, "New Breakouts": 0}
    if changes_df.empty:
        return pd.DataFrame(), summary
    df = changes_df.copy()
    if "label" not in df.columns:
        df["label"] = df.apply(classify_stock, axis=1)

    if "entered_stage_2" in df.columns:
        summary["Entered Stage 2"] = int(df["entered_stage_2"].fillna(False).sum())
    if "new_daily_breakout" in df.columns:
        summary["New Breakouts"] += int(df["new_daily_breakout"].fillna(False).sum())
    if "new_weekly_breakout" in df.columns:
        summary["New Breakouts"] += int(df["new_weekly_breakout"].fillna(False).sum())

    df["change_priority_score"] = 0.0
    weights = {"new_top_10": 60, "new_top_20": 40, "entered_stage_2": 90, "new_daily_breakout": 70, "new_weekly_breakout": 80}
    for col, wt in weights.items():
        if col in df.columns:
            df["change_priority_score"] += df[col].fillna(False).astype(int) * wt
    if "rank_change" in df.columns:
        df["change_priority_score"] += pd.to_numeric(df["rank_change"], errors="coerce").clip(lower=0, upper=20).fillna(0) * 2
    if "combined_score_change" in df.columns:
        df["change_priority_score"] += pd.to_numeric(df["combined_score_change"], errors="coerce").clip(lower=0).fillna(0) * 3

    entered_strong = (df["label"] == "Strong") & (df["change_priority_score"] >= 60)
    summary["New Strong"] = int(entered_strong.sum())
    df["change_priority_score"] += entered_strong.astype(int) * 100

    def what_changed(row):
        parts = []
        if bool(row.get("entered_stage_2", False)):
            parts.append("Entered Stage 2")
        if bool(row.get("new_weekly_breakout", False)):
            parts.append("Weekly breakout")
        if bool(row.get("new_daily_breakout", False)):
            parts.append("Daily breakout")
        if bool(row.get("new_top_10", False)):
            parts.append("Entered Top 10")
        elif bool(row.get("new_top_20", False)):
            parts.append("Entered Top 20")
        rc = pd.to_numeric(row.get("rank_change"), errors="coerce")
        if pd.notna(rc) and rc > 0:
            parts.append(f"Rank improved by {int(rc)}")
        return ", ".join(parts[:3]) if parts else "Score improved"

    df["what_changed"] = df.apply(what_changed, axis=1)
    top_changed = df.sort_values(["change_priority_score", "final_combined_score"], ascending=[False, False]).head(5).copy()
    return top_changed, summary

outdir = "outputs"
help_image_path = "market_phases_reference.png"

combined = ensure_label(safe_read(f"{outdir}/vcp_combined_ranked.csv"))
daily_df = ensure_label(safe_read(f"{outdir}/vcp_daily_ranked.csv"))
weekly_df = ensure_label(safe_read(f"{outdir}/vcp_weekly_ranked.csv"))
industry = ensure_label(safe_read(f"{outdir}/industry_strength.csv"))
changes = ensure_label(safe_read(f"{outdir}/stock_changes.csv"))
industry_changes = ensure_label(safe_read(f"{outdir}/industry_changes.csv"))
moves = ensure_label(safe_read(f"{outdir}/stock_price_moves.csv"))
top_movers = ensure_label(safe_read(f"{outdir}/top_movers.csv"))
if top_movers.empty:
    top_movers = moves.copy()
regime = safe_read(f"{outdir}/market_regime.csv")

if combined.empty:
    st.error("No data found in the default outputs folder.")
    st.info("Create an outputs folder beside this file and keep the generated CSV files there.")
    st.stop()

for df_name in ["combined", "daily_df", "weekly_df", "changes", "moves", "top_movers"]:
    _df = locals().get(df_name)
    if _df is not None and not _df.empty:
        if "decision_score" not in _df.columns:
            _df["decision_score"] = _df.apply(decision_score, axis=1)
        if "decision_state" not in _df.columns:
            _df["decision_state"] = _df.apply(decision_state, axis=1)


daily_dir = f"{outdir}/charts/daily"
weekly_dir = f"{outdir}/charts/weekly"
company_map = company_choices(combined)
chart_choice_map = chart_dropdown_options(combined)
top_changed_df, changes_summary = build_today_changes(changes, industry_changes)
changed_tickers = set(top_changed_df["ticker"].dropna().tolist()) if not top_changed_df.empty and "ticker" in top_changed_df.columns else set()
board_sections = build_decision_board_sections(combined, changes)
def build_alert_candidates(combined_df: pd.DataFrame, changes_df: pd.DataFrame) -> pd.DataFrame:
    if combined_df.empty:
        return pd.DataFrame()
    alerts = []
    changes_lookup = changes_df.copy() if not changes_df.empty else pd.DataFrame()
    if not changes_lookup.empty and "ticker" in changes_lookup.columns:
        changes_lookup["ticker"] = changes_lookup["ticker"].astype(str).str.strip()
        changes_lookup = changes_lookup.set_index("ticker", drop=False)

    for _, row in combined_df.iterrows():
        ticker = str(row.get("ticker", "")).strip()
        cr = changes_lookup.loc[ticker] if (not changes_lookup.empty and ticker in changes_lookup.index) else None
        alert_type = ""
        reason = ""
        if cr is not None and bool(cr.get("entered_stage_2", False)):
            alert_type = "Entered Stage 2"
            reason = "Trend moved into the uptrend phase."
        elif cr is not None and bool(cr.get("new_weekly_breakout", False)):
            alert_type = "Weekly breakout"
            reason = "Weekly structure triggered a fresh breakout event."
        elif cr is not None and bool(cr.get("new_daily_breakout", False)):
            alert_type = "Daily breakout"
            reason = "Daily structure triggered a fresh breakout event."
        else:
            rank_change = pd.to_numeric(row.get("rank_change"), errors="coerce")
            if pd.notna(rank_change) and rank_change >= 5:
                alert_type = "Rank improvement"
                reason = f"Rank improved by {int(rank_change)} places."

        if alert_type:
            item = row.copy()
            item["alert_type"] = alert_type
            item["alert_reason"] = reason
            alerts.append(item)

    if not alerts:
        return pd.DataFrame()
    out = pd.DataFrame(alerts)
    if "final_combined_score" in out.columns:
        out = out.sort_values(["final_combined_score", "alert_type"], ascending=[False, True])
    return out.head(20)


alert_candidates = build_alert_candidates(combined, changes)
stage_counts = stage_count_summary(combined)
TOP_MOVER_RANK_MAP = build_simple_rank_map(top_movers)

def dedupe_names(names: list, limit: int = MAX_PORTFOLIO_STOCKS) -> list:
    out = []
    seen = set()
    for name in names:
        if pd.isna(name):
            continue
        name = str(name).strip()
        if not name or name in seen:
            continue
        seen.add(name)
        out.append(name)
        if len(out) >= limit:
            break
    return out

def get_stock_rank(ticker: str) -> str:
    t = str(ticker).strip()
    return TOP_MOVER_RANK_MAP.get(t) or TOP_MOVER_RANK_MAP.get(t.replace(".NS","")) or rank_lookup(top_movers, ticker, ["current_rank"])

def get_display_stock_rank(ticker: str) -> str:
    return get_stock_rank(ticker)

def get_industry_portfolio_options(industry_df: pd.DataFrame, combined_df: pd.DataFrame, limit: int = 21) -> list:
    if not industry_df.empty and "Industry" in industry_df.columns:
        view = industry_df.copy()
        sort_col = None
        ascending = False
        for candidate in ["avg_combined_score", "final_combined_score"]:
            if candidate in view.columns:
                sort_col = candidate
                ascending = False
                break
        if sort_col is None:
            for candidate in ["current_rank", "rs_rank"]:
                if candidate in view.columns:
                    sort_col = candidate
                    ascending = True
                    break
        if sort_col is not None:
            view[sort_col] = pd.to_numeric(view[sort_col], errors="coerce")
            view = view.sort_values(sort_col, ascending=ascending, na_position="last")
        industries = view["Industry"].dropna().astype(str).str.strip().tolist()
        return dedupe_names(industries, limit=limit)

    if "Industry" not in combined_df.columns:
        return []

    grouped = (combined_df.dropna(subset=["Industry"])
               .groupby("Industry", as_index=False)["final_combined_score"]
               .mean()
               .sort_values("final_combined_score", ascending=False))
    industries = grouped["Industry"].astype(str).str.strip().tolist()
    return dedupe_names(industries, limit=limit)

INDUSTRY_PORTFOLIOS = get_industry_portfolio_options(industry, combined, limit=21)


def get_prebuilt_portfolio(name: str, combined: pd.DataFrame, changes: pd.DataFrame) -> list:
    ranked = combined.sort_values("final_combined_score", ascending=False).copy()
    if "decision_state" not in ranked.columns:
        ranked["decision_state"] = ranked.apply(decision_state, axis=1)
    names = []
    if name == "Top 15":
        names = ranked.head(15)["Company Name"].dropna().tolist()
    elif name == "New Breakouts":
        tmp = changes.copy()
        mask = pd.Series(False, index=tmp.index)
        if "new_daily_breakout" in tmp.columns:
            mask = mask | tmp["new_daily_breakout"].fillna(False)
        if "new_weekly_breakout" in tmp.columns:
            mask = mask | tmp["new_weekly_breakout"].fillna(False)
        names = tmp.loc[mask, "Company Name"].dropna().tolist()
    elif name == "New Strong":
        tmp = changes.copy()
        if "label" not in tmp.columns:
            tmp["label"] = tmp.apply(classify_stock, axis=1)
        names = tmp.loc[tmp["label"] == "Strong", "Company Name"].dropna().tolist()
    elif name == "Ready Now":
        names = ranked.loc[ranked["decision_state"] == "Ready", "Company Name"].dropna().tolist()
    elif name == "Improving Fast":
        improving_mask = pd.to_numeric(ranked.get("rank_change"), errors="coerce").fillna(0).gt(0)
        if "new_daily_breakout" in ranked.columns:
            improving_mask = improving_mask | ranked["new_daily_breakout"].fillna(False)
        if "new_weekly_breakout" in ranked.columns:
            improving_mask = improving_mask | ranked["new_weekly_breakout"].fillna(False)
        names = ranked.loc[improving_mask, "Company Name"].dropna().tolist()
    elif name == "Watchlist":
        names = ranked.loc[ranked["decision_state"].isin(["Near Ready", "Needs Confirmation", "Too Early"]), "Company Name"].dropna().tolist()
    elif name == "Avoid":
        names = ranked.loc[ranked["decision_state"] == "Avoid", "Company Name"].dropna().tolist()
    elif name in {"Stage 1", "Stage 2", "Stage 3", "Stage 4"}:
        names = combined.loc[combined["stage"] == name, "Company Name"].dropna().tolist()
    elif name == "Cautious":
        names = combined.loc[combined["label"] == "Cautious", "Company Name"].dropna().tolist()
    elif name == "Weak":
        names = combined.loc[combined["label"] == "Weak", "Company Name"].dropna().tolist()
    elif name == "Strong":
        names = combined.loc[combined["label"] == "Strong", "Company Name"].dropna().tolist()
    elif name in INDUSTRY_PORTFOLIOS:
        names = ranked.loc[ranked["Industry"].astype(str).str.strip() == name, "Company Name"].dropna().tolist()
    return dedupe_names(names, limit=MAX_PORTFOLIO_STOCKS)


st.title("Market Structure Radar")
view_mode = st.radio("View mode", ["Beginner", "Pro"], horizontal=True, index=0)
show_pro_quick_read = False
if view_mode == "Beginner":
    tab_names = ["Decision Board", "Charts", "Movers", "Portfolio", "How to Use", "Disclaimer"]
else:
    tab_names = ["Decision Board", "Charts", "Movers", "Market", "Portfolio", "Alerts", "Advanced", "How to Use", "Disclaimer"]
def render_stock_detail(row):
    """Render a readable stock detail panel below the selected stock card."""
    try:
        stock_name = escape(str(row.get("Company Name", row.get("stock_name", "")) or ""))
        ticker = escape(str(row.get("ticker", "") or ""))
        stage = escape(str(row.get("stage", "") or ""))
        decision = escape(decision_state(row) if "decision_state" in globals() else "")
        qualifier = escape(stage_condition_text(row) if "stage_condition_text" in globals() else "")
        try:
            dscore = int(round(decision_score(row))) if "decision_score" in globals() else None
        except Exception:
            dscore = None

        rank_val = None
        for key in ["current_rank", "rank", "final_rank"]:
            if key in row and str(row.get(key)).strip() not in ("", "nan", "None"):
                rank_val = row.get(key)
                break

        why_parts = []
        if "rank_change" in row and str(row.get("rank_change")).strip() not in ("", "nan", "None"):
            try:
                rc = int(float(row.get("rank_change", 0)))
                if rc > 0:
                    why_parts.append(f"Rank improved by {rc}")
                elif rc < 0:
                    why_parts.append(f"Rank slipped by {abs(rc)}")
            except Exception:
                pass
        if "industry_rank" in row and str(row.get("industry_rank")).strip() not in ("", "nan", "None"):
            why_parts.append(f"Industry rank {row.get('industry_rank')}")
        if stage == "Stage 2":
            why_parts.append("Uptrend structure remains in focus")
        elif stage == "Stage 1":
            why_parts.append("Base is still forming")
        elif stage == "Stage 3":
            why_parts.append("Trend is under pressure")
        elif stage == "Stage 4":
            why_parts.append("Structure remains weak")
        why_now = escape(" • ".join(why_parts[:3]) if why_parts else "Review current structure and relative position.")

        improved_parts = []
        for key, label in [("breakout", "Breakout present"), ("weekly_breakout", "Weekly breakout"), ("daily_breakout", "Daily breakout")]:
            if key in row:
                val = str(row.get(key)).lower()
                if val in ("1", "true", "yes", "y"):
                    improved_parts.append(label)
        for key, label in [("rs_3m_pct", "3M RS"), ("rs_6m_pct", "6M RS")]:
            if key in row:
                try:
                    if float(row.get(key, 0)) > 0:
                        improved_parts.append(f"{label} positive")
                except Exception:
                    pass
        what_improved = escape(" • ".join(improved_parts[:3]) if improved_parts else "No major fresh improvement signal detected.")

        if stage == "Stage 2":
            monitor = "Watch for rank stability, follow-through, and support holding."
        elif stage == "Stage 1":
            monitor = "Watch for tighter structure and stronger confirmation."
        elif stage == "Stage 3":
            monitor = "Watch whether strength stabilizes or breakdown risk increases."
        else:
            monitor = "Watch for any improvement in structure before prioritizing."
        monitor = escape(monitor)

        score_html = f"<div style='font-size:0.92rem;color:#cbd5e1;margin-top:0.2rem;'>Decision Score: <b>{dscore}</b></div>" if dscore is not None else ""
        rank_html = f"<div style='font-size:0.92rem;color:#cbd5e1;margin-top:0.2rem;'>Rank: <b>{escape(str(rank_val))}</b></div>" if rank_val is not None else ""
        qualifier_html = f" • {qualifier}" if qualifier else ""

        html = f"""
        <div style="margin-top:0.7rem;padding:0.9rem;border-radius:16px;background:#0b1220;border:1px solid rgba(148,163,184,0.25);">
            <div style="font-size:1.05rem;font-weight:700;color:#f8fafc;">{stock_name} ({ticker})</div>
            <div style="font-size:0.95rem;color:#93c5fd;margin-top:0.2rem;">{decision}</div>
            <div style="font-size:0.92rem;color:#e2e8f0;margin-top:0.15rem;">{stage}{qualifier_html}</div>
            {score_html}
            {rank_html}
            <div style="margin-top:0.75rem;padding:0.8rem;border-radius:12px;background:#111827;">
                <div style="font-size:0.84rem;font-weight:700;color:#93c5fd;">Why it matters now</div>
                <div style="font-size:0.98rem;line-height:1.5;color:#f8fafc;margin-top:0.25rem;">{why_now}</div>
            </div>
            <div style="margin-top:0.55rem;padding:0.8rem;border-radius:12px;background:#0f172a;">
                <div style="font-size:0.84rem;font-weight:700;color:#86efac;">What improved</div>
                <div style="font-size:0.98rem;line-height:1.5;color:#f8fafc;margin-top:0.25rem;">{what_improved}</div>
            </div>
            <div style="margin-top:0.55rem;padding:0.8rem;border-radius:12px;background:#1f2937;">
                <div style="font-size:0.84rem;font-weight:700;color:#fcd34d;">What to monitor next</div>
                <div style="font-size:0.98rem;line-height:1.5;color:#f8fafc;margin-top:0.25rem;">{monitor}</div>
            </div>
        </div>
        """
        st.markdown(html, unsafe_allow_html=True)
    except Exception as e:
        st.info(f"Unable to render stock detail: {e}")


tabs = st.tabs(tab_names)

# Decision Board
with tabs[0]:
    current_market_tone = market_tone(regime, combined)
    st.markdown("### Decision Board")
    c1, c2, c3 = st.columns(3)
    with c1:
        render_summary_card("Market tone", current_market_tone, "Use this before reviewing any stock")
    with c2:
        render_summary_card("New Strong", str(changes_summary["New Strong"]), "Stage 2 leaders improving materially")
    with c3:
        render_summary_card("Top industries", top_industry_text(industry), "Industries that are leading currently")
    for title in ["Top Names that Changed", "Ready Now", "Improving Fast", "Watchlist"]:
        section = board_sections.get(title, {"all": pd.DataFrame(), "top": pd.DataFrame()})
        total_ct = len(section["all"])
        st.markdown(f"#### {title} (Top 3 out of {total_ct})")
        if total_ct == 0:
            st.info(f"No stocks in {title.lower()} right now.")
        else:
            cols = st.columns(3)
            for col, (_, r) in zip(cols, section["top"].iterrows()):
                with col:
                    stock_rank = get_stock_rank(r["ticker"])
                    extra = ""
                    if title == "Top Names that Changed":
                        what_changed = str(r.get("what_changed", "")).strip()
                        if what_changed:
                            extra = f"What changed: {what_changed}"
                    card(r, use_stage_color=True, show_change_text=extra, stock_rank=stock_rank)
    st.divider()
    st.markdown("#### Guided workflow")
    workflow_cols = st.columns(len(guided_workflow_steps(current_market_tone)))
    for col, step_text in zip(workflow_cols, guided_workflow_steps(current_market_tone)):
        with col:
            st.markdown(f'''<div class="assist-box"><div class="assist-text">{step_text}</div></div>''', unsafe_allow_html=True)
    render_disclosure()

# Charts
with tabs[1]:
    ranked = combined.sort_values("final_combined_score", ascending=False).reset_index(drop=True).copy()
    ticker_list = ranked["ticker"].dropna().astype(str).tolist()
    if "selected_stock_index" not in st.session_state:
        st.session_state["selected_stock_index"] = 0
    st.session_state["selected_stock_index"] = max(0, min(st.session_state["selected_stock_index"], len(ticker_list) - 1))
    current_ticker = ticker_list[st.session_state["selected_stock_index"]] if ticker_list else None
    selected_display = st.selectbox("Select stock", options=[None] + list(chart_choice_map.keys()), index=0, placeholder="Type stock name or ticker")
    if selected_display:
        selected_ticker = chart_choice_map[selected_display]
        selected_index = ticker_list.index(selected_ticker)
        if selected_index != st.session_state["selected_stock_index"]:
            st.session_state["selected_stock_index"] = selected_index
            st.rerun()

    row = ranked.iloc[st.session_state["selected_stock_index"]]
    ticker_short = str(row["ticker"]).replace(".NS", "")
    dpath = resolve_chart_path(daily_dir, row["ticker"], "_daily.png")
    wpath = resolve_chart_path(weekly_dir, row["ticker"], "_weekly.png")
    a, b = st.columns(2)
    with a:
        daily_rank = get_display_stock_rank(row["ticker"])
        st.markdown(f"#### Daily * {ticker_short} * {row.get('stage', '')} * Daily Rank {daily_rank}")
        if dpath:
            st.image(safe_image_bytes(dpath), use_container_width=True)
        else:
            st.info("Daily chart not available.")
    with b:
        weekly_rank = get_display_stock_rank(row["ticker"])
        st.markdown(f"#### Weekly * {ticker_short} * {row.get('stage', '')} * Weekly Rank {weekly_rank}")
        if wpath:
            st.image(safe_image_bytes(wpath), use_container_width=True)
        else:
            st.info("Weekly chart not available.")

    nav1, nav2 = st.columns(2)
    with nav1:
        prev2 = st.button("Previous", use_container_width=True, disabled=(st.session_state["selected_stock_index"] == 0), key=f"charts_prev_{st.session_state['selected_stock_index']}")
    with nav2:
        next2 = st.button("Next", use_container_width=True, disabled=(st.session_state["selected_stock_index"] >= len(ticker_list) - 1), key=f"charts_next_{st.session_state['selected_stock_index']}")
    if prev2 and st.session_state["selected_stock_index"] > 0:
        st.session_state["selected_stock_index"] -= 1
        st.rerun()
    if next2 and st.session_state["selected_stock_index"] < len(ticker_list) - 1:
        st.session_state["selected_stock_index"] += 1
        st.rerun()

    st.markdown("#### Selected stock")
    stock_rank = get_stock_rank(row["ticker"])
    card(row, use_stage_color=True, stock_rank=stock_rank)
    render_stock_detail(row)

    st.divider()
    st.markdown("### Browse more stocks")
    for _, r in ranked.head(20).iterrows():
        stock_rank = get_stock_rank(r["ticker"])
        card(r, use_stage_color=True, stock_rank=stock_rank)
    render_disclosure()


# Movers
# Movers
with tabs[2]:
    st.markdown("### Movers")
    if moves.empty:
        st.info("Price move data not found yet.")
    else:
        window_map = {"1 Day":"change_1d_pct","1 Week":"change_1w_pct","1 Month":"change_1m_pct","YTD":"change_ytd_pct"}
        selected = st.radio("Move window", list(window_map.keys()), horizontal=True, index=0)
        col = window_map[selected]
        mv = moves.copy()
        mv[col] = pd.to_numeric(mv[col], errors="coerce")
        mv = mv.dropna(subset=[col])
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f"#### Biggest upward moves • {selected}")
            for _, r in mv.sort_values([col, "final_combined_score"], ascending=[False, False]).head(10).iterrows():
                stock_rank = get_stock_rank(r["ticker"])
                card(r, pct=float(r[col]), use_stage_color=True, stock_rank=stock_rank)
        with c2:
            st.markdown(f"#### Major downward moves • {selected}")
            for _, r in mv.sort_values([col, "final_combined_score"], ascending=[True, False]).head(10).iterrows():
                stock_rank = get_stock_rank(r["ticker"])
                card(r, pct=float(r[col]), use_stage_color=True, stock_rank=stock_rank)
    render_disclosure()

# Market only in Pro
if view_mode == "Pro":
    with tabs[3]:
        st.markdown("### Market")
        c1, c2, c3, c4 = st.columns(4)
        with c1: render_summary_card("Stage 1", str(stage_counts["Stage 1"]), "Base / repair")
        with c2: render_summary_card("Stage 2", str(stage_counts["Stage 2"]), "Advancing trend")
        with c3: render_summary_card("Stage 3", str(stage_counts["Stage 3"]), "Under pressure")
        with c4: render_summary_card("Stage 4", str(stage_counts["Stage 4"]), "Weakening trend")

        if industry.empty:
            st.info("Industry data not available.")
        else:
            view = industry.copy()
            stage2 = stage2_count_by_industry(combined)
            if "Industry" in view.columns:
                view = view.merge(stage2, on="Industry", how="left")
            sort_col = None
            for candidate in ["avg_combined_score","current_rank","rs_rank"]:
                if candidate in view.columns:
                    sort_col = candidate
                    break
            if sort_col is not None:
                view[sort_col] = pd.to_numeric(view[sort_col], errors="coerce")
                view = view.sort_values(sort_col, ascending=(sort_col!="avg_combined_score"), na_position="last").reset_index(drop=True)
                view["Rank"] = range(1, len(view)+1)
            if "Stage 2 Stocks" in view.columns:
                view["Stage 2 Stocks"] = view["Stage 2 Stocks"].fillna(0).astype(int)
            left, right = st.columns(2)
            with left:
                st.markdown("#### Industry strength")
                st.dataframe(view[[c for c in ["Industry","Rank","Stage 2 Stocks"] if c in view.columns]], use_container_width=True, hide_index=True, height=520)
            with right:
                st.markdown("#### Industry changes")
                if industry_changes.empty:
                    st.info("Industry changes data not available.")
                else:
                    cols = [c for c in ["Industry","current_rank","prev_rank","rank_change"] if c in industry_changes.columns]
                    renamed = industry_changes[cols].rename(columns={"current_rank":"Current Rank","prev_rank":"Previous Rank","rank_change":"Rank Change"})
                    st.dataframe(renamed, use_container_width=True, hide_index=True, height=520)
        render_disclosure()

# Portfolio
portfolio_tab_index = 3 if view_mode == "Beginner" else 4
with tabs[portfolio_tab_index]:
    if "portfolio_names" not in st.session_state:
        st.session_state["portfolio_names"] = []
    if "custom_portfolio_names" not in st.session_state:
        st.session_state["custom_portfolio_names"] = []
    if "portfolio_chart_index" not in st.session_state:
        st.session_state["portfolio_chart_index"] = 0
    if "portfolio_selection" not in st.session_state:
        st.session_state["portfolio_selection"] = "Custom"
    if "portfolio_selection_prev" not in st.session_state:
        st.session_state["portfolio_selection_prev"] = st.session_state["portfolio_selection"]

    portfolio_options = ["Custom", "Top 15", "New Breakouts", "New Strong", "Ready Now", "Improving Fast", "Watchlist", "Avoid", "Strong", "Cautious", "Weak", "Stage 1", "Stage 2", "Stage 3", "Stage 4"] + INDUSTRY_PORTFOLIOS
    selected_portfolio = st.selectbox("Portfolio selection", portfolio_options, key="portfolio_selection")

    previous_portfolio = st.session_state.get("portfolio_selection_prev", "Custom")
    if selected_portfolio != previous_portfolio:
        if previous_portfolio == "Custom":
            st.session_state["custom_portfolio_names"] = dedupe_names(st.session_state["portfolio_names"], limit=MAX_PORTFOLIO_STOCKS)
        if selected_portfolio == "Custom":
            st.session_state["portfolio_names"] = dedupe_names(st.session_state.get("custom_portfolio_names", []), limit=MAX_PORTFOLIO_STOCKS)
        else:
            st.session_state["portfolio_names"] = get_prebuilt_portfolio(selected_portfolio, combined, changes)
        st.session_state["portfolio_chart_index"] = 0
        st.session_state["portfolio_selection_prev"] = selected_portfolio

    st.session_state["portfolio_names"] = dedupe_names(st.session_state["portfolio_names"], limit=MAX_PORTFOLIO_STOCKS)
    if selected_portfolio == "Custom":
        st.session_state["custom_portfolio_names"] = dedupe_names(st.session_state["portfolio_names"], limit=MAX_PORTFOLIO_STOCKS)

    available = [label for label in chart_choice_map.keys() if label.split(" (")[0] not in st.session_state["portfolio_names"]]
    portfolio_full = len(st.session_state["portfolio_names"]) >= MAX_PORTFOLIO_STOCKS
    selected_to_add = st.selectbox("Add stock", options=[None] + list(chart_choice_map.keys()), index=0, placeholder="Type stock name or ticker", key="portfolio_add_name", disabled=portfolio_full)
    if portfolio_full:
        st.warning(f"Portfolio is limited to {MAX_PORTFOLIO_STOCKS} stocks.")
    if st.button("Add to portfolio", use_container_width=True, key="portfolio_add_btn", disabled=portfolio_full) and selected_to_add:
        selected_name = selected_to_add.rsplit(" (", 1)[0]
        st.session_state["portfolio_names"] = dedupe_names(st.session_state["portfolio_names"] + [selected_name], limit=MAX_PORTFOLIO_STOCKS)
        if selected_portfolio == "Custom":
            st.session_state["custom_portfolio_names"] = dedupe_names(st.session_state["portfolio_names"], limit=MAX_PORTFOLIO_STOCKS)
        if st.session_state["portfolio_chart_index"] >= len(st.session_state["portfolio_names"]):
            st.session_state["portfolio_chart_index"] = max(0, len(st.session_state["portfolio_names"]) - 1)
        st.rerun()

    if not st.session_state["portfolio_names"]:
        st.info("No stocks added yet.")
    else:
        current = combined[combined["Company Name"].isin(st.session_state["portfolio_names"])].copy().sort_values("final_combined_score", ascending=False).head(MAX_PORTFOLIO_STOCKS).copy()
        p_stage_counts = current["stage"].value_counts() if "stage" in current.columns else pd.Series(dtype=int)
        c1, c2, c3, c4, c5 = st.columns(5)
        with c1: render_summary_card("Total stocks", str(len(current)), "Stocks currently added")
        with c2: render_summary_card("Stage 1", str(int(p_stage_counts.get("Stage 1", 0))), "Preparing")
        with c3: render_summary_card("Stage 2", str(int(p_stage_counts.get("Stage 2", 0))), "Advancing")
        with c4: render_summary_card("Stage 3", str(int(p_stage_counts.get("Stage 3", 0))), "Under pressure")
        with c5: render_summary_card("Stage 4", str(int(p_stage_counts.get("Stage 4", 0))), "Weakening")

        st.markdown("### Portfolio assistant")
        health_title, health_text = portfolio_health_summary(current)
        st.markdown(f'<div class="assist-box"><div class="assist-title">Portfolio health: {health_title}</div><div class="assist-text">{health_text}</div></div>', unsafe_allow_html=True)
        for msg in portfolio_assistant(current):
            st.markdown(f'''<div class="assist-box"><div class="assist-text">{msg}</div></div>''', unsafe_allow_html=True)

        st.divider()
        for _, r in current.sort_values("final_combined_score", ascending=False).iterrows():
            stock_rank = get_stock_rank(r["ticker"])
            card(r, use_stage_color=True, stock_rank=stock_rank)

        removable = [""] + sorted(st.session_state["portfolio_names"])
        selected_remove = st.selectbox("Remove stock", removable, key="portfolio_remove_name")
        if st.button("Remove from portfolio", use_container_width=True, key="portfolio_remove_btn") and selected_remove:
            st.session_state["portfolio_names"] = [x for x in st.session_state["portfolio_names"] if x != selected_remove]
            if selected_portfolio == "Custom":
                st.session_state["custom_portfolio_names"] = dedupe_names(st.session_state["portfolio_names"], limit=MAX_PORTFOLIO_STOCKS)
            st.session_state["portfolio_chart_index"] = min(st.session_state["portfolio_chart_index"], max(0, len(st.session_state["portfolio_names"]) - 1))
            st.rerun()

        portfolio_ordered = current.sort_values("final_combined_score", ascending=False).reset_index(drop=True)
        if not portfolio_ordered.empty:
            st.divider()
            st.markdown("### Portfolio charts")
            st.session_state["portfolio_chart_index"] = max(0, min(st.session_state["portfolio_chart_index"], len(portfolio_ordered) - 1))
            prow = portfolio_ordered.iloc[st.session_state["portfolio_chart_index"]]
            pticker_short = str(prow["ticker"]).replace(".NS", "")

            pc1, pc2 = st.columns(2)
            with pc1:
                pdaily_rank = get_display_stock_rank(prow["ticker"])
                st.markdown(f"#### Daily * {pticker_short} * {prow.get('stage', '')} * Daily Stock Rank {pdaily_rank}")
                pdpath = resolve_chart_path(daily_dir, prow["ticker"], "_daily.png")
                if pdpath:
                    st.image(safe_image_bytes(pdpath), use_container_width=True)
                else:
                    st.info("Daily chart not available.")
            with pc2:
                pweekly_rank = get_display_stock_rank(prow["ticker"])
                st.markdown(f"#### Weekly * {pticker_short} * {prow.get('stage', '')} * Weekly Stock Rank {pweekly_rank}")
                pwpath = resolve_chart_path(weekly_dir, prow["ticker"], "_weekly.png")
                if pwpath:
                    st.image(safe_image_bytes(pwpath), use_container_width=True)
                else:
                    st.info("Weekly chart not available.")

            nav1, nav2 = st.columns(2)
            with nav1:
                pprev = st.button("Previous", use_container_width=True, disabled=(st.session_state["portfolio_chart_index"] == 0), key="portfolio_prev")
            with nav2:
                pnext = st.button("Next", use_container_width=True, disabled=(st.session_state["portfolio_chart_index"] >= len(portfolio_ordered) - 1), key="portfolio_next")
            if pprev and st.session_state["portfolio_chart_index"] > 0:
                st.session_state["portfolio_chart_index"] -= 1
                st.rerun()
            if pnext and st.session_state["portfolio_chart_index"] < len(portfolio_ordered) - 1:
                st.session_state["portfolio_chart_index"] += 1
                st.rerun()

            stock_rank = get_stock_rank(prow["ticker"])
            card(prow, use_stage_color=True, stock_rank=stock_rank)
            render_stock_detail(prow)

    render_disclosure()

# Alerts and Advanced only in Pro
if view_mode == "Pro":
    with tabs[5]:
        st.markdown("### Alerts")
        st.markdown("#### Triggered alert candidates from the latest scan")
        if alert_candidates.empty:
            st.info("No alert candidates found in the latest data.")
        else:
            for _, r in alert_candidates.iterrows():
                stock_rank = get_stock_rank(r["ticker"])
                card(r, use_stage_color=True, show_change_text=f"Alert: {r['alert_type']} — {r['alert_reason']}", stock_rank=stock_rank)
        render_disclosure()

    with tabs[6]:
        def keep_simple(df: pd.DataFrame) -> pd.DataFrame:
            wanted = [c for c in ["Company Name","ticker","label","classification","stage","Industry"] if c in df.columns]
            out = df[wanted].copy() if wanted else df.copy()
            if "classification" in out.columns and "label" not in out.columns:
                out["label"] = out["classification"]
                out = out.drop(columns=["classification"])
            if "ticker" in out.columns:
                out = out.rename(columns={"ticker":"Ticker","label":"Classification"})
                out["Ticker"] = out["Ticker"].astype(str).str.replace(".NS","", regex=False)
            else:
                out = out.rename(columns={"label":"Classification"})
            return out
        st.markdown("### Advanced")
        with st.expander("Overall ranked", expanded=True):
            st.dataframe(keep_simple(combined), use_container_width=True, hide_index=True, height=360)
        with st.expander("Daily ranked", expanded=False):
            st.dataframe(keep_simple(daily_df), use_container_width=True, hide_index=True, height=320)
        with st.expander("Weekly ranked", expanded=False):
            st.dataframe(keep_simple(weekly_df), use_container_width=True, hide_index=True, height=320)
        with st.expander("Stock changes", expanded=False):
            st.dataframe(keep_simple(changes), use_container_width=True, hide_index=True, height=320)
        with st.expander("Industry changes", expanded=False):
            cols = [c for c in ["Industry","current_rank","prev_rank","rank_change"] if c in industry_changes.columns]
            st.dataframe(industry_changes[cols].rename(columns={"current_rank":"Current Rank","prev_rank":"Previous Rank","rank_change":"Rank Change"}), use_container_width=True, hide_index=True, height=320)
        render_disclosure()

# How to Use
how_tab_index = 4 if view_mode == "Beginner" else 7
with tabs[how_tab_index]:
    current_market_tone = market_tone(regime, combined)
    left, right = st.columns([1.05, 0.95])
    with left:
        st.markdown(f'''<div class="learn-card">
  <div class="stock-title">How to read this dashboard</div>
  <ul class="list-tight">
    <li>Start with <b>Decision Board</b>. Today the model reads <b>{current_market_tone}</b>.</li>
    <li>Then scan <b>Ready Now</b> and <b>Improving Fast</b> first, and treat watchlist names as earlier-stage ideas.</li>
    <li>Use <b>Charts</b> for daily and weekly confirmation.</li>
    <li>Use <b>Portfolio</b> to review baskets like Ready Now, Improving Fast, Watchlist and Avoid.</li>
  </ul>
</div>
<div class="learn-card">
  <div class="stock-title">How the stage model should be read</div>
  <ul class="list-tight">
    <li><b>Stage 1 • Preparing</b>: base forming, early structure.</li>
    <li><b>Stage 2 • Advancing</b>: uptrend with strength.</li>
    <li><b>Stage 3 • Under Pressure</b>: trend slowing, mixed signals.</li>
    <li><b>Stage 4 • Weakening</b>: downtrend, declining structure.</li>
  </ul>
</div>''', unsafe_allow_html=True)
    with right:
        img = Path(help_image_path)
        if img.exists():
            st.image(str(img), caption="Reference image for the four market phases", use_container_width=True)
        else:
            st.info("Stage image not found.")
    render_disclosure()

# Disclaimer
disclaimer_tab_index = 5 if view_mode == "Beginner" else 8
with tabs[disclaimer_tab_index]:
    st.markdown("### Disclaimer")
    st.write("This tool is for informational purposes only. It presents rule-based stage classifications and market summaries. In this model, Stage 1 means a base or repair zone, while Stage 2 is the main advancing phase. It does not provide personalized investment advice, suitability analysis, buy calls, sell calls, or allocation recommendations.")
    render_disclosure()
