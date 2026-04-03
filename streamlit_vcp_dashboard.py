
import streamlit as st
import pandas as pd
from pathlib import Path
import math
from urllib.parse import quote

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
.assist-box {border:1px solid var(--card-border); border-radius:16px; padding:0.85rem 0.95rem; background:rgba(255,255,255,0.03); margin-bottom:0.55rem;}
.assist-title {font-size:1rem; font-weight:800; margin-bottom:0.28rem;}
.assist-text {font-size:0.92rem; color: var(--muted); line-height:1.35;}
.stock-title {font-size: 1.02rem; font-weight: 700; margin-bottom: 0.06rem; line-height: 1.2;}
.meta-line {font-size: 0.93rem; font-weight: 600; line-height: 1.18; margin-top: 0.06rem; margin-bottom: 0.02rem;}
.stock-card {margin-bottom: 0.42rem; background: rgba(255,255,255,0.03); padding-top: 0.72rem; padding-bottom: 0.72rem;}
.stage-card-1 {background: var(--stage1-bg); border-color: var(--stage1-border);}
.stage-card-2 {background: var(--stage2-bg); border-color: var(--stage2-border);}
.stage-card-3 {background: var(--stage3-bg); border-color: var(--stage3-border);}
.stage-card-4 {background: var(--stage4-bg); border-color: var(--stage4-border);}
.change-badge-up {font-size: 1.12rem; font-weight: 900; margin-top: 0.1rem; color: var(--up);}
.change-badge-down {font-size: 1.12rem; font-weight: 900; margin-top: 0.1rem; color: var(--down);}
.rank-text {font-size: 0.84rem; font-weight: 700; color: var(--muted); margin-top: 0.18rem;}
.disclosure {border-left: 4px solid rgba(240,180,41,0.55); background: rgba(240,180,41,0.08); border-radius: 12px; padding: 0.7rem 0.85rem; font-size: 0.86rem; margin-bottom: 0.7rem; margin-top: 1rem;}
.list-tight {margin: 0.2rem 0 0 1rem; padding: 0;}
.change-text {font-size: 0.88rem; margin-top: 0.06rem; line-height: 1.18;}

.nav-wrap {display:flex; flex-wrap:wrap; gap:0.55rem; margin: 0.45rem 0 1rem 0;}
.nav-link {
  display:inline-block; padding:0.68rem 1.05rem; border-radius:999px; text-decoration:none;
  border:1px solid rgba(255,255,255,0.12); color:white; background: rgba(255,255,255,0.04); font-weight:700;
}
.nav-link.active {background: rgba(55,95,220,0.22); border-color: rgba(55,95,220,0.45);}
.stock-card-wrap {position:relative; margin-bottom:0.48rem;}
.stock-card-overlay {
  position:absolute; inset:0; z-index:1; border-radius:16px; text-decoration:none;
}
.stock-card-overlay:hover + .stock-card {border-color: rgba(55,95,220,0.45);}
.stock-card-content {position:relative; z-index:2;}
.card-actions {display:flex; gap:0.5rem; margin-top:0.7rem; position:relative; z-index:3;}
.card-action-btn {
  display:inline-block; padding:0.32rem 0.7rem; border-radius:999px; text-decoration:none;
  font-size:0.78rem; font-weight:800; border:1px solid rgba(255,255,255,0.18);
}
.card-action-watch {background: rgba(55,95,220,0.14); color:#8ab4ff; border-color: rgba(55,95,220,0.35);}
.card-action-alert {background: rgba(30,201,119,0.10); color:#7ee7b2; border-color: rgba(30,201,119,0.28);}
.small-note {font-size:0.86rem; color:var(--muted);}
@media (max-width: 768px) {
  .block-container {padding-top: 0.35rem; padding-left: 0.35rem; padding-right: 0.35rem;}
  .nav-link {font-size:0.92rem; padding:0.58rem 0.82rem;}
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

def resolve_chart_path(charts_dir: str, ticker: str, suffix: str):
    filename = ticker.replace(".", "_") + suffix
    path = Path(charts_dir) / filename
    return path if path.exists() else None

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
        if pd.notna(rs3) and pd.notna(rs6) and rs3 > 0 and rs6 > 0:
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

def beginner_translation(row: pd.Series) -> str:
    stage = str(row.get("stage", ""))
    label = str(row.get("label", row.get("classification", "Developing")))
    rank_change = pd.to_numeric(row.get("rank_change"), errors="coerce")
    if stage == "Stage 2" and label == "Strong":
        if pd.notna(rank_change) and rank_change > 0:
            return "This is one of the stronger names right now. Track it first because rank is improving."
        return "This is a stronger trending stock. Beginners should track it before looking at weaker setups."
    if stage == "Stage 2" and label == "Developing":
        return "Trend is positive, but it is not one of the cleanest leaders yet."
    if stage == "Stage 1":
        return "This is still in base or repair mode. Keep it on watchlist instead of treating it like a leader."
    if stage == "Stage 3":
        return "Momentum is less reliable here. Be more selective."
    if stage == "Stage 4" or label == "Weak":
        return "This is a lagging structure. Ignore it for now."
    return "Watch this after you review the strongest Stage 2 names."

def confidence_score(row: pd.Series) -> int:
    stage = str(row.get("stage", ""))
    label = str(row.get("label", row.get("classification", "Developing")))
    rank = pd.to_numeric(row.get("current_rank"), errors="coerce")
    rank_change = pd.to_numeric(row.get("rank_change"), errors="coerce")
    score = 40
    if stage == "Stage 2":
        score += 28
    elif stage == "Stage 1":
        score += 12
    elif stage == "Stage 3":
        score += 4
    elif stage == "Stage 4":
        score -= 8
    if label == "Strong":
        score += 18
    elif label == "Developing":
        score += 8
    elif label == "Cautious":
        score -= 4
    else:
        score -= 12
    if pd.notna(rank):
        score += max(0, 15 - min(int(rank), 15))
    if pd.notna(rank_change) and rank_change > 0:
        score += min(int(rank_change), 8)
    return max(5, min(int(score), 99))

def guided_workflow_steps(market_label: str) -> list:
    first_step = {
        "Risk On": "Start with Stage 2 names and the strongest industries.",
        "Mixed": "Be selective and focus on top-ranked Stage 2 names or the tightest Stage 1 bases.",
        "Risk Off": "Use the dashboard mainly to track improving bases and avoid forcing Stage 2 labels.",
    }.get(market_label, "Start with the highest-ranked names and confirm on both timeframes.")
    return [
        f"Read market tone first. Today the model reads: {market_label}. {first_step}",
        "Treat Stage 1 as a base or repair zone, and treat Stage 2 as the primary leadership phase.",
        "Prefer improving ranks, stronger industries, and daily-weekly alignment over isolated laggards.",
        "Use Portfolio and Alerts to monitor stage transitions over time.",
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
    for score_col in ["final_combined_score", "avg_combined_score", "combined_score", "score"]:
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
    for col in preferred_cols + ["current_rank", "rank", "rs_rank", "daily_rank", "weekly_rank", "stock_rank"]:
        if col in match.columns:
            val = pd.to_numeric(row.get(col), errors="coerce")
            if pd.notna(val):
                return str(int(val))
    return auto_rank(match, preferred_cols)

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

def build_today_changes(changes_df: pd.DataFrame):
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

def get_stock_rank(ticker: str, top_movers: pd.DataFrame) -> str:
    return rank_lookup(top_movers, ticker, ["current_rank"])

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

def app_url(tab=None, stock=None, action=None):
    parts = []
    if tab:
        parts.append(f"tab={quote(str(tab))}")
    if stock:
        parts.append(f"stock={quote(str(stock))}")
    if action:
        parts.append(f"action={quote(str(action))}")
    return "?" + "&".join(parts) if parts else "?"

def render_nav(active_tab: str, is_beginner: bool):
    tabs = ["Home", "Stocks", "Portfolio"] if is_beginner else ["Home", "Stocks", "Movers", "Market", "Portfolio", "Alerts", "Advanced", "Disclaimer"]
    links = []
    for tab in tabs:
        cls = "nav-link active" if tab == active_tab else "nav-link"
        links.append(f"<a class='{cls}' href='{app_url(tab=tab)}'>{tab}</a>")
    st.markdown("<div class='nav-wrap'>" + "".join(links) + "</div>", unsafe_allow_html=True)

def render_stock_card(row: pd.Series, *, active_tab: str, top_movers: pd.DataFrame, show_change_text: str = "", pct=None, show_quick_read: bool = False, beginner_mode: bool = False, show_actions: bool = True):
    label = row.get("label", row.get("classification", "Developing"))
    style = LABELS.get(label, LABELS["Developing"])
    company = str(row.get("Company Name", row.get("ticker", "Stock")))
    ticker = str(row.get("ticker", ""))
    ticker_short = ticker.replace(".NS", "")
    stage_raw = str(row.get("stage", "Unknown"))
    trend = trend_text(row)
    stock_rank = get_stock_rank(ticker, top_movers)
    explanation = beginner_translation(row) if beginner_mode else one_line_explanation(row)
    quick_read_html = f"<div class='change-text'><b>Quick read:</b> {one_line_explanation(row)}</div>" if show_quick_read else ""
    beginner_html = ""
    if beginner_mode:
        beginner_html = (
            f"<div class='change-text'><b>What it means:</b> {explanation}</div>"
            f"<div class='change-text'><b>Confidence:</b> {confidence_score(row)}/100</div>"
        )
    change_html = ""
    if pct is not None:
        cls = "change-badge-up" if pct > 0 else "change-badge-down"
        change_html = f"<div class='{cls}'>{pct:+.2f}%</div>"
    extra_change = f"<div class='change-text'>{show_change_text}</div>" if show_change_text else ""
    stage_cls = _stage_card_class(stage_raw)

    actions_html = ""
    if show_actions:
        watch_url = app_url(tab=active_tab, stock=ticker, action="watch")
        alert_url = app_url(tab=active_tab, stock=ticker, action="alert")
        actions_html = (
            "<div class='card-actions'>"
            f"<a class='card-action-btn card-action-watch' href='{watch_url}'>⭐ Watchlist</a>"
            f"<a class='card-action-btn card-action-alert' href='{alert_url}'>🔔 Alerts</a>"
            "</div>"
        )

    card_open_url = app_url(tab="Stocks", stock=ticker)
    html = f"""
<div class='stock-card-wrap'>
  <a class='stock-card-overlay' href='{card_open_url}' aria-label='Open {ticker_short} charts'></a>
  <div class='stock-card {stage_cls}'>
    <div class='stock-card-content'>
      <div style='display:flex; justify-content:space-between; align-items:flex-start; gap:0.5rem;'>
        <div style='min-width:0;'>
          <div class='stock-title'>{company} ({ticker_short})</div>
          <div class='meta-line'>{stage_raw} * {trend} * {stage_display(stage_raw)}</div>
        </div>
        <div style='display:flex; flex-direction:column; align-items:flex-end; gap:0.05rem;'>
          <div class='status-pill {style["css"]}'>{label}</div>
          <div class='rank-text'>Rank {stock_rank}</div>
          {change_html}
        </div>
      </div>
      {beginner_html}
      {quick_read_html}
      {extra_change}
      {actions_html}
    </div>
  </div>
</div>
"""
    st.markdown(html, unsafe_allow_html=True)

# ---------- load data ----------
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

daily_dir = f"{outdir}/charts/daily"
weekly_dir = f"{outdir}/charts/weekly"
company_map = company_choices(combined)
ticker_to_name = {str(v): str(k) for k, v in company_map.items()}
top_changed_df, changes_summary = build_today_changes(changes)
changed_tickers = set(top_changed_df["ticker"].dropna().tolist()) if not top_changed_df.empty and "ticker" in top_changed_df.columns else set()
top_stocks_today = combined[~combined["ticker"].isin(changed_tickers)].sort_values("final_combined_score", ascending=False).head(5).copy()
stage_counts = stage_count_summary(combined)

# ---------- state ----------
for key, default in [
    ("portfolio_names", []),
    ("custom_portfolio_names", []),
    ("portfolio_chart_index", 0),
    ("portfolio_selection", "Custom"),
    ("portfolio_selection_prev", "Custom"),
    ("selected_stock_index", 0),
    ("watchlist_names", []),
    ("alert_names", []),
]:
    if key not in st.session_state:
        st.session_state[key] = default

# ---------- query param actions ----------
qp = st.query_params
qp_tab = qp.get("tab", None)
qp_stock = qp.get("stock", None)
qp_action = qp.get("action", None)

st.title("Market Structure Radar")
view_mode = st.radio("View mode", ["Beginner", "Pro"], horizontal=True, index=0)
is_beginner = view_mode == "Beginner"
show_pro_quick_read = view_mode == "Pro"

allowed_tabs = ["Home", "Stocks", "Portfolio"] if is_beginner else ["Home", "Stocks", "Movers", "Market", "Portfolio", "Alerts", "Advanced", "Disclaimer"]
active_tab = qp_tab if qp_tab in allowed_tabs else ("Home" if "active_tab" not in st.session_state else st.session_state.get("active_tab", "Home"))
if active_tab not in allowed_tabs:
    active_tab = "Home"
st.session_state["active_tab"] = active_tab

if qp_stock:
    ranked = combined.sort_values("final_combined_score", ascending=False).reset_index(drop=True).copy()
    matches = ranked.index[ranked["ticker"].astype(str) == str(qp_stock)].tolist()
    if not matches:
        matches = ranked.index[ranked["ticker"].astype(str).str.replace(".NS", "", regex=False) == str(qp_stock).replace(".NS", "")].tolist()
    if matches:
        st.session_state["selected_stock_index"] = int(matches[0])

if qp_action and qp_stock:
    company = ticker_to_name.get(str(qp_stock))
    if company:
        if qp_action == "watch":
            st.session_state["watchlist_names"] = dedupe_names(st.session_state["watchlist_names"] + [company], limit=MAX_PORTFOLIO_STOCKS)
            st.session_state["portfolio_names"] = dedupe_names(st.session_state["portfolio_names"] + [company], limit=MAX_PORTFOLIO_STOCKS)
            st.success(f"Added {company} to watchlist.")
        elif qp_action == "alert":
            st.session_state["alert_names"] = dedupe_names(st.session_state["alert_names"] + [company], limit=MAX_PORTFOLIO_STOCKS)
            st.success(f"Added {company} to alerts.")

if is_beginner:
    st.caption("Beginner mode narrows the flow to market tone, starter stocks, and a small watchlist.")
else:
    st.caption("Pro mode includes full rankings, movers, market internals, alert candidates, and portfolio diagnostics.")

render_nav(active_tab, is_beginner)

def get_prebuilt_portfolio(name: str, combined: pd.DataFrame, changes: pd.DataFrame, industry_names: list) -> list:
    ranked = combined.sort_values("final_combined_score", ascending=False)
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
    elif name in {"Stage 1", "Stage 2", "Stage 3", "Stage 4"}:
        names = combined.loc[combined["stage"] == name, "Company Name"].dropna().tolist()
    elif name in {"Cautious", "Weak", "Strong"}:
        names = combined.loc[combined["label"] == name, "Company Name"].dropna().tolist()
    elif name in industry_names:
        names = ranked.loc[ranked["Industry"].astype(str).str.strip() == name, "Company Name"].dropna().tolist()
    return dedupe_names(names, limit=MAX_PORTFOLIO_STOCKS)

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

if active_tab == "Home":
    current_market_tone = market_tone(regime, combined)
    st.markdown("### Today’s Summary")
    c1, c2, c3 = st.columns(3)
    with c1:
        render_summary_card("Market tone", current_market_tone, "Use this before reviewing any stock")
    with c2:
        render_summary_card("New Strong", str(changes_summary["New Strong"]), "Stage 2 leaders improving materially")
    with c3:
        render_summary_card("Top industries", top_industry_text(industry), "Industries that are leading currently")

    left, right = st.columns([1.25, 1])
    with left:
        st.markdown("#### Top names that changed")
        if top_changed_df.empty:
            st.info("No major stock changes found in the latest run.")
        else:
            for _, r in top_changed_df.iterrows():
                render_stock_card(r, active_tab=active_tab, top_movers=top_movers, show_change_text=f"What changed: {r['what_changed']}", beginner_mode=is_beginner)
    with right:
        st.markdown("#### Top stocks today")
        for _, r in top_stocks_today.iterrows():
            render_stock_card(r, active_tab=active_tab, top_movers=top_movers, show_quick_read=show_pro_quick_read, beginner_mode=is_beginner)

    st.divider()
    st.markdown("#### Guided workflow")
    workflow_cols = st.columns(len(guided_workflow_steps(current_market_tone)))
    for col, step_text in zip(workflow_cols, guided_workflow_steps(current_market_tone)):
        with col:
            st.markdown(f"""<div class="assist-box"><div class="assist-text">{step_text}</div></div>""", unsafe_allow_html=True)
    render_disclosure()

elif active_tab == "Stocks":
    ranked = combined.sort_values("final_combined_score", ascending=False).reset_index(drop=True).copy()
    names = ranked["Company Name"].dropna().astype(str).tolist()
    if not names:
        st.info("No stocks available.")
    else:
        st.session_state["selected_stock_index"] = max(0, min(st.session_state["selected_stock_index"], len(names)-1))
        current_index = st.session_state["selected_stock_index"]
        selected_name = st.selectbox("Select stock", names, index=current_index, key=f"stocks_select_name_ordered_{current_index}")
        selected_index = names.index(selected_name)
        if selected_index != current_index:
            st.session_state["selected_stock_index"] = selected_index
            st.query_params["tab"] = "Stocks"
            st.query_params["stock"] = str(ranked.iloc[selected_index]["ticker"])
            st.rerun()

        row = ranked.iloc[st.session_state["selected_stock_index"]]
        ticker_short = str(row["ticker"]).replace(".NS", "")
        st.markdown("#### Selected stock")
        render_stock_card(row, active_tab=active_tab, top_movers=top_movers, show_quick_read=show_pro_quick_read, beginner_mode=is_beginner)

        dpath = resolve_chart_path(daily_dir, row["ticker"], "_daily.png")
        wpath = resolve_chart_path(weekly_dir, row["ticker"], "_weekly.png")
        a, b = st.columns(2)
        with a:
            daily_rank = get_stock_rank(row["ticker"], top_movers)
            st.markdown(f"#### Daily * {ticker_short} * {row.get('stage', '')} * Daily Rank {daily_rank}")
            if dpath:
                st.image(safe_image_bytes(dpath), use_container_width=True)
            else:
                st.info("Daily chart not available.")
        with b:
            weekly_rank = get_stock_rank(row["ticker"], top_movers)
            st.markdown(f"#### Weekly * {ticker_short} * {row.get('stage', '')} * Weekly Rank {weekly_rank}")
            if wpath:
                st.image(safe_image_bytes(wpath), use_container_width=True)
            else:
                st.info("Weekly chart not available.")

        nav1, nav2 = st.columns(2)
        with nav1:
            prev2 = st.button("Previous", use_container_width=True, disabled=(st.session_state["selected_stock_index"] == 0))
        with nav2:
            next2 = st.button("Next", use_container_width=True, disabled=(st.session_state["selected_stock_index"] >= len(names) - 1))
        if prev2 and st.session_state["selected_stock_index"] > 0:
            st.session_state["selected_stock_index"] -= 1
            st.query_params["tab"] = "Stocks"
            st.query_params["stock"] = str(ranked.iloc[st.session_state["selected_stock_index"]]["ticker"])
            st.rerun()
        if next2 and st.session_state["selected_stock_index"] < len(names) - 1:
            st.session_state["selected_stock_index"] += 1
            st.query_params["tab"] = "Stocks"
            st.query_params["stock"] = str(ranked.iloc[st.session_state["selected_stock_index"]]["ticker"])
            st.rerun()

        st.divider()
        st.markdown("### Browse more stocks")
        for _, r in ranked.head(20).iterrows():
            render_stock_card(r, active_tab=active_tab, top_movers=top_movers, beginner_mode=is_beginner)
        render_disclosure()

elif active_tab == "Movers" and not is_beginner:
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
                render_stock_card(r, active_tab=active_tab, top_movers=top_movers, pct=float(r[col]), show_quick_read=show_pro_quick_read)
        with c2:
            st.markdown(f"#### Major downward moves • {selected}")
            for _, r in mv.sort_values([col, "final_combined_score"], ascending=[True, False]).head(10).iterrows():
                render_stock_card(r, active_tab=active_tab, top_movers=top_movers, pct=float(r[col]), show_quick_read=show_pro_quick_read)
    render_disclosure()

elif active_tab == "Market" and not is_beginner:
    st.markdown("### Market")
    c1, c2, c3, c4 = st.columns(4)
    with c1: render_summary_card("Stage 1", str(stage_counts["Stage 1"]), "Base / repair")
    with c2: render_summary_card("Stage 2", str(stage_counts["Stage 2"]), "Advancing trend")
    with c3: render_summary_card("Stage 3", str(stage_counts["Stage 3"]), "Topping / transition")
    with c4: render_summary_card("Stage 4", str(stage_counts["Stage 4"]), "Declining trend")

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

elif active_tab == "Portfolio":
    portfolio_options = ["Custom", "Top 15", "New Breakouts", "New Strong", "Strong", "Cautious", "Weak", "Stage 1", "Stage 2", "Stage 3", "Stage 4"] + INDUSTRY_PORTFOLIOS
    selected_portfolio = st.selectbox("Portfolio selection", portfolio_options, key="portfolio_selection")
    previous_portfolio = st.session_state.get("portfolio_selection_prev", "Custom")
    if selected_portfolio != previous_portfolio:
        if previous_portfolio == "Custom":
            st.session_state["custom_portfolio_names"] = dedupe_names(st.session_state["portfolio_names"], limit=MAX_PORTFOLIO_STOCKS)
        if selected_portfolio == "Custom":
            st.session_state["portfolio_names"] = dedupe_names(st.session_state.get("custom_portfolio_names", []), limit=MAX_PORTFOLIO_STOCKS)
        else:
            st.session_state["portfolio_names"] = get_prebuilt_portfolio(selected_portfolio, combined, changes, INDUSTRY_PORTFOLIOS)
        st.session_state["portfolio_chart_index"] = 0
        st.session_state["portfolio_selection_prev"] = selected_portfolio

    st.session_state["portfolio_names"] = dedupe_names(st.session_state["portfolio_names"], limit=MAX_PORTFOLIO_STOCKS)
    if selected_portfolio == "Custom":
        st.session_state["custom_portfolio_names"] = dedupe_names(st.session_state["portfolio_names"], limit=MAX_PORTFOLIO_STOCKS)

    names = sorted(company_map.keys())
    available = [n for n in names if n not in st.session_state["portfolio_names"]]
    portfolio_full = len(st.session_state["portfolio_names"]) >= MAX_PORTFOLIO_STOCKS
    selected_to_add = st.selectbox("Add stock", [""] + available, key="portfolio_add_name", disabled=portfolio_full)
    if portfolio_full:
        st.warning(f"Portfolio is limited to {MAX_PORTFOLIO_STOCKS} stocks.")
    if st.button("Add to portfolio", use_container_width=True, disabled=portfolio_full) and selected_to_add:
        st.session_state["portfolio_names"] = dedupe_names(st.session_state["portfolio_names"] + [selected_to_add], limit=MAX_PORTFOLIO_STOCKS)
        if selected_portfolio == "Custom":
            st.session_state["custom_portfolio_names"] = dedupe_names(st.session_state["portfolio_names"], limit=MAX_PORTFOLIO_STOCKS)
        st.rerun()

    if not st.session_state["portfolio_names"]:
        st.info("No stocks added yet.")
    else:
        current = combined[combined["Company Name"].isin(st.session_state["portfolio_names"])].copy().sort_values("final_combined_score", ascending=False).head(MAX_PORTFOLIO_STOCKS).copy()
        p_stage_counts = current["stage"].value_counts() if "stage" in current.columns else pd.Series(dtype=int)
        c1, c2, c3, c4, c5 = st.columns(5)
        with c1: render_summary_card("Total stocks", str(len(current)), "Stocks currently added")
        with c2: render_summary_card("Stage 1", str(int(p_stage_counts.get("Stage 1", 0))), "Base / repair")
        with c3: render_summary_card("Stage 2", str(int(p_stage_counts.get("Stage 2", 0))), "Advancing trend")
        with c4: render_summary_card("Stage 3", str(int(p_stage_counts.get("Stage 3", 0))), "Topping / transition")
        with c5: render_summary_card("Stage 4", str(int(p_stage_counts.get("Stage 4", 0))), "Declining trend")

        st.markdown("### Portfolio assistant")
        for msg in portfolio_assistant(current):
            st.markdown(f"""<div class="assist-box"><div class="assist-text">{msg}</div></div>""", unsafe_allow_html=True)

        st.divider()
        for _, r in current.sort_values("final_combined_score", ascending=False).iterrows():
            render_stock_card(r, active_tab=active_tab, top_movers=top_movers, show_quick_read=show_pro_quick_read, beginner_mode=is_beginner)

        removable = [""] + sorted(st.session_state["portfolio_names"])
        selected_remove = st.selectbox("Remove stock", removable, key="portfolio_remove_name")
        if st.button("Remove from portfolio", use_container_width=True) and selected_remove:
            st.session_state["portfolio_names"] = [x for x in st.session_state["portfolio_names"] if x != selected_remove]
            if selected_portfolio == "Custom":
                st.session_state["custom_portfolio_names"] = dedupe_names(st.session_state["portfolio_names"], limit=MAX_PORTFOLIO_STOCKS)
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
                pdaily_rank = get_stock_rank(prow["ticker"], top_movers)
                st.markdown(f"#### Daily * {pticker_short} * {prow.get('stage', '')} * Daily Stock Rank {pdaily_rank}")
                pdpath = resolve_chart_path(daily_dir, prow["ticker"], "_daily.png")
                if pdpath:
                    st.image(safe_image_bytes(pdpath), use_container_width=True)
                else:
                    st.info("Daily chart not available.")
            with pc2:
                pweekly_rank = get_stock_rank(prow["ticker"], top_movers)
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
    render_disclosure()

elif active_tab == "Alerts" and not is_beginner:
    st.markdown("### Alerts")
    if not st.session_state["alert_names"]:
        st.info("No stocks added to alerts yet.")
    else:
        alert_df = combined[combined["Company Name"].isin(st.session_state["alert_names"])].copy().sort_values("final_combined_score", ascending=False)
        for _, r in alert_df.iterrows():
            render_stock_card(r, active_tab=active_tab, top_movers=top_movers, show_change_text="Tracked in your alerts list.", show_quick_read=show_pro_quick_read)
    render_disclosure()

elif active_tab == "Advanced" and not is_beginner:
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
    render_disclosure()

elif active_tab == "Disclaimer" and not is_beginner:
    st.markdown("### Disclaimer")
    st.write("This tool is for informational purposes only. It presents rule-based stage classifications and market summaries. In this model, Stage 1 means a base or repair zone, while Stage 2 is the main advancing phase. It does not provide personalized investment advice, suitability analysis, buy calls, sell calls, or allocation recommendations.")
    render_disclosure()
