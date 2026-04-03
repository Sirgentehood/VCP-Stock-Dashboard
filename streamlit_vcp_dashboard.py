import math
from pathlib import Path

import pandas as pd
import streamlit as st

st.set_page_config(page_title="Market Structure Radar", layout="wide", initial_sidebar_state="collapsed")

st.markdown(
    """
<style>
:root {
  --bg-soft: rgba(255,255,255,0.03);
  --bg-softer: rgba(255,255,255,0.02);
  --card-border: rgba(148,163,184,0.18);
  --text-muted: rgba(255,255,255,0.70);
  --text-faint: rgba(255,255,255,0.54);
  --stage1: #5b8cff;
  --stage2: #10c58a;
  --stage3: #f2b84b;
  --stage4: #ff6b6b;
  --strong: #19d28c;
  --developing: #78a6ff;
  --cautious: #f2b84b;
  --weak: #ff7a7a;
}
.block-container {
  max-width: 1450px;
  padding-top: 0.45rem;
  padding-bottom: 1.3rem;
  padding-left: 0.85rem;
  padding-right: 0.85rem;
}
[data-testid="stSidebar"], section[data-testid="stSidebar"], [data-testid="collapsedControl"] {display:none;}
.stTabs [data-baseweb="tab-list"] {gap: 0.45rem; margin-top: 0.15rem;}
.stTabs [data-baseweb="tab"] {
  height: 44px;
  border-radius: 12px;
  padding-left: 0.95rem;
  padding-right: 0.95rem;
  background: rgba(255,255,255,0.03);
  font-weight: 700;
}
.stTabs [aria-selected="true"] {background: rgba(255,255,255,0.08) !important;}
div[data-testid="stVerticalBlock"]:has(> div > .sticky-shell) {
  position: sticky;
  top: 0.25rem;
  z-index: 20;
}
.sticky-shell {
  background: linear-gradient(180deg, rgba(14,17,23,0.98) 0%, rgba(14,17,23,0.88) 100%);
  border: 1px solid rgba(255,255,255,0.07);
  border-radius: 18px;
  padding: 0.8rem 0.95rem;
  margin-bottom: 0.7rem;
  backdrop-filter: blur(12px);
}
.topbar-grid {
  display: grid;
  grid-template-columns: 1.15fr 1fr 1fr 1fr;
  gap: 0.65rem;
}
.hero-card, .summary-card, .learn-card, .assist-box, .timeline-card, .mini-card, .stock-shell {
  border: 1px solid var(--card-border);
  border-radius: 18px;
  background: var(--bg-soft);
}
.hero-card {padding: 1rem 1.05rem;}
.summary-card {padding: 0.95rem 1rem; height: 100%;}
.learn-card, .assist-box, .timeline-card, .mini-card {padding: 0.95rem 1rem;}
.kicker {
  font-size: 0.72rem;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--text-faint);
}
.big-number {font-size: 1.45rem; font-weight: 800; margin-top: 0.1rem;}
.muted {color: var(--text-muted);}
.market-story {font-size: 0.97rem; color: var(--text-muted); margin-top: 0.35rem; line-height: 1.35;}
.decision-banner {
  border-radius: 18px;
  padding: 1rem 1.1rem;
  border: 1px solid rgba(255,255,255,0.08);
  background: linear-gradient(135deg, rgba(16,197,138,0.10) 0%, rgba(91,140,255,0.08) 50%, rgba(255,255,255,0.03) 100%);
}
.decision-title {font-size: 1.12rem; font-weight: 800; margin-bottom: 0.2rem;}
.decision-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 0.65rem;
  margin-top: 0.75rem;
}
.decision-pill {
  border-radius: 14px;
  padding: 0.8rem 0.9rem;
  background: rgba(255,255,255,0.04);
  border: 1px solid rgba(255,255,255,0.06);
}
.decision-label {font-size: 0.72rem; text-transform: uppercase; color: var(--text-faint); letter-spacing: 0.06em;}
.decision-text {font-size: 0.96rem; font-weight: 700; margin-top: 0.15rem; line-height: 1.28;}
.stock-shell {
  margin-bottom: 0.7rem;
  padding: 0.9rem 0.95rem 0.8rem 0.95rem;
  transition: transform 0.14s ease, border-color 0.14s ease, box-shadow 0.14s ease;
}
.stock-shell:hover {
  transform: translateY(-1px);
  border-color: rgba(255,255,255,0.16);
  box-shadow: 0 10px 30px rgba(0,0,0,0.16);
}
.stock-stage-1 {background: linear-gradient(135deg, rgba(91,140,255,0.14), rgba(91,140,255,0.05)); border-color: rgba(91,140,255,0.34);}
.stock-stage-2 {background: linear-gradient(135deg, rgba(16,197,138,0.16), rgba(16,197,138,0.05)); border-color: rgba(16,197,138,0.38); box-shadow: 0 0 0 1px rgba(16,197,138,0.10) inset;}
.stock-stage-3 {background: linear-gradient(135deg, rgba(242,184,75,0.15), rgba(242,184,75,0.05)); border-color: rgba(242,184,75,0.34);}
.stock-stage-4 {background: linear-gradient(135deg, rgba(255,107,107,0.16), rgba(255,107,107,0.05)); border-color: rgba(255,107,107,0.34);}
.stock-topline {display:flex; justify-content:space-between; align-items:flex-start; gap:0.8rem;}
.stock-name {font-size: 1.13rem; font-weight: 800; line-height: 1.2;}
.stock-rank {
  font-size: 1.05rem;
  font-weight: 800;
  white-space: nowrap;
}
.rank-up {color: var(--strong);}
.rank-down {color: var(--weak);}
.rank-flat {color: rgba(255,255,255,0.82);}
.stock-meta {font-size: 0.94rem; font-weight: 700; color: rgba(255,255,255,0.88); margin-top: 0.15rem;}
.stock-industry {font-size: 0.82rem; color: var(--text-faint); margin-top: 0.1rem;}
.stock-insight {font-size: 1rem; font-weight: 700; margin-top: 0.6rem; line-height: 1.28;}
.stock-subline {font-size: 0.86rem; color: var(--text-muted); margin-top: 0.34rem; line-height: 1.28;}
.stock-footer {display:flex; justify-content:space-between; align-items:center; gap:0.6rem; margin-top: 0.72rem; flex-wrap: wrap;}
.pill-row {display:flex; gap:0.45rem; flex-wrap:wrap; align-items:center;}
.status-pill, .action-pill, .mini-pill {
  display:inline-flex;
  align-items:center;
  border-radius:999px;
  font-size:0.74rem;
  font-weight:800;
  padding:0.22rem 0.56rem;
  white-space:nowrap;
}
.status-strong {background: rgba(25,210,140,0.16); color: var(--strong); border:1px solid rgba(25,210,140,0.34);}
.status-developing {background: rgba(120,166,255,0.14); color: var(--developing); border:1px solid rgba(120,166,255,0.30);}
.status-cautious {background: rgba(242,184,75,0.16); color: var(--cautious); border:1px solid rgba(242,184,75,0.34);}
.status-weak {background: rgba(255,122,122,0.16); color: var(--weak); border:1px solid rgba(255,122,122,0.34);}
.action-opportunity {background: rgba(25,210,140,0.12); color: var(--strong); border:1px solid rgba(25,210,140,0.30);}
.action-watch {background: rgba(91,140,255,0.12); color: #9fc0ff; border:1px solid rgba(91,140,255,0.30);}
.action-caution {background: rgba(242,184,75,0.12); color: var(--cautious); border:1px solid rgba(242,184,75,0.30);}
.action-avoid {background: rgba(255,107,107,0.12); color: var(--weak); border:1px solid rgba(255,107,107,0.30);}
.mini-pill {background: rgba(255,255,255,0.05); color: var(--text-muted); border:1px solid rgba(255,255,255,0.07);}
.change-up {color: var(--strong); font-weight: 800;}
.change-down {color: var(--weak); font-weight: 800;}
.timeline-line {padding: 0.65rem 0; border-bottom: 1px solid rgba(255,255,255,0.06);}
.timeline-line:last-child {border-bottom: none;}
.timeline-time {font-size: 0.78rem; color: var(--text-faint); font-weight: 700;}
.timeline-text {font-size: 0.95rem; font-weight: 700; margin-top: 0.12rem;}
.disclosure {
  border-left: 4px solid rgba(242,184,75,0.55);
  background: rgba(242,184,75,0.08);
  border-radius: 14px;
  padding: 0.8rem 0.9rem;
  font-size: 0.86rem;
  margin-bottom: 0.7rem;
  margin-top: 1rem;
}
.section-title {font-size: 1.1rem; font-weight: 800; margin-bottom: 0.55rem;}
.small-help {font-size: 0.85rem; color: var(--text-faint);}
@media (max-width: 900px) {
  .topbar-grid, .decision-grid {grid-template-columns: 1fr;}
  .block-container {padding-left: 0.5rem; padding-right: 0.5rem;}
}
</style>
""",
    unsafe_allow_html=True,
)

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


def compact_explanation(row: pd.Series) -> str:
    label = str(row.get("label", row.get("classification", "Developing")))
    stage = str(row.get("stage", ""))
    rank = pd.to_numeric(row.get("current_rank"), errors="coerce")
    prev_rank = pd.to_numeric(row.get("prev_rank"), errors="coerce")
    rank_change = pd.to_numeric(row.get("rank_change"), errors="coerce")
    rs3 = pd.to_numeric(row.get("rs_3m_pct"), errors="coerce")
    rs6 = pd.to_numeric(row.get("rs_6m_pct"), errors="coerce")
    score = pd.to_numeric(row.get("final_combined_score", row.get("avg_combined_score", row.get("combined_score"))), errors="coerce")

    if stage == "Stage 2" and label == "Strong":
        if pd.notna(rank_change) and rank_change > 0:
            return f"Leadership improving • Rank up {int(rank_change)}"
        if pd.notna(rank) and rank <= 10:
            return "Top-ranked Stage 2 leader"
        if pd.notna(rs3) and rs3 > 0 and pd.notna(rs6) and rs6 > 0:
            return "Trend and relative strength aligned"
        return "Leadership structure intact"

    if stage == "Stage 1":
        if pd.notna(score) and score >= 65:
            return "Base tightening • Watch for Stage 2"
        if pd.notna(rs3) and rs3 < 0:
            return "Repair phase • Needs more time"
        return "Base forming • Not yet trending"

    if label == "Developing" and stage == "Stage 2":
        return "Positive trend • Needs more conviction"

    if stage == "Stage 3" or label == "Cautious":
        if pd.notna(prev_rank) and pd.notna(rank) and rank > prev_rank:
            return "Momentum slipping • Structure weakening"
        return "Transition phase • Failed rallies risk"

    if stage == "Stage 4":
        return "Declining structure • Avoid for now"

    if pd.notna(rs3) and pd.notna(rs6) and rs3 < 0 and rs6 < 0:
        return "Relative strength weak across timeframes"

    return "Mixed structure • Keep on watch"


def action_tag(row: pd.Series) -> tuple[str, str]:
    stage = str(row.get("stage", ""))
    label = str(row.get("label", row.get("classification", "Developing")))
    if stage == "Stage 2" and label == "Strong":
        return "Opportunity", "action-opportunity"
    if stage == "Stage 1":
        return "Watch", "action-watch"
    if stage == "Stage 3" or label == "Cautious":
        return "Caution", "action-caution"
    if stage == "Stage 4" or label == "Weak":
        return "Avoid", "action-avoid"
    return "Watch", "action-watch"


def guided_workflow_steps(market_label: str) -> list[str]:
    first_step = {
        "Risk On": "Start with Stage 2 names and strongest industries.",
        "Mixed": "Focus on top-ranked Stage 2 names and tight Stage 1 bases.",
        "Risk Off": "Track improving bases and avoid forcing weak names.",
    }.get(market_label, "Start with the highest-ranked names and confirm on both timeframes.")
    return [
        f"Read market tone first. Today: {market_label}. {first_step}",
        "Treat Stage 1 as watchlist territory and Stage 2 as the primary leadership phase.",
        "Prefer improving ranks, stronger industries and daily-weekly alignment.",
        "Use Portfolio and Alerts to track transitions instead of reacting to noise.",
    ]


def portfolio_assistant(current: pd.DataFrame) -> list[str]:
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
        msgs.append(f"Only {stage2} of {total} stocks are in Stage 2, so internal leadership is limited.")
    if weak >= max(2, math.ceil(total * 0.4)):
        msgs.append(f"{weak} names are in Weak or Cautious territory, so risk is concentrated in laggards.")
    else:
        msgs.append("Weak and Cautious names are contained, so the basket is not heavily tilted to laggards.")
    if stage4 > 0:
        msgs.append(f"{stage4} names are already in Stage 4, so these deserve review first.")
    top_industries = current["Industry"].dropna().astype(str).value_counts().head(2).index.tolist() if "Industry" in current.columns else []
    if top_industries:
        msgs.append(f"Main exposure sits in {', '.join(top_industries)}.")
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
    st.markdown(
        """
<div class="disclosure">
This dashboard is an informational analytics tool. It shows rule-based stage classifications and market summaries. In this model, Stage 1 means a base or repair zone, not an actionable uptrend by itself. Stage 2 is the primary leadership phase. The tool does not provide personalized investment advice, suitability analysis, buy calls, sell calls, or allocation recommendations.
</div>
""",
        unsafe_allow_html=True,
    )


def render_summary_card(title: str, value: str, subtitle: str):
    st.markdown(
        f"""
<div class="summary-card">
  <div class="kicker">{title}</div>
  <div class="big-number">{value}</div>
  <div class="muted">{subtitle}</div>
</div>
""",
        unsafe_allow_html=True,
    )


def _stage_card_class(stage_raw: str) -> str:
    return {
        "Stage 1": "stock-stage-1",
        "Stage 2": "stock-stage-2",
        "Stage 3": "stock-stage-3",
        "Stage 4": "stock-stage-4",
    }.get(stage_raw, "")


def auto_rank(df: pd.DataFrame, preferred_cols: list[str]) -> str:
    if df.empty:
        return "n/a"
    work = df.copy()
    candidate_score_cols = [
        "final_combined_score", "avg_combined_score", "combined_score",
        "final_daily_score", "daily_score", "final_weekly_score", "weekly_score", "score"
    ]
    for score_col in candidate_score_cols:
        if score_col in work.columns:
            scores = pd.to_numeric(work[score_col], errors="coerce")
            if scores.notna().any():
                val = scores.rank(method="min", ascending=False).iloc[0]
                if pd.notna(val):
                    return str(int(val))
    return "n/a"


def rank_lookup(df: pd.DataFrame, ticker: str, preferred_cols: list[str]) -> str:
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
    search_cols = preferred_cols + ["current_rank", "rank", "rs_rank", "daily_rank", "weekly_rank", "final_rank", "combined_rank", "stock_rank"]
    for col in search_cols:
        if col in match.columns:
            val = pd.to_numeric(row.get(col), errors="coerce")
            if pd.notna(val):
                return str(int(val))
    return auto_rank(match, preferred_cols)


def priority_score(row: pd.Series) -> float:
    stage = str(row.get("stage", ""))
    label = str(row.get("label", row.get("classification", "Developing")))
    score = 0.0
    score += {"Stage 2": 120, "Stage 1": 70, "Stage 3": 35, "Stage 4": 0}.get(stage, 30)
    score += {"Strong": 40, "Developing": 18, "Cautious": -8, "Weak": -25}.get(label, 0)
    rank_change = pd.to_numeric(row.get("rank_change"), errors="coerce")
    if pd.notna(rank_change):
        score += max(min(rank_change, 12), -12) * 4
    final_score = pd.to_numeric(row.get("final_combined_score", row.get("avg_combined_score", row.get("combined_score"))), errors="coerce")
    if pd.notna(final_score):
        score += final_score * 0.35
    for col, weight in [("entered_stage_2", 28), ("new_weekly_breakout", 24), ("new_daily_breakout", 18)]:
        if bool(row.get(col, False)):
            score += weight
    return float(score)


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

    df["change_priority_score"] = df.apply(priority_score, axis=1)
    entered_strong = (df["label"] == "Strong") & (df["change_priority_score"] >= 60)
    summary["New Strong"] = int(entered_strong.sum())

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
            parts.append(f"Rank up {int(rc)}")
        return " • ".join(parts[:3]) if parts else "Score improved"

    df["what_changed"] = df.apply(what_changed, axis=1)
    top_changed = df.sort_values(["change_priority_score", "final_combined_score"], ascending=[False, False]).head(5).copy()
    return top_changed, summary


def dedupe_names(names: list, limit: int = MAX_PORTFOLIO_STOCKS) -> list[str]:
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


def get_industry_portfolio_options(industry_df: pd.DataFrame, combined_df: pd.DataFrame, limit: int = 21) -> list[str]:
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

    grouped = (
        combined_df.dropna(subset=["Industry"])
        .groupby("Industry", as_index=False)["final_combined_score"]
        .mean()
        .sort_values("final_combined_score", ascending=False)
    )
    industries = grouped["Industry"].astype(str).str.strip().tolist()
    return dedupe_names(industries, limit=limit)


def get_prebuilt_portfolio(name: str, combined: pd.DataFrame, changes: pd.DataFrame, industry_portfolios: list[str]) -> list[str]:
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
    elif name == "Cautious":
        names = combined.loc[combined["label"] == "Cautious", "Company Name"].dropna().tolist()
    elif name == "Weak":
        names = combined.loc[combined["label"] == "Weak", "Company Name"].dropna().tolist()
    elif name == "Strong":
        names = combined.loc[combined["label"] == "Strong", "Company Name"].dropna().tolist()
    elif name in industry_portfolios:
        names = ranked.loc[ranked["Industry"].astype(str).str.strip() == name, "Company Name"].dropna().tolist()
    return dedupe_names(names, limit=MAX_PORTFOLIO_STOCKS)


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
            reason = "Trend moved into the advancing phase."
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


def market_story(current_market_tone: str, combined_df: pd.DataFrame, industry_df: pd.DataFrame) -> str:
    stage2_count = int((combined_df["stage"] == "Stage 2").sum()) if "stage" in combined_df.columns else 0
    stage4_count = int((combined_df["stage"] == "Stage 4").sum()) if "stage" in combined_df.columns else 0
    top_industries = top_industry_text(industry_df, 2)
    if current_market_tone == "Risk On":
        return f"Leadership is broadening. Stage 2 count is {stage2_count} and leading groups are {top_industries}."
    if current_market_tone == "Mixed":
        return f"Leadership is selective. Focus on top-ranked Stage 2 names while Stage 4 count remains {stage4_count}."
    return f"Risk appetite is weak. Keep attention on improving bases while {stage4_count} names remain in Stage 4."


def decision_texts(current_market_tone: str) -> tuple[str, str, str]:
    if current_market_tone == "Risk On":
        return (
            "Stage 2 strong names with improving rank",
            "Stage 3/4 names with slipping rank",
            "Tight Stage 1 bases near transition",
        )
    if current_market_tone == "Mixed":
        return (
            "Only top-ranked Stage 2 leaders",
            "Loose structures and falling ranks",
            "Stage 1 names with tighter bases",
        )
    return (
        "Improving bases and selective leaders",
        "Weak structure and failed rallies",
        "Repair candidates building cleaner bases",
    )


def short_label(value) -> str:
    if pd.isna(value):
        return "n/a"
    try:
        if float(value).is_integer():
            return str(int(float(value)))
    except Exception:
        pass
    return str(value)


def rank_trend_text(row: pd.Series, stock_rank: str) -> tuple[str, str]:
    rank_change = pd.to_numeric(row.get("rank_change"), errors="coerce")
    if stock_rank == "n/a":
        return "Rank n/a", "rank-flat"
    if pd.notna(rank_change) and rank_change > 0:
        return f"Rank #{stock_rank} ↑{int(rank_change)}", "rank-up"
    if pd.notna(rank_change) and rank_change < 0:
        return f"Rank #{stock_rank} ↓{abs(int(rank_change))}", "rank-down"
    return f"Rank #{stock_rank}", "rank-flat"


def show_message(msg: str):
    st.toast(msg)


def add_to_named_list(list_key: str, name: str, message: str):
    current = st.session_state.get(list_key, [])
    updated = dedupe_names(current + [name], limit=MAX_PORTFOLIO_STOCKS)
    st.session_state[list_key] = updated
    show_message(message)


def card(
    row: pd.Series,
    key_prefix: str,
    stock_rank: str = "n/a",
    show_quick_read: bool = False,
    show_rank: bool = True,
    show_change_text: str = "",
    pct=None,
):
    company = str(row.get("Company Name", row.get("ticker", "Stock"))).strip()
    ticker = str(row.get("ticker", "")).replace(".NS", "")
    stage_raw = str(row.get("stage", "Unknown"))
    label = str(row.get("label", row.get("classification", "Developing")))
    trend = trend_text(row)
    phase = stage_display(stage_raw)
    explanation = compact_explanation(row)
    tag_text, tag_css = action_tag(row)
    stage_class = _stage_card_class(stage_raw)
    status_css = LABELS.get(label, LABELS["Developing"])["css"]
    rank_text, rank_css = rank_trend_text(row, stock_rank)
    industry_text = str(row.get("Industry", "Unknown")).strip() or "Unknown"

    change_html = ""
    if pct is not None:
        cls = "change-up" if pct > 0 else "change-down"
        change_html = f"<span class='{cls}'>{pct:+.2f}%</span>"
    elif show_change_text:
        change_html = f"<span class='mini-pill'>{show_change_text}</span>"

    quick_html = ""
    if show_quick_read:
        quick_html = f"<div class='stock-subline'><b>Quick read:</b> {explanation}</div>"

    rank_html = f"<div class='stock-rank {rank_css}'>{rank_text}</div>" if show_rank else ""

    st.markdown(
        f"""
<div class="stock-shell {stage_class}">
  <div class="stock-topline">
    <div>
      <div class="stock-name">{company} ({ticker})</div>
      <div class="stock-meta">{stage_raw} • {trend} • {phase}</div>
      <div class="stock-industry">{industry_text}</div>
    </div>
    {rank_html}
  </div>
  <div class="stock-insight">{explanation}</div>
  {quick_html}
  <div class="stock-footer">
    <div class="pill-row">
      <span class="status-pill {status_css}">{label}</span>
      <span class="action-pill {tag_css}">{tag_text}</span>
      {change_html}
    </div>
  </div>
</div>
""",
        unsafe_allow_html=True,
    )

    b1, b2 = st.columns(2)
    with b1:
        if st.button("Add to Watchlist", use_container_width=True, key=f"{key_prefix}_watch"):
            add_to_named_list("watchlist_names", company, f"Added {company} to Watchlist. Check in Portfolio tab.")
    with b2:
        if st.button("Add to Alert", use_container_width=True, key=f"{key_prefix}_alert"):
            add_to_named_list("alert_watch_names", company, f"Added {company} to Alerts. Check in Portfolio tab.")


def render_sticky_topbar(current_market_tone: str, stage_counts: dict, combined_df: pd.DataFrame, industry_df: pd.DataFrame):
    top_industry = top_industry_text(industry_df, 1)
    market_story_text = market_story(current_market_tone, combined_df, industry_df)
    st.markdown(
        f"""
<div class="sticky-shell">
  <div class="topbar-grid">
    <div class="hero-card">
      <div class="kicker">Market tone</div>
      <div class="big-number">{current_market_tone}</div>
      <div class="market-story">{market_story_text}</div>
    </div>
    <div class="summary-card">
      <div class="kicker">Top group</div>
      <div class="big-number">{top_industry}</div>
      <div class="muted">Current leading industry</div>
    </div>
    <div class="summary-card">
      <div class="kicker">Stage 2</div>
      <div class="big-number">{stage_counts['Stage 2']}</div>
      <div class="muted">Advancing trend candidates</div>
    </div>
    <div class="summary-card">
      <div class="kicker">Stage 4</div>
      <div class="big-number">{stage_counts['Stage 4']}</div>
      <div class="muted">Declining trend candidates</div>
    </div>
  </div>
</div>
""",
        unsafe_allow_html=True,
    )


def render_decision_banner(current_market_tone: str):
    focus, avoid, watch = decision_texts(current_market_tone)
    st.markdown(
        f"""
<div class="decision-banner">
  <div class="decision-title">Decision first</div>
  <div class="muted">Use this dashboard as a fast filter, not a data dump.</div>
  <div class="decision-grid">
    <div class="decision-pill">
      <div class="decision-label">Focus today</div>
      <div class="decision-text">{focus}</div>
    </div>
    <div class="decision-pill">
      <div class="decision-label">Avoid</div>
      <div class="decision-text">{avoid}</div>
    </div>
    <div class="decision-pill">
      <div class="decision-label">Watch</div>
      <div class="decision-text">{watch}</div>
    </div>
  </div>
</div>
""",
        unsafe_allow_html=True,
    )


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

for state_key in ["watchlist_names", "alert_watch_names", "portfolio_names", "custom_portfolio_names"]:
    st.session_state.setdefault(state_key, [])
st.session_state.setdefault("portfolio_chart_index", 0)
st.session_state.setdefault("portfolio_selection", "Custom")
st.session_state.setdefault("portfolio_selection_prev", "Custom")
st.session_state.setdefault("selected_stock_index", 0)

daily_dir = f"{outdir}/charts/daily"
weekly_dir = f"{outdir}/charts/weekly"
company_map = company_choices(combined)
changes["priority_score"] = changes.apply(priority_score, axis=1) if not changes.empty else pd.Series(dtype=float)
combined["priority_score"] = combined.apply(priority_score, axis=1)
top_changed_df, changes_summary = build_today_changes(changes, industry_changes)
changed_tickers = set(top_changed_df["ticker"].dropna().tolist()) if not top_changed_df.empty and "ticker" in top_changed_df.columns else set()
priority_ranked = combined.sort_values(["priority_score", "final_combined_score"], ascending=[False, False]).reset_index(drop=True)
top_stocks_today = priority_ranked[~priority_ranked["ticker"].isin(changed_tickers)].head(5).copy()
alert_candidates = build_alert_candidates(combined, changes)
stage_counts = stage_count_summary(combined)
INDUSTRY_PORTFOLIOS = get_industry_portfolio_options(industry, combined, limit=21)


def get_stock_rank(ticker: str) -> str:
    return rank_lookup(top_movers, ticker, ["current_rank"])


def get_display_stock_rank(ticker: str) -> str:
    return get_stock_rank(ticker)


st.title("Market Structure Radar")
view_mode = st.radio("View mode", ["Beginner", "Pro"], horizontal=True, index=0)
show_pro_quick_read = view_mode == "Pro"
show_ranks = view_mode == "Pro"
render_sticky_topbar(market_tone(regime, combined), stage_counts, combined, industry)

tabs = st.tabs(["Home", "Stocks", "Movers", "Market", "How to Use", "Portfolio", "Alerts", "Advanced", "Disclaimer"])

with tabs[0]:
    current_market_tone = market_tone(regime, combined)
    render_decision_banner(current_market_tone)
    st.markdown("### Today’s summary")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        render_summary_card("Market tone", current_market_tone, "Use this before reviewing any stock")
    with c2:
        render_summary_card("New Strong", str(changes_summary["New Strong"]), "Stage 2 leaders improving materially")
    with c3:
        render_summary_card("Entered Stage 2", str(changes_summary["Entered Stage 2"]), "New advancing trend transitions")
    with c4:
        render_summary_card("Top industries", top_industry_text(industry), "Current leadership groups")

    left, right = st.columns([1.15, 1])
    with left:
        st.markdown("### Top names that changed")
        if top_changed_df.empty:
            st.info("No major stock changes found in the latest run.")
        else:
            for idx, r in top_changed_df.iterrows():
                stock_rank = get_stock_rank(r["ticker"])
                card(r, key_prefix=f"home_changed_{idx}", stock_rank=stock_rank, show_quick_read=show_pro_quick_read, show_rank=show_ranks, show_change_text=r["what_changed"])
    with right:
        st.markdown("### Focus list")
        for idx, r in top_stocks_today.iterrows():
            stock_rank = get_stock_rank(r["ticker"])
            card(r, key_prefix=f"home_focus_{idx}", stock_rank=stock_rank, show_quick_read=show_pro_quick_read, show_rank=show_ranks)

    st.divider()
    st.markdown("### Guided workflow")
    workflow_cols = st.columns(len(guided_workflow_steps(current_market_tone)))
    for col, step_text in zip(workflow_cols, guided_workflow_steps(current_market_tone)):
        with col:
            st.markdown(f"<div class='assist-box'><div class='assist-text'>{step_text}</div></div>", unsafe_allow_html=True)
    render_disclosure()

with tabs[1]:
    render_decision_banner(market_tone(regime, combined))
    ranked = priority_ranked.copy()
    stock_search = st.text_input("Search stock", placeholder="Type company or ticker")
    filtered = ranked.copy()
    if stock_search:
        q = stock_search.strip().lower()
        filtered = filtered[
            filtered["Company Name"].astype(str).str.lower().str.contains(q, na=False)
            | filtered["ticker"].astype(str).str.lower().str.contains(q, na=False)
        ]
    stage_filter, label_filter, industry_filter = st.columns(3)
    with stage_filter:
        selected_stage = st.selectbox("Stage filter", ["All", "Stage 1", "Stage 2", "Stage 3", "Stage 4"])
    with label_filter:
        selected_label = st.selectbox("Strength filter", ["All", "Strong", "Developing", "Cautious", "Weak"])
    with industry_filter:
        industry_options = ["All"] + sorted(filtered["Industry"].dropna().astype(str).unique().tolist())
        selected_industry = st.selectbox("Industry filter", industry_options)

    if selected_stage != "All":
        filtered = filtered[filtered["stage"] == selected_stage]
    if selected_label != "All":
        filtered = filtered[filtered["label"] == selected_label]
    if selected_industry != "All":
        filtered = filtered[filtered["Industry"].astype(str) == selected_industry]

    names = filtered["Company Name"].dropna().astype(str).tolist()
    if not names:
        st.info("No stocks matched the current filters.")
    else:
        st.session_state["selected_stock_index"] = max(0, min(st.session_state["selected_stock_index"], len(names) - 1))
        current_index = st.session_state["selected_stock_index"]
        selected_name = st.selectbox("Selected stock", names, index=current_index, key=f"stocks_select_name_ordered_{current_index}")
        selected_index = names.index(selected_name)
        if selected_index != current_index:
            st.session_state["selected_stock_index"] = selected_index
            st.rerun()

        row = filtered.iloc[st.session_state["selected_stock_index"]]
        ticker_short = str(row["ticker"]).replace(".NS", "")
        st.markdown("### Selected stock")
        stock_rank = get_stock_rank(row["ticker"])
        card(row, key_prefix="stocks_selected", stock_rank=stock_rank, show_quick_read=show_pro_quick_read, show_rank=show_ranks)

        dpath = resolve_chart_path(daily_dir, row["ticker"], "_daily.png")
        wpath = resolve_chart_path(weekly_dir, row["ticker"], "_weekly.png")
        a, b = st.columns(2)
        with a:
            daily_rank = get_display_stock_rank(row["ticker"])
            st.markdown(f"#### Daily • {ticker_short} • {row.get('stage', '')} • Rank {daily_rank}")
            if dpath:
                st.image(safe_image_bytes(dpath), use_container_width=True)
            else:
                st.info("Daily chart not available.")
        with b:
            weekly_rank = get_display_stock_rank(row["ticker"])
            st.markdown(f"#### Weekly • {ticker_short} • {row.get('stage', '')} • Rank {weekly_rank}")
            if wpath:
                st.image(safe_image_bytes(wpath), use_container_width=True)
            else:
                st.info("Weekly chart not available.")

        nav1, nav2 = st.columns(2)
        with nav1:
            prev_btn = st.button("Previous", use_container_width=True, disabled=(st.session_state["selected_stock_index"] == 0), key="stocks_prev_bottom")
        with nav2:
            next_btn = st.button("Next", use_container_width=True, disabled=(st.session_state["selected_stock_index"] >= len(names) - 1), key="stocks_next_bottom")
        if prev_btn and st.session_state["selected_stock_index"] > 0:
            st.session_state["selected_stock_index"] -= 1
            st.rerun()
        if next_btn and st.session_state["selected_stock_index"] < len(names) - 1:
            st.session_state["selected_stock_index"] += 1
            st.rerun()

        st.divider()
        st.markdown("### Browse more stocks")
        for idx, r in filtered.head(20).iterrows():
            stock_rank = get_stock_rank(r["ticker"])
            card(r, key_prefix=f"stocks_list_{idx}", stock_rank=stock_rank, show_quick_read=show_pro_quick_read, show_rank=show_ranks)
    render_disclosure()

with tabs[2]:
    st.markdown("### Movers")
    if moves.empty:
        st.info("Price move data not found yet.")
    else:
        window_map = {"1 Day": "change_1d_pct", "1 Week": "change_1w_pct", "1 Month": "change_1m_pct", "YTD": "change_ytd_pct"}
        selected = st.radio("Move window", list(window_map.keys()), horizontal=True, index=0)
        col = window_map[selected]
        mv = moves.copy()
        mv[col] = pd.to_numeric(mv[col], errors="coerce")
        mv = mv.dropna(subset=[col])
        mv["priority_score"] = mv.apply(priority_score, axis=1)
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f"### Biggest upward moves • {selected}")
            for idx, r in mv.sort_values([col, "priority_score"], ascending=[False, False]).head(10).iterrows():
                stock_rank = get_stock_rank(r["ticker"])
                card(r, key_prefix=f"movers_up_{idx}", pct=float(r[col]), stock_rank=stock_rank, show_quick_read=show_pro_quick_read, show_rank=show_ranks)
        with c2:
            st.markdown(f"### Major downward moves • {selected}")
            for idx, r in mv.sort_values([col, "priority_score"], ascending=[True, False]).head(10).iterrows():
                stock_rank = get_stock_rank(r["ticker"])
                card(r, key_prefix=f"movers_down_{idx}", pct=float(r[col]), stock_rank=stock_rank, show_quick_read=show_pro_quick_read, show_rank=show_ranks)
    render_disclosure()

with tabs[3]:
    st.markdown("### Market")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        render_summary_card("Stage 1", str(stage_counts["Stage 1"]), "Base / repair")
    with c2:
        render_summary_card("Stage 2", str(stage_counts["Stage 2"]), "Advancing trend")
    with c3:
        render_summary_card("Stage 3", str(stage_counts["Stage 3"]), "Topping / transition")
    with c4:
        render_summary_card("Stage 4", str(stage_counts["Stage 4"]), "Declining trend")

    if industry.empty:
        st.info("Industry data not available.")
    else:
        view = industry.copy()
        stage2 = stage2_count_by_industry(combined)
        if "Industry" in view.columns:
            view = view.merge(stage2, on="Industry", how="left")
        sort_col = None
        for candidate in ["avg_combined_score", "current_rank", "rs_rank"]:
            if candidate in view.columns:
                sort_col = candidate
                break
        if sort_col is not None:
            view[sort_col] = pd.to_numeric(view[sort_col], errors="coerce")
            view = view.sort_values(sort_col, ascending=(sort_col != "avg_combined_score"), na_position="last").reset_index(drop=True)
            view["Rank"] = range(1, len(view) + 1)
        if "Stage 2 Stocks" in view.columns:
            view["Stage 2 Stocks"] = view["Stage 2 Stocks"].fillna(0).astype(int)
        left, right = st.columns(2)
        with left:
            st.markdown("### Industry strength")
            st.dataframe(view[[c for c in ["Industry", "Rank", "Stage 2 Stocks"] if c in view.columns]], use_container_width=True, hide_index=True, height=520)
        with right:
            st.markdown("### Industry changes")
            if industry_changes.empty:
                st.info("Industry changes data not available.")
            else:
                cols = [c for c in ["Industry", "current_rank", "prev_rank", "rank_change"] if c in industry_changes.columns]
                renamed = industry_changes[cols].rename(columns={"current_rank": "Current Rank", "prev_rank": "Previous Rank", "rank_change": "Rank Change"})
                st.dataframe(renamed, use_container_width=True, hide_index=True, height=520)
    render_disclosure()

with tabs[4]:
    current_market_tone = market_tone(regime, combined)
    left, right = st.columns([1.05, 0.95])
    with left:
        st.markdown(
            f"""
<div class="learn-card">
  <div class="section-title">How to read this dashboard</div>
  <div class="small-help">Start with market tone. Today it reads <b>{current_market_tone}</b>.</div>
  <ul>
    <li>Scan Strong Stage 2 names first and use Stage 1 names mainly as watchlist bases.</li>
    <li>Use the quick read before opening charts.</li>
    <li>Check daily and weekly charts together. Agreement matters more than a single chart.</li>
  </ul>
</div>
<div class="learn-card">
  <div class="section-title">How the stage model should be read</div>
  <ul>
    <li><b>Stage 1</b>: base / repair zone. Not a confirmed uptrend yet.</li>
    <li><b>Stage 2</b>: advancing trend. This is the main leadership phase.</li>
    <li><b>Stage 3</b>: topping or transition. Failed rallies and distribution risk matter more here.</li>
    <li><b>Stage 4</b>: declining trend. Weak structure remains dominant.</li>
  </ul>
</div>
<div class="learn-card">
  <div class="section-title">SEBI-safe language built into the app</div>
  <ul>
    <li>The app describes structure, trend, rank and improvement.</li>
    <li>It avoids direct buy, sell, target, stop-loss or allocation advice.</li>
    <li>Use terms like <b>advancing trend</b>, <b>tightening base</b>, <b>transition structure</b>, or <b>weak structure</b>.</li>
  </ul>
</div>
""",
            unsafe_allow_html=True,
        )
    with right:
        img = Path(help_image_path)
        if img.exists():
            st.image(str(img), caption="Reference image for the four market phases", use_container_width=True)
        else:
            st.info("Stage image not found.")
    render_disclosure()

with tabs[5]:
    st.markdown("### Portfolio")
    watch_col, alert_col = st.columns(2)
    with watch_col:
        st.markdown("#### Watchlist")
        if not st.session_state["watchlist_names"]:
            st.info("No watchlist stocks yet. Use 'Add to Watchlist' on any stock card.")
        else:
            watch_df = combined[combined["Company Name"].isin(st.session_state["watchlist_names"])].copy().sort_values(["priority_score", "final_combined_score"], ascending=[False, False])
            for idx, r in watch_df.iterrows():
                stock_rank = get_stock_rank(r["ticker"])
                card(r, key_prefix=f"portfolio_watch_{idx}", stock_rank=stock_rank, show_quick_read=show_pro_quick_read, show_rank=show_ranks)
    with alert_col:
        st.markdown("#### Alert watch")
        if not st.session_state["alert_watch_names"]:
            st.info("No alert stocks yet. Use 'Add to Alert' on any stock card.")
        else:
            alert_watch_df = combined[combined["Company Name"].isin(st.session_state["alert_watch_names"])].copy().sort_values(["priority_score", "final_combined_score"], ascending=[False, False])
            for idx, r in alert_watch_df.iterrows():
                stock_rank = get_stock_rank(r["ticker"])
                card(r, key_prefix=f"portfolio_alert_{idx}", stock_rank=stock_rank, show_quick_read=show_pro_quick_read, show_rank=show_ranks)

    st.divider()
    portfolio_options = ["Custom", "Top 15", "New Breakouts", "New Strong", "Strong", "Cautious", "Weak", "Stage 1", "Stage 2", "Stage 3", "Stage 4"] + INDUSTRY_PORTFOLIOS
    selected_portfolio = st.selectbox("Portfolio basket", portfolio_options, key="portfolio_selection")
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
    selected_to_add = st.selectbox("Add stock to basket", [""] + available, key="portfolio_add_name", disabled=portfolio_full)
    if portfolio_full:
        st.warning(f"Portfolio is limited to {MAX_PORTFOLIO_STOCKS} stocks.")
    if st.button("Add to portfolio", use_container_width=True, key="portfolio_add_btn", disabled=portfolio_full) and selected_to_add:
        st.session_state["portfolio_names"] = dedupe_names(st.session_state["portfolio_names"] + [selected_to_add], limit=MAX_PORTFOLIO_STOCKS)
        if selected_portfolio == "Custom":
            st.session_state["custom_portfolio_names"] = dedupe_names(st.session_state["portfolio_names"], limit=MAX_PORTFOLIO_STOCKS)
        if st.session_state["portfolio_chart_index"] >= len(st.session_state["portfolio_names"]):
            st.session_state["portfolio_chart_index"] = max(0, len(st.session_state["portfolio_names"]) - 1)
        show_message(f"Added {selected_to_add} to Portfolio basket.")
        st.rerun()

    if not st.session_state["portfolio_names"]:
        st.info("No portfolio basket stocks yet.")
    else:
        current = combined[combined["Company Name"].isin(st.session_state["portfolio_names"])].copy().sort_values(["priority_score", "final_combined_score"], ascending=[False, False]).head(MAX_PORTFOLIO_STOCKS).copy()
        p_stage_counts = current["stage"].value_counts() if "stage" in current.columns else pd.Series(dtype=int)
        c1, c2, c3, c4, c5 = st.columns(5)
        with c1:
            render_summary_card("Total stocks", str(len(current)), "Stocks in current basket")
        with c2:
            render_summary_card("Stage 1", str(int(p_stage_counts.get("Stage 1", 0))), "Base / repair")
        with c3:
            render_summary_card("Stage 2", str(int(p_stage_counts.get("Stage 2", 0))), "Advancing trend")
        with c4:
            render_summary_card("Stage 3", str(int(p_stage_counts.get("Stage 3", 0))), "Topping / transition")
        with c5:
            render_summary_card("Stage 4", str(int(p_stage_counts.get("Stage 4", 0))), "Declining trend")

        st.markdown("### Portfolio assistant")
        for msg in portfolio_assistant(current):
            st.markdown(f"<div class='assist-box'><div class='assist-text'>{msg}</div></div>", unsafe_allow_html=True)

        st.divider()
        st.markdown("### Basket holdings")
        for idx, r in current.iterrows():
            stock_rank = get_stock_rank(r["ticker"])
            card(r, key_prefix=f"portfolio_holdings_{idx}", stock_rank=stock_rank, show_quick_read=show_pro_quick_read, show_rank=show_ranks)

        removable = [""] + sorted(st.session_state["portfolio_names"])
        selected_remove = st.selectbox("Remove stock from basket", removable, key="portfolio_remove_name")
        if st.button("Remove from portfolio", use_container_width=True, key="portfolio_remove_btn") and selected_remove:
            st.session_state["portfolio_names"] = [x for x in st.session_state["portfolio_names"] if x != selected_remove]
            if selected_portfolio == "Custom":
                st.session_state["custom_portfolio_names"] = dedupe_names(st.session_state["portfolio_names"], limit=MAX_PORTFOLIO_STOCKS)
            st.session_state["portfolio_chart_index"] = min(st.session_state["portfolio_chart_index"], max(0, len(st.session_state["portfolio_names"]) - 1))
            show_message(f"Removed {selected_remove} from Portfolio basket.")
            st.rerun()

        portfolio_ordered = current.reset_index(drop=True)
        if not portfolio_ordered.empty:
            st.divider()
            st.markdown("### Portfolio charts")
            st.session_state["portfolio_chart_index"] = max(0, min(st.session_state["portfolio_chart_index"], len(portfolio_ordered) - 1))
            prow = portfolio_ordered.iloc[st.session_state["portfolio_chart_index"]]
            pticker_short = str(prow["ticker"]).replace(".NS", "")

            pc1, pc2 = st.columns(2)
            with pc1:
                pdaily_rank = get_display_stock_rank(prow["ticker"])
                st.markdown(f"#### Daily • {pticker_short} • {prow.get('stage', '')} • Stock Rank {pdaily_rank}")
                pdpath = resolve_chart_path(daily_dir, prow["ticker"], "_daily.png")
                if pdpath:
                    st.image(safe_image_bytes(pdpath), use_container_width=True)
                else:
                    st.info("Daily chart not available.")
            with pc2:
                pweekly_rank = get_display_stock_rank(prow["ticker"])
                st.markdown(f"#### Weekly • {pticker_short} • {prow.get('stage', '')} • Stock Rank {pweekly_rank}")
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

with tabs[6]:
    st.markdown("### Alerts")
    alert_timeline = alert_candidates.head(8).copy() if not alert_candidates.empty else pd.DataFrame()
    if alert_timeline.empty:
        st.info("No alert candidates found in the latest data.")
    else:
        st.markdown("#### Latest alert timeline")
        timeline_html = "<div class='timeline-card'>"
        for idx, (_, r) in enumerate(alert_timeline.iterrows(), start=1):
            stock_rank = get_stock_rank(r["ticker"])
            timeline_html += (
                f"<div class='timeline-line'>"
                f"<div class='timeline-time'>Alert {idx}</div>"
                f"<div class='timeline-text'>{r.get('Company Name', r.get('ticker', 'Stock'))} • {r['alert_type']} • Rank {stock_rank}</div>"
                f"<div class='small-help'>{r['alert_reason']}</div>"
                f"</div>"
            )
        timeline_html += "</div>"
        st.markdown(timeline_html, unsafe_allow_html=True)

        st.markdown("#### Triggered alert candidates")
        for idx, r in alert_candidates.iterrows():
            stock_rank = get_stock_rank(r["ticker"])
            card(r, key_prefix=f"alerts_card_{idx}", stock_rank=stock_rank, show_quick_read=show_pro_quick_read, show_rank=show_ranks, show_change_text=f"{r['alert_type']} • {r['alert_reason']}")

    st.divider()
    st.markdown("#### How to add alerts for users")
    a1, a2, a3 = st.columns(3)
    with a1:
        st.markdown('<div class="assist-box"><div class="section-title">1. Store user rules</div><div class="assist-text">Save watchlists and alert rules in a database: entered Stage 2, breakout, rank improvement or weak structure.</div></div>', unsafe_allow_html=True)
    with a2:
        st.markdown('<div class="assist-box"><div class="section-title">2. Run after each scan</div><div class="assist-text">After CSV generation, compare the latest snapshot vs previous snapshot and create alert events only for new changes.</div></div>', unsafe_allow_html=True)
    with a3:
        st.markdown('<div class="assist-box"><div class="section-title">3. Send neutral notifications</div><div class="assist-text">Use email, Telegram, WhatsApp or push notifications with neutral wording like “entered Stage 2” or “rank improved”.</div></div>', unsafe_allow_html=True)
    render_disclosure()

with tabs[7]:
    def keep_simple(df: pd.DataFrame) -> pd.DataFrame:
        wanted = [c for c in ["Company Name", "ticker", "label", "classification", "stage", "Industry", "priority_score"] if c in df.columns]
        out = df[wanted].copy() if wanted else df.copy()
        if "classification" in out.columns and "label" not in out.columns:
            out["label"] = out["classification"]
            out = out.drop(columns=["classification"])
        if "ticker" in out.columns:
            out = out.rename(columns={"ticker": "Ticker", "label": "Classification", "priority_score": "Priority Score"})
            out["Ticker"] = out["Ticker"].astype(str).str.replace(".NS", "", regex=False)
        else:
            out = out.rename(columns={"label": "Classification", "priority_score": "Priority Score"})
        return out

    st.markdown("### Advanced")
    with st.expander("Overall ranked", expanded=True):
        st.dataframe(keep_simple(combined.sort_values(["priority_score", "final_combined_score"], ascending=[False, False])), use_container_width=True, hide_index=True, height=360)
    with st.expander("Daily ranked", expanded=False):
        st.dataframe(keep_simple(daily_df), use_container_width=True, hide_index=True, height=320)
    with st.expander("Weekly ranked", expanded=False):
        st.dataframe(keep_simple(weekly_df), use_container_width=True, hide_index=True, height=320)
    with st.expander("Stock changes", expanded=False):
        st.dataframe(keep_simple(changes), use_container_width=True, hide_index=True, height=320)
    with st.expander("Industry changes", expanded=False):
        cols = [c for c in ["Industry", "current_rank", "prev_rank", "rank_change"] if c in industry_changes.columns]
        st.dataframe(industry_changes[cols].rename(columns={"current_rank": "Current Rank", "prev_rank": "Previous Rank", "rank_change": "Rank Change"}), use_container_width=True, hide_index=True, height=320)
    render_disclosure()

with tabs[8]:
    st.markdown("### Disclaimer")
    st.write("This tool is for informational purposes only. It presents rule-based stage classifications and market summaries. In this model, Stage 1 means a base or repair zone, while Stage 2 is the main advancing phase. It does not provide personalized investment advice, suitability analysis, buy calls, sell calls, or allocation recommendations.")
    render_disclosure()
