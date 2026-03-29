# Simple Streamlit Dashboard (Clean UX)

import streamlit as st
import pandas as pd
from pathlib import Path

st.set_page_config(layout="wide")

def load_csv(path):
    return pd.read_csv(path) if Path(path).exists() else pd.DataFrame()

def classify(row):
    score = row.get("final_combined_score", 0)
    stage = row.get("stage", "")
    if stage == "Stage 2" and score >= 60:
        return "Strong"
    elif score >= 45:
        return "Developing"
    else:
        return "Weak"

def one_line_reason(row):
    return f"{row.get('stage','')} | {row.get('Industry','')}"

outdir = "outputs"

combined = load_csv(f"{outdir}/vcp_combined_ranked.csv")
industry = load_csv(f"{outdir}/industry_strength.csv")
changes = load_csv(f"{outdir}/stock_changes.csv")

if combined.empty:
    st.warning("No data found. Run engine first.")
    st.stop()

combined["label"] = combined.apply(classify, axis=1)

st.title("Market Dashboard")

top_industries = ", ".join(industry.head(3)["Industry"]) if not industry.empty else "N/A"
strong_count = (combined["label"] == "Strong").sum()

st.markdown(f'''
### Market Snapshot
- Market structure: {'Constructive' if strong_count > 10 else 'Mixed'}
- Strong setups: {strong_count}
- Leading industries: {top_industries}
''')

st.divider()

st.subheader("Top Stocks Today")

top = combined.sort_values("final_combined_score", ascending=False).head(5)

for _, row in top.iterrows():
    st.markdown(f"{row['Company Name']} — {row['label']} — {one_line_reason(row)}")

st.divider()

st.subheader("What Changed")

if not changes.empty:
    st.markdown(f'''
- New Top 10: {(changes.get("new_top_10", False)).sum()}
- New Breakouts: {(changes.get("new_daily_breakout", False)).sum()}
- Stage 2 Entries: {(changes.get("entered_stage_2", False)).sum()}
''')

st.divider()

st.subheader("My Portfolio")

names = combined["Company Name"].dropna().unique().tolist()
selected = st.multiselect("Select stocks", names)

if selected:
    portfolio_df = combined[combined["Company Name"].isin(selected)]
    for _, row in portfolio_df.iterrows():
        st.markdown(f"{row['Company Name']} — {row['label']} — {one_line_reason(row)}")

st.divider()

st.subheader("Stock Detail")

selected_stock = st.selectbox("Select stock", names)

row = combined[combined["Company Name"] == selected_stock].iloc[0]

st.markdown(f'''
### {row['Company Name']}

Classification: {row['label']}
Stage: {row.get('stage')}
Industry: {row.get('Industry')}
Score: {row.get('final_combined_score')}

This is a model-based classification using structure, momentum, and industry context.
''')

st.divider()

st.subheader("Learn")

st.markdown('''
Strong = Better structure  
Developing = Mixed signals  
Weak = Lower alignment  

Stage 1 = Accumulation  
Stage 2 = Uptrend  
Stage 3 = Distribution  
Stage 4 = Downtrend  
''')
