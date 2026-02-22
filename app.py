import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from scipy import stats
import io
from openpyxl.utils import get_column_letter

st.set_page_config(page_title="ניתוח קורלציות מקצועי", layout="wide", page_icon="📊")

# =====================================================
# 🎨 CSS MODERN FINTECH UI
# =====================================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Rubik:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Rubik', sans-serif;
    direction: rtl;
}

.stApp {
    background: linear-gradient(180deg,#f8fafc 0%,#eef2f7 100%);
}

.main-header {
    text-align:center;
    font-size:2.7rem;
    font-weight:700;
    margin-bottom:0.3rem;
    background: linear-gradient(90deg,#2563eb,#1e3a8a);
    -webkit-background-clip:text;
    -webkit-text-fill-color:transparent;
}

.sub-header {
    text-align:center;
    color:#64748b;
    margin-bottom:2rem;
}

.card {
    background:white;
    padding:1.5rem;
    border-radius:16px;
    box-shadow:0 6px 20px rgba(0,0,0,0.06);
    margin-bottom:1.5rem;
}

.result-card {
    background:linear-gradient(135deg,#1e293b,#0f172a);
    color:white;
    padding:1.8rem;
    border-radius:18px;
    box-shadow:0 10px 30px rgba(0,0,0,0.25);
    margin-bottom:2rem;
}

.section-title {
    font-weight:600;
    font-size:1.2rem;
    margin-bottom:1rem;
}

.big-metric {
    font-size:2rem;
    font-weight:700;
}

.stDownloadButton button {
    background: linear-gradient(90deg,#2563eb,#1e40af);
    color:white;
    border-radius:12px;
    height:48px;
    font-weight:600;
}

@media (max-width:768px){
    .main-header{font-size:1.8rem;}
    .big-metric{font-size:1.5rem;}
}
</style>
""", unsafe_allow_html=True)

st.markdown("<h1 class='main-header'>ניתוח קורלציות מקצועי</h1>", unsafe_allow_html=True)

# =====================================================
# ⚙️ INPUT CARD
# =====================================================
st.markdown("<div class='card'>", unsafe_allow_html=True)
st.markdown("<div class='section-title'>⚙️ שלב 1 – הגדר את הניתוח</div>", unsafe_allow_html=True)

DEFAULT_TICKERS = {
    "לאומי": "LUMI.TA",
    "פועלים": "POLI.TA",
    "דיסקונט": "DSCT.TA",
    "מדד ת\"א 35": "TA35.TA",
    "S&P 500": "ES=F",
    "נאסד\"ק 100": "NQ=F",
    "USD/ILS": "ILS=X"
}

col1, col2, col3 = st.columns(3)

with col1:
    asset1_name = st.selectbox("נכס 1", list(DEFAULT_TICKERS.keys()), index=0)
    asset2_name = st.selectbox("נכס 2", list(DEFAULT_TICKERS.keys()), index=1)

with col2:
    return_type = st.radio("סוג תשואה", ["אחוז שינוי רגיל", "תשואה לוגריתמית"])
    use_log = "לוגריתמית" in return_type

with col3:
    days_back = st.number_input("ימים אחורה", min_value=30, max_value=730, value=365)

st.markdown("</div>", unsafe_allow_html=True)

ticker1 = DEFAULT_TICKERS[asset1_name]
ticker2 = DEFAULT_TICKERS[asset2_name]

# =====================================================
# 📥 FETCH DATA
# =====================================================
progress = st.progress(10)

@st.cache_data(ttl=600)
def fetch(sym1, sym2, days):
    df1 = yf.download(sym1, period=f"{days}d")["Close"]
    df2 = yf.download(sym2, period=f"{days}d")["Close"]
    return pd.DataFrame({sym1: df1, sym2: df2}).dropna()

df = fetch(ticker1, ticker2, days_back)
progress.progress(60)

if df.empty:
    st.error("לא נמצאו נתונים.")
    st.stop()

returns = np.log(df / df.shift(1)) if use_log else df.pct_change()
returns = returns.dropna()

col_a, col_b = returns.columns

r, p = stats.pearsonr(returns[col_a], returns[col_b])
r2 = r**2
n = len(returns)

progress.progress(100)

# =====================================================
# 📊 RESULT CARD
# =====================================================
st.markdown("<div class='result-card'>", unsafe_allow_html=True)
st.markdown("### 📊 תוצאת הקורלציה")

c1, c2, c3 = st.columns(3)

c1.markdown(f"<div class='big-metric'>{r:.3f}</div>קורלציה", unsafe_allow_html=True)
c2.markdown(f"<div class='big-metric'>{r2:.2f}</div>R²", unsafe_allow_html=True)
c3.markdown(f"<div class='big-metric'>{n}</div>תצפיות", unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)

# =====================================================
# 📈 TABS FOR GRAPHS
# =====================================================
tab1, tab2 = st.tabs(["📊 פיזור", "📈 Rolling Correlation"])

with tab1:
    fig_scatter = px.scatter(
        returns,
        x=col_a,
        y=col_b,
        trendline="ols",
        template="plotly_white"
    )
    fig_scatter.update_layout(
        height=450,
        font=dict(family="Rubik"),
        margin=dict(l=10,r=10,t=40,b=10)
    )
    st.plotly_chart(fig_scatter, use_container_width=True)

with tab2:
    rolling = returns[col_a].rolling(30).corr(returns[col_b])
    fig_roll = go.Figure()
    fig_roll.add_trace(go.Scatter(
        x=rolling.index,
        y=rolling,
        mode="lines",
        fill="tozeroy"
    ))
    fig_roll.update_layout(
        template="plotly_white",
        height=450,
        yaxis=dict(range=[-1,1]),
        font=dict(family="Rubik")
    )
    st.plotly_chart(fig_roll, use_container_width=True)

# =====================================================
# 📋 DATA + EXPORT
# =====================================================
st.markdown("<div class='card'>", unsafe_allow_html=True)
st.markdown("<div class='section-title'>📋 טבלת נתונים וייצוא</div>", unsafe_allow_html=True)

st.dataframe(returns, use_container_width=True)

buffer = io.BytesIO()
with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
    returns.to_excel(writer)

st.download_button(
    "📥 הורד לאקסל",
    data=buffer,
    file_name="correlation_data.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    use_container_width=True
)

st.markdown("</div>", unsafe_allow_html=True)
