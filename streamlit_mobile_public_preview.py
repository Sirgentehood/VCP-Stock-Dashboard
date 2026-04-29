from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

import streamlit as st

st.set_page_config(
    page_title="Post-Close Market Reset",
    page_icon="📊",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# -----------------------------------------------------------------------------
# Config
# -----------------------------------------------------------------------------
DEFAULT_JSON_PATHS = [
    Path("outputs/public_daily.json"),
    Path("public_daily.json"),
    Path("data/public_daily.json"),
]

# -----------------------------------------------------------------------------
# Styles: mobile-first, fast-scroll, card feed
# -----------------------------------------------------------------------------
st.markdown(
    """
<style>
[data-testid="stSidebar"], [data-testid="collapsedControl"] {display:none;}
.block-container {
    max-width: 520px;
    padding: 0.45rem 0.55rem 1.5rem 0.55rem;
}
#MainMenu, footer, header {visibility: hidden;}
:root {
    --bg-card: rgba(255,255,255,0.055);
    --border: rgba(255,255,255,0.12);
    --muted: rgba(255,255,255,0.66);
    --green: #23d18b;
    --red: #ff5f68;
    --yellow: #f2c14e;
    --blue: #73a7ff;
}
.stApp {background: #050507; color: #ffffff;}
.stButton > button {
    width: 100%;
    border-radius: 999px;
    border: 1px solid var(--border);
    background: rgba(255,255,255,0.07);
    color: #fff;
    font-weight: 800;
}
.hero {
    position: sticky;
    top: 0;
    z-index: 99;
    background: linear-gradient(180deg, #050507 0%, rgba(5,5,7,0.96) 86%, rgba(5,5,7,0) 100%);
    padding: 0.25rem 0 0.75rem 0;
    border-bottom: 1px solid rgba(255,255,255,0.08);
    margin-bottom: 0.65rem;
}
.brand-row {display:flex; align-items:center; justify-content:space-between; gap:0.5rem;}
.brand {font-size: 0.78rem; color: var(--muted); font-weight: 750; letter-spacing:0.04em; text-transform:uppercase;}
.updated {font-size:0.72rem; color: var(--muted); white-space:nowrap;}
.title {font-size:1.72rem; line-height:1.05; font-weight:950; margin:0.24rem 0 0.16rem;}
.subtitle {font-size:0.86rem; line-height:1.25; color:var(--muted); margin-bottom:0.25rem;}
.grid2 {display:grid; grid-template-columns:1fr 1fr; gap:0.55rem; margin:0.55rem 0 0.8rem;}
.metric {
    border:1px solid var(--border);
    background:var(--bg-card);
    border-radius:18px;
    padding:0.7rem 0.75rem;
}
.metric-label {font-size:0.72rem; color:var(--muted); font-weight:700; text-transform:uppercase; letter-spacing:0.03em;}
.metric-value {font-size:1.28rem; font-weight:950; margin-top:0.08rem;}
.section-title {font-size:1.04rem; font-weight:950; margin:1.05rem 0 0.48rem;}
.stock-card {
    border:1px solid var(--border);
    background:var(--bg-card);
    border-radius:22px;
    padding:0.78rem;
    margin-bottom:0.72rem;
    box-shadow: 0 12px 30px rgba(0,0,0,0.22);
}
.card-top {display:flex; justify-content:space-between; gap:0.6rem; align-items:flex-start;}
.company {font-size:1.03rem; font-weight:900; line-height:1.16; margin-bottom:0.15rem;}
.meta {font-size:0.78rem; color:var(--muted); line-height:1.2;}
.rankbox {text-align:right; min-width:54px;}
.rank-label {font-size:0.66rem; color:var(--muted); font-weight:800; text-transform:uppercase;}
.rank-value {font-size:1.34rem; font-weight:950; line-height:1;}
.badges {display:flex; gap:0.32rem; flex-wrap:wrap; margin-top:0.62rem;}
.badge {font-size:0.72rem; font-weight:850; padding:0.22rem 0.48rem; border-radius:999px; border:1px solid rgba(255,255,255,0.14); background:rgba(255,255,255,0.08); color:#f2f6ff;}
.badge-strong {background:rgba(35,209,139,0.13); color:var(--green); border-color:rgba(35,209,139,0.28);}
.badge-transition {background:rgba(242,193,78,0.13); color:var(--yellow); border-color:rgba(242,193,78,0.30);}
.badge-weak {background:rgba(255,95,104,0.13); color:var(--red); border-color:rgba(255,95,104,0.28);}
.reason {font-size:0.86rem; color:rgba(255,255,255,0.82); line-height:1.35; margin-top:0.62rem;}
.chart-wrap {margin-top:0.65rem; border-radius:16px; overflow:hidden; border:1px solid rgba(255,255,255,0.09); background:#111;}
.chart-wrap img {display:block; width:100%;}
.disclaimer {font-size:0.74rem; color:var(--muted); border-left:3px solid rgba(242,193,78,0.6); padding:0.52rem 0.65rem; background:rgba(242,193,78,0.08); border-radius:12px; margin-top:0.75rem;}
.empty {border:1px dashed var(--border); border-radius:18px; padding:1rem; color:var(--muted); font-size:0.9rem;}
.small-link {font-size:0.78rem; color:var(--muted);}
</style>
""",
    unsafe_allow_html=True,
)

# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------
@st.cache_data(show_spinner=False)
def load_json_from_path(path_str: str, mtime_ns: int) -> Dict[str, Any]:
    path = Path(path_str)
    return json.loads(path.read_text(encoding="utf-8"))


def find_default_json() -> Path | None:
    for path in DEFAULT_JSON_PATHS:
        if path.exists():
            return path
    return None


def normalize_items(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    # Supports both naming styles from earlier exporter versions.
    for key in ["top_stocks", "featured", "items", "stocks"]:
        items = payload.get(key)
        if isinstance(items, list):
            return items
    return []


def get_badge_class(text: str) -> str:
    t = str(text or "").lower()
    if "weak" in t or "declin" in t:
        return "badge badge-weak"
    if "transition" in t or "cautious" in t:
        return "badge badge-transition"
    if "strong" in t or "advancing" in t or "stage 2" in t:
        return "badge badge-strong"
    return "badge"


def chart_exists(chart: str) -> bool:
    if not chart:
        return False
    return Path(chart).exists()


def resolve_chart_path(chart: str) -> str | None:
    if not chart:
        return None
    candidates = [Path(chart), Path("outputs") / chart, Path("public") / chart]
    for c in candidates:
        if c.exists():
            return str(c)
    return None


def safe_int(value: Any, default: int = 0) -> int:
    try:
        if value is None or value == "":
            return default
        return int(float(value))
    except Exception:
        return default


# -----------------------------------------------------------------------------
# Data source selector
# -----------------------------------------------------------------------------
def get_payload() -> Dict[str, Any] | None:
    default_path = find_default_json()

    with st.expander("Data source", expanded=default_path is None):
        uploaded = st.file_uploader("Upload public_daily.json", type=["json"])
        manual_path = st.text_input(
            "Or JSON path inside repo/server",
            value=str(default_path) if default_path else "outputs/public_daily.json",
        )

    if uploaded is not None:
        try:
            return json.load(uploaded)
        except Exception as exc:
            st.error(f"Invalid uploaded JSON: {exc}")
            return None

    path = Path(manual_path)
    if not path.exists():
        st.markdown(
            """
<div class="empty">
No JSON found yet. Generate <b>outputs/public_daily.json</b> from your private dashboard, or upload it above.
</div>
""",
            unsafe_allow_html=True,
        )
        return None

    try:
        return load_json_from_path(str(path), path.stat().st_mtime_ns)
    except Exception as exc:
        st.error(f"Could not read JSON: {exc}")
        return None


payload = get_payload()
if not payload:
    st.stop()

items = normalize_items(payload)
summary = payload.get("summary", {}) if isinstance(payload.get("summary"), dict) else {}
disclaimer = payload.get(
    "disclaimer",
    "This is market structure analytics only and not investment advice.",
)

# -----------------------------------------------------------------------------
# Derived summary metrics
# -----------------------------------------------------------------------------
total_charts = len(items)
stage2_count = sum(1 for x in items if str(x.get("stage", "")).lower() == "stage 2")
weak_count = sum(1 for x in items if "weak" in str(x.get("label", x.get("public_label", ""))).lower() or str(x.get("stage", "")).lower() in ["stage 3", "stage 4"])
leader_sector = summary.get("leader_sector") or "—"
updated_text = payload.get("updated_at") or payload.get("updated") or "Post close"

# -----------------------------------------------------------------------------
# Hero
# -----------------------------------------------------------------------------
st.markdown(
    f"""
<div class="hero">
  <div class="brand-row">
    <div class="brand">Post-Close Market Reset</div>
    <div class="updated">{updated_text}</div>
  </div>
  <div class="title">Today in 60 Seconds</div>
  <div class="subtitle">Fast market-structure view for daily review. No buy/sell calls.</div>
</div>
""",
    unsafe_allow_html=True,
)

st.markdown(
    f"""
<div class="grid2">
  <div class="metric"><div class="metric-label">Charts</div><div class="metric-value">{total_charts}</div></div>
  <div class="metric"><div class="metric-label">Stage 2</div><div class="metric-value">{stage2_count}</div></div>
  <div class="metric"><div class="metric-label">Weak / Transition</div><div class="metric-value">{weak_count}</div></div>
  <div class="metric"><div class="metric-label">Leader Sector</div><div class="metric-value">{leader_sector}</div></div>
</div>
""",
    unsafe_allow_html=True,
)

st.markdown(f"<div class='disclaimer'>{disclaimer}</div>", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# Filters
# -----------------------------------------------------------------------------
sectors = sorted({str(x.get("sector") or x.get("industry") or "Unknown") for x in items})
stages = sorted({str(x.get("stage") or "Unknown") for x in items})

f1, f2 = st.columns(2)
with f1:
    selected_sector = st.selectbox("Sector", ["All"] + sectors, index=0)
with f2:
    selected_stage = st.selectbox("Stage", ["All"] + stages, index=0)

filtered = items
if selected_sector != "All":
    filtered = [x for x in filtered if str(x.get("sector") or x.get("industry") or "Unknown") == selected_sector]
if selected_stage != "All":
    filtered = [x for x in filtered if str(x.get("stage") or "Unknown") == selected_stage]

# -----------------------------------------------------------------------------
# Feed
# -----------------------------------------------------------------------------
st.markdown("<div class='section-title'>Today’s Structure Feed</div>", unsafe_allow_html=True)

if not filtered:
    st.markdown("<div class='empty'>No items match this filter.</div>", unsafe_allow_html=True)
    st.stop()

for stock in filtered:
    ticker = str(stock.get("ticker", "")).replace(".NS", "")
    company = stock.get("company") or stock.get("Company Name") or ticker or "Stock"
    sector = stock.get("sector") or stock.get("industry") or "Unknown"
    stage = stock.get("stage") or "Unknown"
    label = stock.get("label") or stock.get("public_label") or "Structure"
    rank = safe_int(stock.get("rank") or stock.get("current_rank"), 0)
    rank_change = safe_int(stock.get("rank_change"), 0)
    reason = stock.get("reason") or stock.get("summary") or "Structure data available."
    chart = stock.get("chart") or stock.get("chart_path") or ""
    chart_path = resolve_chart_path(str(chart))

    rank_change_badge = ""
    if rank_change > 0:
        rank_change_badge = f"<span class='badge badge-strong'>Rank ↑ {rank_change}</span>"
    elif rank_change < 0:
        rank_change_badge = f"<span class='badge badge-transition'>Rank ↓ {abs(rank_change)}</span>"

    st.markdown(
        f"""
<div class="stock-card">
  <div class="card-top">
    <div>
      <div class="company">{company}</div>
      <div class="meta">{ticker} • {sector}</div>
    </div>
    <div class="rankbox">
      <div class="rank-label">Rank</div>
      <div class="rank-value">#{rank if rank else '—'}</div>
    </div>
  </div>
  <div class="badges">
    <span class="{get_badge_class(str(stage))}">{stage}</span>
    <span class="{get_badge_class(str(label))}">{label}</span>
    {rank_change_badge}
  </div>
  <div class="reason">{reason}</div>
</div>
""",
        unsafe_allow_html=True,
    )

    if chart_path:
        st.image(chart_path, use_container_width=True)
    elif chart:
        st.caption(f"Chart not found locally: {chart}")

st.markdown("<div class='small-link'>End of daily structure feed.</div>", unsafe_allow_html=True)
