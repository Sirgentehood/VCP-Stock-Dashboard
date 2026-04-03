import streamlit as st
import pandas as pd
from pathlib import Path
import math

st.set_page_config(page_title="Market Structure Radar", layout="wide")

# =========================
# SESSION STATE
# =========================
if "watchlist" not in st.session_state:
    st.session_state["watchlist"] = []

if "alerts" not in st.session_state:
    st.session_state["alerts"] = []

if "active_tab" not in st.session_state:
    st.session_state["active_tab"] = "Home"

if "selected_stock_index" not in st.session_state:
    st.session_state["selected_stock_index"] = 0

if "portfolio_chart_index" not in st.session_state:
    st.session_state["portfolio_chart_index"] = 0


# =========================
# LOAD DATA
# =========================
@st.cache_data
def load_csv(path):
    if Path(path).exists():
        return pd.read_csv(path)
    return pd.DataFrame()

combined = load_csv("outputs/vcp_combined_ranked.csv")

if combined.empty:
    st.error("Missing data")
    st.stop()


# =========================
# DECISION ENGINE
# =========================
def decision_label(row):
    stage = str(row.get("stage", ""))
    label = str(row.get("label", "Developing"))
    rank = pd.to_numeric(row.get("current_rank"), errors="coerce")

    if stage == "Stage 2" and label == "Strong":
        if pd.notna(rank) and rank <= 10:
            return ("High Conviction", "green")
        return ("Opportunity", "green")

    if stage == "Stage 2":
        return ("Watch Closely", "blue")

    if stage == "Stage 1":
        return ("Watchlist", "blue")

    if stage == "Stage 3":
        return ("Caution", "orange")

    if stage == "Stage 4":
        return ("Avoid", "red")

    return ("Neutral", "gray")


# =========================
# CARD COMPONENT
# =========================
def card(row, idx, context="general"):
    company = row["Company Name"]
    ticker = str(row["ticker"]).replace(".NS", "")
    stage = row.get("stage", "")
    rank = row.get("current_rank", "n/a")

    decision_text, color = decision_label(row)

    st.markdown(f"""
    <div style="
        border:1px solid #333;
        border-radius:12px;
        padding:10px;
        margin-bottom:8px;
    ">
        <b>{company} ({ticker})</b><br>
        {stage}<br>
        <b style="color:{color}">{decision_text}</b><br>
        Rank: {rank}
    </div>
    """, unsafe_allow_html=True)

    # ACTION ROW
    c1, c2, c3 = st.columns(3)

    # 👉 OPEN
    with c1:
        if st.button("Open", key=f"open_{ticker}_{idx}"):
            names = combined["Company Name"].tolist()
            st.session_state["selected_stock_index"] = names.index(company)

            if context == "portfolio":
                st.session_state["active_tab"] = "Portfolio"
            else:
                st.session_state["active_tab"] = "Stocks"

            st.rerun()

    # 👉 WATCHLIST
    with c2:
        if st.button("Watchlist", key=f"watch_{ticker}_{idx}"):
            st.session_state["watchlist"] = list(set(st.session_state["watchlist"] + [ticker]))
            st.toast(f"{ticker} added")

    # 👉 ALERT
    with c3:
        if st.button("Alert", key=f"alert_{ticker}_{idx}"):
            st.session_state["alerts"] = list(set(st.session_state["alerts"] + [ticker]))
            st.toast(f"Alert added")


# =========================
# TABS
# =========================
tab_names = ["Home", "Stocks", "Portfolio", "Alerts"]
tabs = st.tabs(tab_names)

active = st.session_state["active_tab"]

# =========================
# HOME
# =========================
with tabs[0]:
    if active != "Home":
        st.stop()

    st.title("Market Radar")

    top = combined.sort_values("final_combined_score", ascending=False).head(10)

    for i, r in top.iterrows():
        card(r, i)


# =========================
# STOCKS TAB
# =========================
with tabs[1]:
    if active != "Stocks":
        st.stop()

    st.title("Stock Detail")

    idx = st.session_state["selected_stock_index"]
    row = combined.iloc[idx]

    card(row, idx)

    st.markdown("### Chart Placeholder")
    st.info("Add your charts here")


# =========================
# PORTFOLIO
# =========================
with tabs[2]:
    if active != "Portfolio":
        st.stop()

    st.title("Portfolio")

    names = combined["Company Name"].head(10)

    current = combined[combined["Company Name"].isin(names)]

    for i, r in current.iterrows():
        card(r, i, context="portfolio")

    st.markdown("### Portfolio Charts")

    idx = st.session_state["portfolio_chart_index"]
    row = current.iloc[idx]

    st.write(f"Showing chart for {row['Company Name']}")


# =========================
# ALERTS
# =========================
with tabs[3]:
    if active != "Alerts":
        st.stop()

    st.title("Alerts")

    if st.session_state["alerts"]:
        st.write("Alerts:", ", ".join(st.session_state["alerts"]))
    else:
        st.info("No alerts")

    st.markdown("### Watchlist")

    if st.session_state["watchlist"]:
        st.write(", ".join(st.session_state["watchlist"]))
    else:
        st.info("No watchlist items")
