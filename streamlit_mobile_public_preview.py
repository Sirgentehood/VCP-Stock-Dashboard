import streamlit as st
import json

st.set_page_config(page_title="Mobile Market Preview", layout="wide")

# ----------------------------
# Header
# ----------------------------
st.markdown("""
<h2 style='margin-bottom:5px;'>📊 Post-Close Market Reset</h2>
<p style='color:gray; margin-top:0;'>Fast mobile-style preview (not investment advice)</p>
""", unsafe_allow_html=True)

# ----------------------------
# Upload JSON
# ----------------------------
uploaded_file = st.file_uploader("Upload public_daily.json", type="json")

if uploaded_file is None:
    st.warning("⬆️ Upload your JSON file from dashboard export to preview")
    st.stop()

data = json.load(uploaded_file)

stocks = data.get("top_stocks", [])

# ----------------------------
# Summary
# ----------------------------
st.markdown("### ⚡ Today in 10 Seconds")

col1, col2 = st.columns(2)
col1.metric("Total Stocks", len(stocks))
col2.metric("Update Type", "Post Close")

st.divider()

# ----------------------------
# Feed
# ----------------------------
st.markdown("### 📈 Structure Feed")

if not stocks:
    st.warning("No stocks found in JSON")
    st.stop()

for s in stocks:
    with st.container():
        st.markdown(f"### {s.get('company','')} ({s.get('ticker','')})")

        col1, col2 = st.columns([3,1])

        with col1:
            st.markdown(f"**Sector:** {s.get('sector','-')}")
            st.markdown(f"**Stage:** {s.get('stage','-')}")
            st.markdown(f"**Structure:** {s.get('label','-')}")

        with col2:
            st.metric("Rank", f"#{s.get('rank','-')}")
            if s.get("rank_change", 0) > 0:
                st.success(f"↑ {s.get('rank_change')}")

        st.markdown(f"🧠 {s.get('reason','')}")

        # Chart
        chart_path = s.get("chart")
        if chart_path:
            try:
                st.image(chart_path, use_container_width=True)
            except:
                st.info("Chart not found (optional)")

        st.divider()

# ----------------------------
# Footer
# ----------------------------
st.caption("This is a data-driven market structure view. Not investment advice.")
