import streamlit as st
import requests

st.title("Mobile Preview")

# 👇 Replace YOUR username + repo
JSON_URL = "https://raw.githubusercontent.com/Sirgentehood/VCP-Stock-Dashboard/main/outputs/public_daily.json"
# https://github.com/Sirgentehood/VCP-Stock-Dashboard/blob/main/outputs/public_daily.json

try:
    res = requests.get(JSON_URL)
    data = res.json()
except:
    st.error("Unable to load data")
    st.stop()

stocks = data.get("top_stocks", [])

st.write(f"Loaded {len(stocks)} stocks")

for s in stocks:
    st.write(s["company"], "-", s["label"])

st.markdown("### ⚡ Today in 10 Seconds")

col1, col2 = st.columns(2)
col1.metric("Stocks", len(stocks))
col2.metric("Type", "Post Close")

st.divider()

st.markdown("### 📈 Structure Feed")

if not stocks:
    st.warning("No data available")
    st.stop()

for s in stocks:
    with st.container():
        st.markdown(f"### {s['company']} ({s['ticker']})")

        col1, col2 = st.columns([3,1])

        with col1:
            st.write(f"Sector: {s.get('sector','-')}")
            st.write(f"Stage: {s.get('stage','-')}")
            st.write(f"Structure: {s.get('label','-')}")

        with col2:
            st.metric("Rank", f"#{s.get('rank','-')}")
            if s.get("rank_change", 0) > 0:
                st.success(f"↑ {s.get('rank_change')}")

        st.write(s.get("reason",""))

        if s.get("chart"):
            st.image(s["chart"], use_container_width=True)

        st.divider()

st.caption("Market structure view only. Not investment advice.")
