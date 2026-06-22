import re
import traceback
from pathlib import Path
from typing import Iterable

import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Market Structure Radar",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ============================================================
# Ultra-stable Streamlit version
# Key design choice: no st.tabs.
# Streamlit executes every tab body on every rerun; this version renders only
# the selected page so chart-heavy pages cannot crash the whole app at startup.
# ============================================================

APP_TITLE = "Market Structure Radar"
OUTDIR = Path("outputs")
DAILY_CHART_DIR = OUTDIR / "charts" / "daily"
WEEKLY_CHART_DIR = OUTDIR / "charts" / "weekly"
MAX_TABLE_ROWS = 150
MAX_CARD_ROWS = 25
MAX_IMAGE_MB = 3.0

CSS = """
<style>
.block-container {padding-top: 0.55rem; padding-left: 0.75rem; padding-right: 0.75rem; max-width: 1400px;}
[data-testid="stSidebar"], section[data-testid="stSidebar"], [data-testid="collapsedControl"] {display:none;}
.hero-card, .stock-card, .info-card {
  border: 1px solid rgba(128,128,128,0.22);
  border-radius: 18px;
  padding: 0.85rem 0.95rem;
  background: rgba(255,255,255,0.035);
  margin-bottom: 0.55rem;
}
.hero-title {font-size: 1.45rem; font-weight: 900; line-height: 1.1;}
.kicker {font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.06em; color: rgba(255,255,255,0.68);}
.big-number {font-size: 1.42rem; font-weight: 900; margin-top: 0.06rem;}
.muted {color: rgba(255,255,255,0.70); font-size: 0.88rem;}
.stock-title {font-size: 1.02rem; font-weight: 800; line-height: 1.18;}
.meta-line {font-size: 0.88rem; color: rgba(255,255,255,0.72); margin-top: 0.1rem;}
.badge {display:inline-block; border-radius:999px; padding:0.18rem 0.48rem; font-size:0.74rem; font-weight:800; margin-top:0.2rem; margin-right:0.25rem; border: 1px solid rgba(255,255,255,0.18);}
.badge-strong {background: rgba(30,201,119,0.14); color:#1ec977;}
.badge-dev {background: rgba(240,180,41,0.14); color:#f0b429;}
.badge-cautious {background: rgba(255,159,67,0.14); color:#ff9f43;}
.badge-weak {background: rgba(255,107,107,0.14); color:#ff6b6b;}
.stage-1 {background: rgba(55,95,220,0.10);}
.stage-2 {background: rgba(0,179,179,0.10);}
.stage-3 {background: rgba(212,160,23,0.10);}
.stage-4 {background: rgba(170,80,180,0.10);}
.warning-box {border-left: 4px solid rgba(240,180,41,0.65); background: rgba(240,180,41,0.08); border-radius:12px; padding:0.75rem 0.9rem; margin:0.7rem 0;}
@media (max-width: 768px) {
  .block-container {padding-left: 0.38rem; padding-right: 0.38rem;}
  .hero-title {font-size: 1.22rem;}
  .stock-title {font-size: 0.95rem;}
}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)


# ============================================================
# Safe utilities
# ============================================================

def safe_execute(label: str, fn, fallback=None):
    try:
        return fn()
    except Exception:
        st.error(f"{label} failed, but the app stayed alive.")
        with st.expander(f"Technical details: {label}"):
            st.code(traceback.format_exc())
        return fallback


DASHBOARD_COLUMNS = [
    "Company Name", "company_name", "Company", "company", "Name", "stock_name", "Stock Name", "Company Name_x", "Company Name_y",
    "ticker", "Ticker", "symbol", "Symbol", "SYMBOL", "nse_symbol",
    "Industry", "industry", "Industry Group", "industry_group", "sector", "Sector", "Industry_x", "Industry_y",
    "stage", "Stage", "current_stage", "Current Stage", "model_stage",
    "label", "classification", "current_rank", "rank", "rs_rank", "daily_rank", "weekly_rank", "final_rank", "combined_rank", "stock_rank",
    "final_combined_score", "avg_combined_score", "combined_score", "rank_change",
    "change_1d_pct", "change_1w_pct", "change_1m_pct", "change_ytd_pct", "rs_3m_pct", "rs_6m_pct",
    "action", "trade_side", "action_confidence", "long_score", "short_score", "rationale",
    "entered_stage_2", "new_weekly_breakout", "new_daily_breakout",
    "F&O", "FNO", "FO", "F&O Stock", "is_fo", "is_fno", "fno", "fo", "FnO",
    "regime_label", "market_regime", "date", "as_of_date"
]


@st.cache_data(show_spinner=False, ttl=1800, max_entries=24)
def read_csv_cached(path: str, mtime_ns: int) -> pd.DataFrame:
    # Fast path: read only columns the dashboard actually displays.
    # If none match, fall back to the full file so unusual files still work.
    try:
        header = pd.read_csv(path, nrows=0)
        usecols = [c for c in header.columns if c in DASHBOARD_COLUMNS]
        if usecols:
            return pd.read_csv(path, usecols=usecols)
    except Exception:
        pass
    return pd.read_csv(path)


def safe_read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    try:
        return read_csv_cached(str(path), path.stat().st_mtime_ns)
    except Exception:
        return pd.DataFrame()


def first_existing(columns: Iterable[str], candidates: list[str]) -> str | None:
    columns_set = {str(c): c for c in columns}
    lower_map = {str(c).strip().lower().replace(" ", "_"): c for c in columns}
    for cand in candidates:
        if cand in columns_set:
            return columns_set[cand]
        key = cand.strip().lower().replace(" ", "_")
        if key in lower_map:
            return lower_map[key]
    return None


def normalize_symbol(value) -> str:
    if pd.isna(value):
        return ""
    text = str(value).strip().upper()
    text = text.replace(".NS", "")
    return text


def normalize_stage(value) -> str:
    text = str(value).strip() if not pd.isna(value) else "Unknown"
    text_lower = text.lower().replace("_", " ").replace("-", " ")
    mapping = {
        "1": "Stage 1", "stage 1": "Stage 1", "s1": "Stage 1",
        "2": "Stage 2", "stage 2": "Stage 2", "s2": "Stage 2",
        "3": "Stage 3", "stage 3": "Stage 3", "s3": "Stage 3",
        "4": "Stage 4", "stage 4": "Stage 4", "s4": "Stage 4",
    }
    return mapping.get(text_lower, text if text and text.lower() not in {"nan", "none"} else "Unknown")


def normalize_df(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame()
    out = df.copy()

    company_col = first_existing(out.columns, [
        "Company Name", "company_name", "Company", "company", "Name", "stock_name", "Stock Name", "Company Name_x", "Company Name_y"
    ])
    ticker_col = first_existing(out.columns, ["ticker", "Ticker", "symbol", "Symbol", "SYMBOL", "nse_symbol"])
    industry_col = first_existing(out.columns, ["Industry", "industry", "Industry Group", "industry_group", "sector", "Sector", "Industry_x", "Industry_y"])
    stage_col = first_existing(out.columns, ["stage", "Stage", "current_stage", "Current Stage", "model_stage"])

    rename = {}
    if company_col and company_col != "Company Name":
        rename[company_col] = "Company Name"
    if ticker_col and ticker_col != "ticker":
        rename[ticker_col] = "ticker"
    if industry_col and industry_col != "Industry":
        rename[industry_col] = "Industry"
    if stage_col and stage_col != "stage":
        rename[stage_col] = "stage"
    if rename:
        out = out.rename(columns=rename)

    if "ticker" not in out.columns:
        out["ticker"] = ""
    out["ticker"] = out["ticker"].astype(str).str.strip()

    if "Company Name" not in out.columns:
        out["Company Name"] = out["ticker"]
    out["Company Name"] = out["Company Name"].astype(str).str.strip()
    out.loc[out["Company Name"].isin(["", "nan", "None"]), "Company Name"] = out["ticker"]
    out.loc[out["Company Name"].eq(""), "Company Name"] = "Unknown"

    if "Industry" not in out.columns:
        out["Industry"] = "Unknown"
    out["Industry"] = out["Industry"].astype(str).str.strip()
    out.loc[out["Industry"].isin(["", "nan", "None"]), "Industry"] = "Unknown"

    if "stage" not in out.columns:
        out["stage"] = "Unknown"
    out["stage"] = out["stage"].apply(normalize_stage)

    for col in [
        "current_rank", "rank", "rs_rank", "daily_rank", "weekly_rank", "final_rank", "combined_rank", "stock_rank",
        "final_combined_score", "avg_combined_score", "combined_score", "rank_change", "change_1d_pct", "change_1w_pct",
        "change_1m_pct", "rs_3m_pct", "rs_6m_pct", "action_confidence", "long_score", "short_score"
    ]:
        if col in out.columns:
            out[col] = pd.to_numeric(out[col], errors="coerce")

    if "current_rank" not in out.columns:
        for alt in ["rank", "rs_rank", "daily_rank", "weekly_rank", "final_rank", "combined_rank", "stock_rank"]:
            if alt in out.columns:
                out["current_rank"] = out[alt]
                break
    if "current_rank" not in out.columns:
        out["current_rank"] = pd.NA
    out["current_rank"] = pd.to_numeric(out["current_rank"], errors="coerce")

    if "label" not in out.columns:
        if "classification" in out.columns:
            out["label"] = out["classification"].astype(str)
        else:
            out["label"] = out.apply(classify_label, axis=1)

    if "display_name" not in out.columns:
        out["display_name"] = out.apply(display_name, axis=1)

    return out


def boolish(value) -> bool:
    if isinstance(value, bool):
        return value
    if pd.isna(value):
        return False
    return str(value).strip().lower() in {"1", "true", "yes", "y", "t", "fo", "f&o", "fno", "f and o", "f_and_o"}


def classify_label(row: pd.Series) -> str:
    stage = str(row.get("stage", "Unknown"))
    score = pd.to_numeric(row.get("final_combined_score", row.get("avg_combined_score", row.get("combined_score"))), errors="coerce")
    rs3 = pd.to_numeric(row.get("rs_3m_pct"), errors="coerce")
    rs6 = pd.to_numeric(row.get("rs_6m_pct"), errors="coerce")

    if stage == "Stage 2":
        return "Strong" if pd.notna(score) and score >= 70 else "Developing"
    if stage == "Stage 4":
        return "Weak"
    if stage == "Stage 3":
        return "Cautious"
    if pd.notna(rs3) and pd.notna(rs6) and rs3 < 0 and rs6 < 0:
        return "Weak"
    return "Developing"


def display_name(row: pd.Series) -> str:
    company = str(row.get("Company Name", "") or "").strip()
    ticker = str(row.get("ticker", "") or "").replace(".NS", "").strip()
    if company and ticker and ticker.upper() not in company.upper():
        return f"{company} ({ticker})"
    return company or ticker or "Unknown"


def rank_text(row: pd.Series) -> str:
    val = pd.to_numeric(row.get("current_rank"), errors="coerce")
    return str(int(val)) if pd.notna(val) else "n/a"


def score_value(row: pd.Series) -> int:
    score = pd.to_numeric(row.get("final_combined_score", row.get("avg_combined_score", row.get("combined_score"))), errors="coerce")
    if pd.notna(score):
        return int(max(0, min(100, round(score))))
    stage = str(row.get("stage", ""))
    return {"Stage 1": 40, "Stage 2": 70, "Stage 3": 45, "Stage 4": 25}.get(stage, 50)


def stage_class(stage: str) -> str:
    return {"Stage 1": "stage-1", "Stage 2": "stage-2", "Stage 3": "stage-3", "Stage 4": "stage-4"}.get(str(stage), "")


def badge_class(label: str) -> str:
    return {
        "Strong": "badge-strong",
        "Developing": "badge-dev",
        "Cautious": "badge-cautious",
        "Weak": "badge-weak",
    }.get(str(label), "badge-dev")


def stage_counts(df: pd.DataFrame) -> dict:
    counts = df["stage"].value_counts() if not df.empty and "stage" in df.columns else pd.Series(dtype="int64")
    return {s: int(counts.get(s, 0)) for s in ["Stage 1", "Stage 2", "Stage 3", "Stage 4"]}


def sort_ranked(df: pd.DataFrame, n: int | None = None) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame()
    out = df.copy()
    by = ["current_rank", "Company Name"]
    asc = [True, True]
    out = out.sort_values(by=[c for c in by if c in out.columns], ascending=asc[: len([c for c in by if c in out.columns])], na_position="last")
    return out.head(n) if n else out


def filter_fo(df: pd.DataFrame, fo_symbols: set[str]) -> pd.DataFrame:
    if df.empty:
        return df
    out = df.copy()
    fo_col = first_existing(out.columns, ["F&O", "FNO", "FO", "F&O Stock", "is_fo", "is_fno", "fno", "fo", "FnO"])
    mask = pd.Series(False, index=out.index)
    if fo_col:
        mask = mask | out[fo_col].apply(boolish)
    if fo_symbols and "ticker" in out.columns:
        mask = mask | out["ticker"].apply(normalize_symbol).isin(fo_symbols)
    if mask.any():
        return out[mask].copy()
    return out.iloc[0:0].copy()


def load_fo_symbols() -> set[str]:
    candidates = [
        Path("universe.csv"), Path("universe(1).csv"), Path("universe_with_FO.csv"), Path("universe_with_full_FO.csv"),
        OUTDIR / "universe.csv", OUTDIR / "universe_clean.csv", OUTDIR / "universe_with_FO.csv", OUTDIR / "universe_with_full_FO.csv",
    ]
    symbols: set[str] = set()
    for path in candidates:
        df = safe_read_csv(path)
        if df.empty:
            continue
        fo_col = first_existing(df.columns, ["F&O", "FNO", "FO", "F&O Stock", "is_fo", "is_fno", "fno", "fo", "FnO"])
        ticker_col = first_existing(df.columns, ["ticker", "Ticker", "symbol", "Symbol", "SYMBOL"])
        if fo_col and ticker_col:
            symbols.update(df.loc[df[fo_col].apply(boolish), ticker_col].apply(normalize_symbol).dropna().tolist())
    return {s for s in symbols if s}


def resolve_chart_path(chart_dir: Path, ticker: str, suffix: str) -> Path | None:
    if not chart_dir.exists() or not ticker:
        return None
    ticker = str(ticker).strip()
    raw = ticker.replace(".NS", "")
    candidates = []
    variants = {
        ticker, raw, ticker.replace(".", "_"), raw.replace(".", "_"),
        ticker.replace("&", "_"), raw.replace("&", "_"),
        ticker.replace("&", "AND"), raw.replace("&", "AND"),
        re.sub(r"[^A-Za-z0-9]+", "_", ticker), re.sub(r"[^A-Za-z0-9]+", "_", raw),
        re.sub(r"[^A-Za-z0-9]+", "", ticker), re.sub(r"[^A-Za-z0-9]+", "", raw),
    }
    for v in variants:
        if v:
            candidates.append(chart_dir / f"{v}{suffix}")
    for path in candidates:
        if path.exists():
            return path

    # Important: do not scan the whole chart folder here.
    # Streamlit Cloud becomes slow when hundreds of chart PNGs are globbed on each chart request.
    # Keep chart names close to: RELIANCE_daily.png / RELIANCE_weekly.png.
    return None


def show_image_limited(path: Path | None, caption: str = ""):
    if path is None or not path.exists():
        st.info("Chart not available.")
        return
    try:
        size_mb = path.stat().st_size / (1024 * 1024)
        if size_mb > MAX_IMAGE_MB:
            st.warning(f"Chart skipped because the image is {size_mb:.1f} MB. Regenerate smaller charts to avoid Streamlit memory crashes.")
            return
        st.image(str(path), caption=caption or None, use_container_width=True)
    except Exception:
        st.warning("Chart could not be displayed, but the app stayed alive.")


def render_card(row: pd.Series, extra: str = ""):
    stage = str(row.get("stage", "Unknown"))
    label = str(row.get("label", "Developing"))
    industry = str(row.get("Industry", "Unknown"))
    html = f"""
    <div class="stock-card {stage_class(stage)}">
      <div style="display:flex; justify-content:space-between; gap:0.7rem; align-items:flex-start;">
        <div style="min-width:0;">
          <div class="stock-title">{display_name(row)}</div>
          <div class="meta-line">{stage} • {industry}</div>
          <span class="badge {badge_class(label)}">{label}</span>
          <span class="badge">Score {score_value(row)}/100</span>
          {f'<div class="meta-line">{extra}</div>' if extra else ''}
        </div>
        <div style="text-align:right; min-width:72px;">
          <div class="kicker">Rank</div>
          <div class="big-number">{rank_text(row)}</div>
        </div>
      </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


def clean_table(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame()
    preferred = [
        "Company Name", "ticker", "Industry", "stage", "label", "current_rank", "final_combined_score", "avg_combined_score",
        "rank_change", "change_1d_pct", "change_1w_pct", "change_1m_pct", "rs_3m_pct", "rs_6m_pct", "action", "trade_side",
        "action_confidence", "rationale"
    ]
    cols = [c for c in preferred if c in df.columns]
    if not cols:
        cols = list(df.columns[:12])
    return df[cols].head(MAX_TABLE_ROWS)


# ============================================================
# Lazy data loading
# ============================================================

DATA_FILES = {
    "combined": OUTDIR / "vcp_combined_ranked.csv",
    "daily": OUTDIR / "vcp_daily_ranked.csv",
    "weekly": OUTDIR / "vcp_weekly_ranked.csv",
    "industry": OUTDIR / "industry_strength.csv",
    "changes": OUTDIR / "stock_changes.csv",
    "industry_changes": OUTDIR / "industry_changes.csv",
    "moves": OUTDIR / "stock_price_moves.csv",
    "top_movers": OUTDIR / "top_movers.csv",
    "regime": OUTDIR / "market_regime.csv",
}


def load_named_df(name: str, normalize: bool = True) -> pd.DataFrame:
    path = DATA_FILES.get(name)
    if path is None:
        return pd.DataFrame()
    df = safe_read_csv(path)
    return normalize_df(df) if normalize else df


@st.cache_data(show_spinner=False, ttl=1800, max_entries=4)
def load_fo_symbols_cached(_: int = 0) -> set[str]:
    return load_fo_symbols()


def maybe_filter_fo(df: pd.DataFrame, enabled: bool, fo_symbols: set[str]) -> pd.DataFrame:
    if not enabled or df is None or df.empty:
        return df
    return filter_fo(df, fo_symbols)


# Header controls are shown before loading heavy data.
st.markdown(
    f"<div class='hero-title'>{APP_TITLE}</div>"
    "<div class='muted'>Fast mode: only the selected page's data is loaded.</div>",
    unsafe_allow_html=True,
)

controls = st.columns([1.6, 1.1, 1.1])
with controls[0]:
    page = st.selectbox(
        "Page",
        ["Today", "Explore", "Watchlist", "Charts", "Market", "Structure Changes", "Mobile Feed", "Learn", "Diagnostics"],
        index=0,
        key="page_select",
    )
with controls[1]:
    show_fo_only = st.checkbox("F&O only", value=False, key="show_fo_only_stable")
with controls[2]:
    card_limit = st.slider("Cards", min_value=5, max_value=MAX_CARD_ROWS, value=10, step=5)

# Defaults keep page functions safe even when a dataframe is not needed.
combined = pd.DataFrame()
daily_df = pd.DataFrame()
weekly_df = pd.DataFrame()
industry_df = pd.DataFrame()
changes_df = pd.DataFrame()
industry_changes_df = pd.DataFrame()
moves_df = pd.DataFrame()
top_movers_df = pd.DataFrame()
regime_df = pd.DataFrame()
fo_symbols: set[str] = set()
counts = {s: 0 for s in ["Stage 1", "Stage 2", "Stage 3", "Stage 4"]}

NEEDS_COMBINED = {"Today", "Explore", "Watchlist", "Charts", "Market", "Mobile Feed"}
NEEDS_CHANGES = {"Structure Changes"}
NEEDS_MARKET_EXTRA = {"Market"}

if show_fo_only and page not in {"Learn", "Diagnostics"}:
    # Load universe only when the user actually switches on F&O filter for a data page.
    fo_symbols = load_fo_symbols_cached(0)

if page in NEEDS_COMBINED:
    with st.spinner("Loading core market data..."):
        combined = maybe_filter_fo(load_named_df("combined"), show_fo_only, fo_symbols)

    if combined.empty:
        st.error("No data found. The app is alive, but `outputs/vcp_combined_ranked.csv` is missing, unreadable, or empty after the selected filter.")
        st.markdown("""
        <div class="warning-box">
        Required folder structure:<br>
        <b>streamlit_app.py</b><br>
        <b>outputs/vcp_combined_ranked.csv</b><br>
        <b>outputs/charts/daily/...</b><br>
        <b>outputs/charts/weekly/...</b>
        </div>
        """, unsafe_allow_html=True)
        st.stop()

    counts = stage_counts(combined)

if page in NEEDS_CHANGES:
    with st.spinner("Loading structure changes..."):
        changes_df = maybe_filter_fo(load_named_df("changes"), show_fo_only, fo_symbols)

if page in NEEDS_MARKET_EXTRA:
    with st.spinner("Loading market extras..."):
        industry_df = maybe_filter_fo(load_named_df("industry"), show_fo_only, fo_symbols)
        top_movers_df = maybe_filter_fo(load_named_df("top_movers"), show_fo_only, fo_symbols)
        if top_movers_df.empty:
            top_movers_df = maybe_filter_fo(load_named_df("moves"), show_fo_only, fo_symbols)


def render_today():
    c1, c2, c3, c4 = st.columns(4)
    metrics = [
        ("Total Stocks", len(combined), "Loaded rows"),
        ("Stage 2", counts["Stage 2"], "Advancing"),
        ("Stage 4", counts["Stage 4"], "Declining"),
        ("Industries", combined["Industry"].nunique() if "Industry" in combined.columns else 0, "Available groups"),
    ]
    for col, (title, value, subtitle) in zip([c1, c2, c3, c4], metrics):
        with col:
            st.markdown(f"<div class='hero-card'><div class='kicker'>{title}</div><div class='big-number'>{value}</div><div class='muted'>{subtitle}</div></div>", unsafe_allow_html=True)

    st.markdown("### Top ranked structure")
    top = sort_ranked(combined, n=card_limit)
    for _, row in top.iterrows():
        render_card(row)

    st.markdown("### Latest table")
    st.dataframe(clean_table(sort_ranked(combined)), use_container_width=True, hide_index=True, height=420)


def render_explore():
    st.markdown("### Explore")
    f1, f2, f3 = st.columns(3)
    with f1:
        stage_options = ["All"] + [s for s in ["Stage 1", "Stage 2", "Stage 3", "Stage 4", "Unknown"] if s in set(combined["stage"].astype(str))]
        selected_stage = st.selectbox("Stage", stage_options)
    with f2:
        label_values = sorted(set(combined["label"].dropna().astype(str).tolist())) if "label" in combined.columns else []
        selected_label = st.selectbox("Label", ["All"] + label_values)
    with f3:
        industry_values = sorted(set(combined["Industry"].dropna().astype(str).tolist())) if "Industry" in combined.columns else []
        selected_industry = st.selectbox("Industry", ["All"] + industry_values[:250])

    query = st.text_input("Search company or ticker", "")
    view = combined.copy()
    if selected_stage != "All":
        view = view[view["stage"].astype(str) == selected_stage]
    if selected_label != "All":
        view = view[view["label"].astype(str) == selected_label]
    if selected_industry != "All":
        view = view[view["Industry"].astype(str) == selected_industry]
    if query.strip():
        q = query.strip().lower()
        view = view[view["Company Name"].astype(str).str.lower().str.contains(q, na=False) | view["ticker"].astype(str).str.lower().str.contains(q, na=False)]

    view = sort_ranked(view)
    st.caption(f"Showing {min(len(view), MAX_TABLE_ROWS)} of {len(view)} rows")
    st.dataframe(clean_table(view), use_container_width=True, hide_index=True, height=560)

    st.markdown("### Cards")
    for _, row in view.head(card_limit).iterrows():
        render_card(row)


def render_watchlist():
    st.markdown("### Watchlist")
    st.caption("Enter tickers like RELIANCE, TCS, HDFCBANK. This page renders only selected watchlist rows.")
    raw = st.text_area("Tickers", value=st.session_state.get("watchlist_tickers", ""), height=90, key="watchlist_tickers")
    tokens = [x.strip().upper().replace(".NS", "") for x in re.split(r"[\s,;\n\t]+", raw) if x.strip()]
    tokens = list(dict.fromkeys(tokens))[:60]
    if not tokens:
        st.info("Add tickers to view watchlist.")
        return
    view = combined[combined["ticker"].apply(normalize_symbol).isin(tokens)].copy()
    if view.empty:
        st.warning("No matching tickers found in the current dataset.")
        return
    view = sort_ranked(view)
    st.dataframe(clean_table(view), use_container_width=True, hide_index=True, height=360)

    selected = st.selectbox("Optional chart for one watchlist stock", view["display_name"].tolist())
    row = view[view["display_name"] == selected].iloc[0]
    render_card(row)
    show_charts = st.checkbox("Load charts for selected watchlist stock", value=False)
    if show_charts:
        a, b = st.columns(2)
        with a:
            st.markdown("#### Daily")
            show_image_limited(resolve_chart_path(DAILY_CHART_DIR, row["ticker"], "_daily.png"))
        with b:
            st.markdown("#### Weekly")
            show_image_limited(resolve_chart_path(WEEKLY_CHART_DIR, row["ticker"], "_weekly.png"))


def render_charts():
    st.markdown("### Charts")
    ranked = sort_ranked(combined).drop_duplicates(subset=["ticker"], keep="first")
    if ranked.empty:
        st.info("No chart options available.")
        return
    options = ranked["display_name"].tolist()
    selected = st.selectbox("Select stock", options)
    row = ranked[ranked["display_name"] == selected].iloc[0]
    render_card(row)
    a, b = st.columns(2)
    with a:
        st.markdown("#### Daily")
        show_image_limited(resolve_chart_path(DAILY_CHART_DIR, row["ticker"], "_daily.png"))
    with b:
        st.markdown("#### Weekly")
        show_image_limited(resolve_chart_path(WEEKLY_CHART_DIR, row["ticker"], "_weekly.png"))


def render_market():
    st.markdown("### Market")
    c1, c2, c3, c4 = st.columns(4)
    for col, stage in zip([c1, c2, c3, c4], ["Stage 1", "Stage 2", "Stage 3", "Stage 4"]):
        with col:
            st.markdown(f"<div class='hero-card'><div class='kicker'>{stage}</div><div class='big-number'>{counts[stage]}</div><div class='muted'>stocks</div></div>", unsafe_allow_html=True)

    left, right = st.columns(2)
    with left:
        st.markdown("#### Industry strength")
        if industry_df.empty:
            industry_view = combined.groupby("Industry", dropna=False).size().reset_index(name="Stocks")
        else:
            industry_view = industry_df.copy()
        st.dataframe(clean_table(industry_view), use_container_width=True, hide_index=True, height=500)
    with right:
        st.markdown("#### Top movers")
        st.dataframe(clean_table(sort_ranked(top_movers_df)), use_container_width=True, hide_index=True, height=500)


def render_structure_changes():
    st.markdown("### Structure Changes")
    if changes_df.empty:
        st.info("No stock_changes.csv data available.")
        return
    view = sort_ranked(changes_df)
    st.dataframe(clean_table(view), use_container_width=True, hide_index=True, height=420)
    for _, row in view.head(card_limit).iterrows():
        flags = []
        for col, label in [("entered_stage_2", "Entered Stage 2"), ("new_weekly_breakout", "Weekly breakout"), ("new_daily_breakout", "Daily breakout")]:
            if col in row.index and boolish(row.get(col)):
                flags.append(label)
        rc = pd.to_numeric(row.get("rank_change"), errors="coerce")
        if pd.notna(rc) and rc != 0:
            flags.append(f"Rank {'improved' if rc > 0 else 'declined'} by {abs(int(rc))}")
        render_card(row, extra=" • ".join(flags))


def render_mobile_feed():
    st.markdown("### Mobile Feed")
    st.caption("Low-memory mobile style feed. Charts are intentionally not loaded here.")
    feed = sort_ranked(combined, n=card_limit)
    for i, (_, row) in enumerate(feed.iterrows(), start=1):
        render_card(row, extra=f"#{i}")


def render_learn():
    st.markdown("### Learn")
    st.markdown("""
    <div class="info-card">
      <b>How to read stages</b><br>
      Stage 1 = base / repair. Stage 2 = advancing structure. Stage 3 = transition. Stage 4 = decline.
    </div>
    <div class="info-card">
      <b>How to use this stable version</b><br>
      Start with Today, use Explore for filters, and open Charts only for one selected stock at a time.
      This keeps Streamlit Cloud memory usage low.
    </div>
    <div class="warning-box">
      This tool is informational. It is not investment advice, recommendation, or suitability analysis.
    </div>
    """, unsafe_allow_html=True)


def render_diagnostics():
    st.markdown("### Diagnostics")
    files = [
        OUTDIR / "vcp_combined_ranked.csv",
        OUTDIR / "vcp_daily_ranked.csv",
        OUTDIR / "vcp_weekly_ranked.csv",
        OUTDIR / "industry_strength.csv",
        OUTDIR / "stock_changes.csv",
        OUTDIR / "top_movers.csv",
        OUTDIR / "market_regime.csv",
    ]
    rows = []
    for path in files:
        rows.append({
            "file": str(path),
            "exists": path.exists(),
            "size_mb": round(path.stat().st_size / (1024 * 1024), 2) if path.exists() else None,
        })
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    chart_rows = []
    for name, path in [("daily", DAILY_CHART_DIR), ("weekly", WEEKLY_CHART_DIR)]:
        if path.exists():
            files_list = []
            for idx, p in enumerate(path.glob("*.png")):
                if idx >= 50:
                    break
                files_list.append(p)
            total_mb = sum(p.stat().st_size for p in files_list if p.exists()) / (1024 * 1024)
            chart_rows.append({"chart_dir": name, "exists": True, "sample_files_counted": len(files_list), "sample_total_mb": round(total_mb, 2)})
        else:
            chart_rows.append({"chart_dir": name, "exists": False, "sample_files_counted": 0, "sample_total_mb": 0})
    st.dataframe(pd.DataFrame(chart_rows), use_container_width=True, hide_index=True)

    st.markdown("#### Data shapes")
    if st.checkbox("Load CSV shapes", value=False):
        with st.spinner("Reading CSV headers/shapes..."):
            shape_payload = {}
            for key in ["combined", "daily", "weekly", "industry", "changes", "top_movers"]:
                shape_payload[key] = list(load_named_df(key).shape)
            shape_payload["fo_symbols"] = len(load_fo_symbols_cached(0))
        st.json(shape_payload)
    else:
        st.caption("CSV shapes are not loaded automatically to keep Diagnostics fast.")


PAGES = {
    "Today": render_today,
    "Explore": render_explore,
    "Watchlist": render_watchlist,
    "Charts": render_charts,
    "Market": render_market,
    "Structure Changes": render_structure_changes,
    "Mobile Feed": render_mobile_feed,
    "Learn": render_learn,
    "Diagnostics": render_diagnostics,
}

safe_execute(page, PAGES[page])

st.markdown("""
<div class="warning-box">
<b>Disclaimer:</b> This dashboard is for informational use only. It does not provide investment advice, recommendations, or buy/sell instructions.
</div>
""", unsafe_allow_html=True)
