# FINAL CLEAN DASHBOARD (Requested Changes Applied)

import streamlit as st
import pandas as pd
from pathlib import Path

st.set_page_config(page_title="Market Stage Screener", layout="wide", initial_sidebar_state="collapsed")

# ------------------ STYLE ------------------
st.markdown("""
<style>
.stTabs [data-baseweb="tab"] {
  font-size: 1.15rem;
  font-weight: 700;
}
.stock-card {
  padding: 10px;
  border-radius: 12px;
  margin-bottom: 8px;
  border-left: 6px solid;
}
.stage1 {border-color:#6c5ce7;}
.stage2 {border-color:#00cec9;}
.stage3 {border-color:#fdcb6e;}
.stage4 {border-color:#a29bfe;}
.up {color:#00b894; font-weight:800;}
.down {color:#d63031; font-weight:800;}
</style>
""", unsafe_allow_html=True)

# ------------------ LOAD ------------------
def load(path):
    return pd.read_csv(path) if Path(path).exists() else pd.DataFrame()

combined = load("outputs/vcp_combined_ranked.csv")
industry = load("outputs/industry_strength.csv")
changes = load("outputs/stock_changes.csv")
moves = load("outputs/stock_price_moves.csv")

if combined.empty:
    st.error("No data found in outputs folder")
    st.stop()

# ------------------ LOGIC ------------------
def classify(row):
    score = row.get("final_combined_score", 0)
    if row.get("stage") == "Stage 2" and score >= 60:
        return "Strong"
    elif score >= 45:
        return "Developing"
    else:
        return "Weak"

combined["label"] = combined.apply(classify, axis=1)

def tone():
    strong = (combined["label"]=="Strong").sum()
    if strong > 15: return "Risk On"
    if strong > 5: return "Mixed"
    return "Risk Off"

# ------------------ CARD ------------------
def card(row, pct=None):
    stage = row.get("stage","Stage 1")
    cls = stage.lower().replace(" ","")
    pct_html = ""
    if pct is not None:
        color = "up" if pct > 0 else "down"
        pct_html = f"<div class='{color}'>{pct:.2f}%</div>"
    st.markdown(f"""
    <div class="stock-card {cls}">
    <b>{row['Company Name']} ({row['ticker'].replace('.NS','')})</b><br>
    {row['stage']} * {row['label']} * {row['Industry']}
    {pct_html}
    </div>
    """, unsafe_allow_html=True)

# ------------------ TITLE ------------------
st.title("Market Stage Screener")

# ------------------ TABS ------------------
tabs = st.tabs(["Home","Stocks","Movers","Market","Learn","Portfolio","Advanced","Disclaimer"])

# ------------------ HOME ------------------
with tabs[0]:
    st.subheader("Market Snapshot")
    st.write(f"**Market Tone:** {tone()}")
    st.write("Top Industries:", ", ".join(industry.head(3)["Industry"]) if not industry.empty else "-")

    st.subheader("Top Stocks")
    for _, r in combined.sort_values("final_combined_score", ascending=False).head(5).iterrows():
        card(r)

# ------------------ STOCKS ------------------
with tabs[1]:
    names = combined.sort_values("final_combined_score", ascending=False)["Company Name"].tolist()
    idx = st.session_state.get("idx",0)

    col1,col2,col3 = st.columns([5,1,1])
    sel = col1.selectbox("Select Stock", names, index=idx)

    idx = names.index(sel)
    st.session_state["idx"] = idx

    if col2.button("Prev") and idx>0:
        st.session_state["idx"] = idx-1
        st.experimental_rerun()

    if col3.button("Next") and idx<len(names)-1:
        st.session_state["idx"] = idx+1
        st.experimental_rerun()

    row = combined[combined["Company Name"]==sel].iloc[0]

    st.subheader("Charts")
    st.write("(charts placeholder)")

    st.subheader("Selected Stock")
    card(row)

# ------------------ MOVERS ------------------
with tabs[2]:
    if not moves.empty:
        st.subheader("Up Moves")
        for _, r in moves.sort_values("change_1d_pct", ascending=False).head(5).iterrows():
            card(r, r["change_1d_pct"])

        st.subheader("Down Moves")
        for _, r in moves.sort_values("change_1d_pct").head(5).iterrows():
            card(r, r["change_1d_pct"])

# ------------------ MARKET ------------------
with tabs[3]:
    if not industry.empty:
        industry = industry.sort_values("avg_combined_score", ascending=False).reset_index(drop=True)
        industry["Rank"] = range(1, len(industry)+1)
        stage2 = combined[combined["stage"]=="Stage 2"].groupby("Industry").size()
        industry["Stage2"] = industry["Industry"].map(stage2).fillna(0).astype(int)

        st.dataframe(industry[["Industry","Rank","Stage2"]])

    if not changes.empty:
        st.subheader("Industry Changes")
        st.dataframe(changes[[c for c in ["Industry","current_rank","prev_rank","rank_change"] if c in changes.columns]])

# ------------------ LEARN ------------------
with tabs[4]:
    st.write("Strong = better structure")
    st.write("Developing = mixed")
    st.write("Weak = lower structure")

# ------------------ PORTFOLIO ------------------
with tabs[5]:
    names = combined["Company Name"].tolist()
    selected = st.multiselect("Add Stocks", names)
    for _, r in combined[combined["Company Name"].isin(selected)].iterrows():
        card(r)

# ------------------ ADVANCED ------------------
with tabs[6]:
    st.dataframe(combined[["Company Name","stage","Industry"]])

# ------------------ DISCLAIMER ------------------
def disclaimer():
    st.markdown("---")
    st.caption("This is a data tool. Not investment advice.")

with tabs[7]:
    st.write("This tool is for informational purposes only. No recommendations are made.")

# show disclaimer on all tabs
disclaimer()
