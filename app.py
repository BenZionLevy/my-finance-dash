import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from scipy import stats
import io
from openpyxl.utils import get_column_letter

st.set_page_config(page_title="מנתח קורלציות", layout="wide", page_icon="📊")

# ==========================================
# עיצוב CSS מרהיב
# ==========================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Heebo:wght@300;400;500;600;700;800;900&family=JetBrains+Mono:wght@400;700&display=swap');

    /* === GLOBAL RESET === */
    html, body, [class*="css"] {
        font-family: 'Heebo', sans-serif;
        direction: rtl;
    }
    
    /* === BACKGROUND === */
    .stApp {
        background: #0a0f1e;
        background-image: 
            radial-gradient(ellipse at 20% 10%, rgba(59, 130, 246, 0.12) 0%, transparent 50%),
            radial-gradient(ellipse at 80% 80%, rgba(16, 185, 129, 0.08) 0%, transparent 50%),
            radial-gradient(ellipse at 50% 50%, rgba(99, 102, 241, 0.05) 0%, transparent 70%);
        min-height: 100vh;
    }

    /* === HIDE STREAMLIT CHROME === */
    #MainMenu, footer, header { visibility: hidden; }
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 2rem !important;
        max-width: 1400px;
    }

    /* === HERO HEADER === */
    .hero-wrap {
        text-align: center;
        padding: 2.5rem 1rem 1rem;
        position: relative;
    }
    .hero-eyebrow {
        display: inline-block;
        background: linear-gradient(90deg, rgba(59,130,246,0.2), rgba(16,185,129,0.2));
        border: 1px solid rgba(59,130,246,0.3);
        border-radius: 100px;
        color: #60a5fa;
        font-size: 0.78rem;
        font-weight: 600;
        letter-spacing: 0.15em;
        padding: 0.3rem 1rem;
        margin-bottom: 1rem;
        text-transform: uppercase;
    }
    .hero-title {
        font-size: clamp(2rem, 5vw, 3.5rem);
        font-weight: 900;
        color: #ffffff;
        line-height: 1.1;
        margin-bottom: 0.5rem;
        letter-spacing: -0.02em;
    }
    .hero-title .accent {
        background: linear-gradient(135deg, #3b82f6 0%, #10b981 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    .hero-sub {
        color: #94a3b8;
        font-size: 1rem;
        font-weight: 400;
        margin-bottom: 0;
    }

    /* === STEP CARDS === */
    .step-label {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        margin-bottom: 0.75rem;
        direction: rtl;
    }
    .step-number {
        width: 28px;
        height: 28px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 0.75rem;
        font-weight: 800;
        flex-shrink: 0;
    }
    .step-1 .step-number { background: rgba(59,130,246,0.2); color: #60a5fa; border: 1px solid rgba(59,130,246,0.4); }
    .step-2 .step-number { background: rgba(99,102,241,0.2); color: #a5b4fc; border: 1px solid rgba(99,102,241,0.4); }
    .step-3 .step-number { background: rgba(16,185,129,0.2); color: #34d399; border: 1px solid rgba(16,185,129,0.4); }
    .step-title {
        font-size: 0.9rem;
        font-weight: 700;
        color: #e2e8f0;
        letter-spacing: 0.02em;
    }

    /* === GLASS PANELS === */
    .glass-panel {
        background: rgba(255,255,255,0.04);
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 16px;
        padding: 1.5rem;
        backdrop-filter: blur(12px);
        margin-bottom: 1rem;
        transition: border-color 0.2s;
    }
    .glass-panel:hover {
        border-color: rgba(59,130,246,0.3);
    }

    /* === DIVIDER === */
    hr { border-color: rgba(255,255,255,0.08) !important; margin: 1.5rem 0 !important; }

    /* === METRICS ROW === */
    .metrics-grid {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 1rem;
        margin-bottom: 1.5rem;
    }
    @media (max-width: 768px) {
        .metrics-grid { grid-template-columns: repeat(2, 1fr); }
    }
    .metric-card {
        background: rgba(255,255,255,0.04);
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 14px;
        padding: 1.2rem;
        text-align: center;
        position: relative;
        overflow: hidden;
    }
    .metric-card::before {
        content: '';
        position: absolute;
        top: 0; left: 0; right: 0;
        height: 3px;
        border-radius: 14px 14px 0 0;
    }
    .metric-card.blue::before  { background: linear-gradient(90deg, #3b82f6, #60a5fa); }
    .metric-card.green::before { background: linear-gradient(90deg, #10b981, #34d399); }
    .metric-card.amber::before { background: linear-gradient(90deg, #f59e0b, #fbbf24); }
    .metric-card.purple::before{ background: linear-gradient(90deg, #8b5cf6, #a78bfa); }
    .metric-icon { font-size: 1.3rem; margin-bottom: 0.4rem; }
    .metric-value {
        font-family: 'JetBrains Mono', monospace;
        font-size: 1.6rem;
        font-weight: 700;
        color: #f8fafc;
        line-height: 1;
        margin-bottom: 0.3rem;
    }
    .metric-label { font-size: 0.72rem; color: #64748b; font-weight: 600; text-transform: uppercase; letter-spacing: 0.08em; }

    /* === RESULT INSIGHT BOX === */
    .insight-box {
        background: linear-gradient(135deg, rgba(59,130,246,0.08) 0%, rgba(16,185,129,0.06) 100%);
        border: 1px solid rgba(59,130,246,0.2);
        border-radius: 14px;
        padding: 1.25rem 1.5rem;
        color: #cbd5e1;
        direction: rtl;
        text-align: right;
        font-size: 0.97rem;
        line-height: 1.7;
        margin-bottom: 1.5rem;
        position: relative;
    }
    .insight-box::before {
        content: '🧠';
        position: absolute;
        top: 1.1rem;
        left: 1.2rem;
        font-size: 1.2rem;
    }
    .insight-box b { color: #e2e8f0; }

    /* === BADGES === */
    .badge {
        display: inline-block;
        padding: 0.2rem 0.7rem;
        border-radius: 100px;
        font-size: 0.82rem;
        font-weight: 700;
        margin: 0 0.15rem;
        vertical-align: middle;
    }
    .badge-pos  { background: rgba(16,185,129,0.15); color: #34d399; border: 1px solid rgba(16,185,129,0.3); }
    .badge-neg  { background: rgba(239,68,68,0.15);  color: #f87171; border: 1px solid rgba(239,68,68,0.3); }
    .badge-neut { background: rgba(100,116,139,0.15);color: #94a3b8; border: 1px solid rgba(100,116,139,0.3); }
    .badge-sig  { background: rgba(59,130,246,0.12); color: #60a5fa; border: 1px solid rgba(59,130,246,0.3); }

    /* === SECTION TITLES === */
    .sec-title {
        font-size: 0.8rem;
        font-weight: 700;
        color: #64748b;
        text-transform: uppercase;
        letter-spacing: 0.12em;
        margin-bottom: 0.75rem;
        direction: rtl;
        text-align: right;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    .sec-title::after {
        content: '';
        flex: 1;
        height: 1px;
        background: rgba(255,255,255,0.07);
    }

    /* === STREAMLIT WIDGET OVERRIDES === */
    .stSelectbox > div > div,
    .stTextInput > div > div > input,
    .stNumberInput > div > div > input {
        background: rgba(255,255,255,0.06) !important;
        border: 1px solid rgba(255,255,255,0.12) !important;
        border-radius: 10px !important;
        color: #e2e8f0 !important;
        direction: rtl !important;
        text-align: right !important;
    }
    .stSelectbox > div > div:focus-within,
    .stTextInput > div > div > input:focus,
    .stNumberInput > div > div > input:focus {
        border-color: rgba(59,130,246,0.5) !important;
        box-shadow: 0 0 0 3px rgba(59,130,246,0.1) !important;
    }
    .stRadio > div {
        direction: rtl !important;
        gap: 0.4rem !important;
    }
    .stRadio label {
        background: rgba(255,255,255,0.04) !important;
        border: 1px solid rgba(255,255,255,0.08) !important;
        border-radius: 8px !important;
        padding: 0.4rem 0.8rem !important;
        cursor: pointer !important;
        transition: all 0.15s !important;
        color: #94a3b8 !important;
        font-size: 0.88rem !important;
    }
    .stRadio label:hover {
        border-color: rgba(59,130,246,0.4) !important;
        color: #e2e8f0 !important;
    }
    div[data-baseweb="radio"] > label[data-checked="true"] {
        background: rgba(59,130,246,0.12) !important;
        border-color: rgba(59,130,246,0.5) !important;
        color: #60a5fa !important;
    }
    .stCheckbox label { color: #94a3b8 !important; font-size: 0.9rem !important; }
    .stSlider > div > div > div > div { background: #3b82f6 !important; }
    label[data-testid="stWidgetLabel"] { color: #94a3b8 !important; font-size: 0.82rem !important; font-weight: 600 !important; text-transform: uppercase !important; letter-spacing: 0.08em !important; }
    .stMetric { background: transparent !important; }
    .stMetric label { color: #64748b !important; }
    .stMetric [data-testid="metric-value"] { color: #f1f5f9 !important; font-family: 'JetBrains Mono', monospace !important; }
    
    /* Expander styling */
    .streamlit-expanderHeader {
        background: rgba(255,255,255,0.04) !important;
        border: 1px solid rgba(255,255,255,0.1) !important;
        border-radius: 12px !important;
        color: #e2e8f0 !important;
        font-weight: 600 !important;
        font-size: 1rem !important;
    }
    .streamlit-expanderContent {
        background: rgba(255,255,255,0.02) !important;
        border: 1px solid rgba(255,255,255,0.07) !important;
        border-top: none !important;
        border-radius: 0 0 12px 12px !important;
    }
    
    /* Download button */
    .stDownloadButton > button {
        background: linear-gradient(135deg, #3b82f6, #1d4ed8) !important;
        color: white !important;
        border: none !important;
        border-radius: 10px !important;
        font-weight: 700 !important;
        padding: 0.65rem 1.5rem !important;
        width: 100% !important;
        transition: opacity 0.2s !important;
        font-size: 0.9rem !important;
    }
    .stDownloadButton > button:hover { opacity: 0.85 !important; }
    
    /* Dataframe */
    .stDataFrame { border-radius: 12px !important; overflow: hidden !important; }
    
    /* Columns gap */
    [data-testid="column"] { padding: 0 0.4rem !important; }

    /* Warning / error / info */
    .stAlert { border-radius: 12px !important; }

    /* Spinner */
    .stSpinner > div { border-top-color: #3b82f6 !important; }

    /* Run button look */
    .stButton > button {
        background: linear-gradient(135deg, #10b981, #059669) !important;
        color: white !important;
        border: none !important;
        border-radius: 10px !important;
        font-weight: 700 !important;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# פונקציות עזר
# ==========================================
def safe_round(val, mult=1.0):
    if pd.isna(val): return None
    return round(float(val) * mult, 2)

# ==========================================
# HERO HEADER
# ==========================================
st.markdown("""
<div class='hero-wrap'>
    <div class='hero-eyebrow'>🔬 כלי ניתוח מקצועי · שוק ההון</div>
    <h1 class='hero-title'>מנתח <span class='accent'>קורלציות</span></h1>
    <p class='hero-sub'>גלה את הקשר הסטטיסטי בין נכסים פיננסיים — בזמן אמת</p>
</div>
""", unsafe_allow_html=True)

# ==========================================
# הגדרות
# ==========================================
DEFAULT_TICKERS = {
    "לאומי 🏦": "LUMI.TA",
    "פועלים 🏦": "POLI.TA",
    "דיסקונט 🏦": "DSCT.TA",
    "ת\"א 35 📈": "TA35.TA",
    "ת\"א 125 📈": "TA125.TA",
    "בנקים 5 📊": "TA-BANKS.TA",
    "S&P 500 🇺🇸": "ES=F",
    'נאסד"ק 100 💻': "NQ=F",
    "דולר/שקל 💱": "ILS=X",
    "XLF פיננסים 🏛️": "XLF"
}

with st.expander("⚙️  הגדרת הניתוח — לחץ להרחבה", expanded=True):
    st.markdown("""
    <div style='padding: 0.5rem 0 1rem; color: #64748b; font-size: 0.88rem; direction: rtl; text-align: right;'>
        מלא את שלושת השלבים הבאים, ולחץ על "הרץ ניתוח" לקבלת התוצאות
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3, gap="medium")

    # ---- שלב 1 ----
    with col1:
        st.markdown("""
        <div class='step-label step-1'>
            <div class='step-number'>1</div>
            <span class='step-title'>בחר את הנכסים</span>
        </div>
        """, unsafe_allow_html=True)

        use_custom = st.checkbox("טיקר חופשי (מתקדם)", value=False)
        if use_custom:
            custom1 = st.text_input("טיקר 1", value="AAPL", placeholder="לדוגמה: AAPL").upper().strip()
            custom2 = st.text_input("טיקר 2", value="MSFT", placeholder="לדוגמה: MSFT").upper().strip()
            asset1_name, asset2_name = custom1, custom2
            ticker1_sym, ticker2_sym = custom1, custom2
        else:
            ticker_names = list(DEFAULT_TICKERS.keys())
            asset1_name = st.selectbox("נכס ראשון", ticker_names, index=0)
            asset2_name = st.selectbox("נכס שני", ticker_names, index=8)
            ticker1_sym = DEFAULT_TICKERS[asset1_name]
            ticker2_sym = DEFAULT_TICKERS[asset2_name]

        if ticker1_sym == ticker2_sym:
            st.error("⚠️ בחרת את אותו נכס פעמיים!")
            st.stop()

    # ---- שלב 2 ----
    with col2:
        st.markdown("""
        <div class='step-label step-2'>
            <div class='step-number'>2</div>
            <span class='step-title'>מבנה הזמן</span>
        </div>
        """, unsafe_allow_html=True)

        mode = st.radio("מצב ניתוח:", [
            "📅 יומי: סגירה רשמית",
            "🕐 יומי: שעה קבועה",
            "⏱️ חלון שעות מסחר",
            "⚡ תוך-יומי מפורט"
        ])
        return_type = st.radio("סוג תשואה:", ["📊 פשוטה (Simple)", "📉 לוגריתמית (Log)"])
        use_log_returns = "לוגריתמית" in return_type

    # ---- שלב 3 ----
    with col3:
        st.markdown("""
        <div class='step-label step-3'>
            <div class='step-number'>3</div>
            <span class='step-title'>הגדרות זמן</span>
        </div>
        """, unsafe_allow_html=True)

        start_hour, end_hour, target_hour = None, None, None
        interval_choice, lag_minutes = "1d", 0

        is_daily_mode = mode == "📅 יומי: סגירה רשמית"
        max_days = 730 if is_daily_mode else 60
        default_days = 365 if is_daily_mode else 60

        if mode == "🕐 יומי: שעה קבועה":
            target_hour = st.selectbox("שעה קבועה:", [f"{h:02d}:00" for h in range(8, 23)], index=2)
            interval_choice = "5m"
        elif mode in ["⏱️ חלון שעות מסחר", "⚡ תוך-יומי מפורט"]:
            start_hour = st.selectbox("שעת התחלה:", [f"{h:02d}:00" for h in range(8, 23)], index=2)
            end_hour   = st.selectbox("שעת סיום:", [f"{h:02d}:00" for h in range(8, 23)], index=8)
            if mode == "⚡ תוך-יומי מפורט":
                int_map = {"5 דקות": "5m", "15 דקות": "15m", "30 דקות": "30m", "שעה": "60m"}
                interval_choice = int_map[st.selectbox("קפיצת זמן:", list(int_map.keys()))]
                lag_minutes = st.number_input("השהיה לנכס 2 (דקות):", min_value=0, max_value=600, value=0, step=5)
            else:
                interval_choice = "5m"

        days_back = st.number_input("ימים אחורה:", min_value=1, max_value=max_days, value=default_days)

    st.divider()

    adv1, adv2 = st.columns(2, gap="medium")
    with adv1:
        show_rolling = st.checkbox("📈 Rolling Correlation", value=True)
        if show_rolling:
            rolling_window = st.slider("גודל חלון:", min_value=5, max_value=100, value=20, format="%d תצפיות")
    with adv2:
        show_ccf = st.checkbox("🔍 מפת הובלה (Cross-Correlation)", value=False)
        if show_ccf:
            ccf_max_lag = st.slider("מספר השהיות:", min_value=1, max_value=20, value=10)

# ==========================================
# פונקציות
# ==========================================
@st.cache_data(ttl=600, show_spinner=False)
def fetch_data(sym1, sym2, days, yf_interval):
    try:
        df1 = yf.download(sym1, period=f"{days}d", interval=yf_interval, auto_adjust=True)["Close"]
        df2 = yf.download(sym2, period=f"{days}d", interval=yf_interval, auto_adjust=True)["Close"]
        if isinstance(df1, pd.DataFrame): df1 = df1.iloc[:, 0]
        if isinstance(df2, pd.DataFrame): df2 = df2.iloc[:, 0]
        combined = pd.DataFrame({sym1: df1, sym2: df2}).dropna(how="all")
        if combined.index.tz is None:
            combined.index = combined.index.tz_localize("UTC").tz_convert("Asia/Jerusalem")
        else:
            combined.index = combined.index.tz_convert("Asia/Jerusalem")
        return combined
    except Exception:
        return pd.DataFrame()

def compute_stats(s1, s2):
    clean = pd.DataFrame({"a": s1, "b": s2}).dropna()
    if len(clean) < 3: return {"corr": np.nan, "r2": np.nan, "pvalue": np.nan, "n": len(clean)}
    r, p = stats.pearsonr(clean["a"], clean["b"])
    return {"corr": r, "r2": r ** 2, "pvalue": p, "n": len(clean)}

def pvalue_label(p):
    if np.isnan(p): return "—"
    if p < 0.001: return "p < 0.001 ✅"
    if p < 0.01:  return f"p = {p:.3f} ✅"
    if p < 0.05:  return f"p = {p:.3f} ⚠️"
    return f"p = {p:.3f} ❌"

def calculate_returns(df, is_log):
    if is_log: return np.log(df / df.shift(1))
    return df.pct_change()

# ==========================================
# עיבוד נתונים
# ==========================================
with st.spinner("🔄  שולף נתונים מהשוק..."):
    raw_df = fetch_data(ticker1_sym, ticker2_sym, days_back, interval_choice)

if raw_df.empty:
    st.error("❌ לא ניתן למשוך נתונים. בדוק שהטיקרים נכונים ויש חיבור לאינטרנט.")
    st.stop()

scatter_df = pd.DataFrame()
records = []

if mode == "📅 יומי: סגירה רשמית":
    returns_df_full = calculate_returns(raw_df, use_log_returns)
    scatter_df = returns_df_full.dropna().rename(columns={ticker1_sym: asset1_name, ticker2_sym: asset2_name})
    for d, row in raw_df.iterrows():
        r1 = returns_df_full.loc[d, ticker1_sym]
        r2 = returns_df_full.loc[d, ticker2_sym]
        records.append({
            "תאריך": d.strftime("%d/%m/%Y"),
            f"שער {asset1_name}": safe_round(row[ticker1_sym]),
            f"תשואה {asset1_name} (%)": safe_round(r1, 100),
            f"שער {asset2_name}": safe_round(row[ticker2_sym]),
            f"תשואה {asset2_name} (%)": safe_round(r2, 100),
            "הפרש (%)": safe_round(r1 - r2, 100) if pd.notna(r1) and pd.notna(r2) else None,
        })

elif mode == "🕐 יומי: שעה קבועה":
    target_end = f"{int(target_hour[:2]):02d}:59"
    hour_df = raw_df.between_time(target_hour, target_end).dropna(how="all")
    if not hour_df.empty:
        hour_df['date_str'] = hour_df.index.date.astype(str)
        daily = hour_df.groupby('date_str').first()
        returns_df_full = calculate_returns(daily, use_log_returns)
        scatter_df = returns_df_full.dropna().rename(columns={ticker1_sym: asset1_name, ticker2_sym: asset2_name})
        scatter_df.index = pd.to_datetime(scatter_df.index)
        for d_str in daily.index:
            d_obj = pd.to_datetime(d_str)
            r1 = returns_df_full.loc[d_str, ticker1_sym]
            r2 = returns_df_full.loc[d_str, ticker2_sym]
            records.append({
                "תאריך": d_obj.strftime("%d/%m/%Y"),
                f"שער {asset1_name}": safe_round(daily.loc[d_str, ticker1_sym]),
                f"תשואה {asset1_name} (%)": safe_round(r1, 100),
                f"שער {asset2_name}": safe_round(daily.loc[d_str, ticker2_sym]),
                f"תשואה {asset2_name} (%)": safe_round(r2, 100),
                "הפרש (%)": safe_round(r1 - r2, 100) if pd.notna(r1) and pd.notna(r2) else None,
            })

elif mode == "⏱️ חלון שעות מסחר":
    filtered = raw_df.between_time(start_hour, end_hour)
    dates = np.unique(filtered.index.date)
    calc, calc_dates = [], []
    for d in dates:
        try: day = filtered.loc[str(d)]
        except KeyError: continue
        v1, v2 = day[ticker1_sym].dropna(), day[ticker2_sym].dropna()
        if len(v1) >= 2 and len(v2) >= 2:
            if use_log_returns:
                ret1 = np.log(v1.iloc[-1] / v1.iloc[0]) if v1.iloc[0] > 0 else np.nan
                ret2 = np.log(v2.iloc[-1] / v2.iloc[0]) if v2.iloc[0] > 0 else np.nan
            else:
                ret1 = (v1.iloc[-1] - v1.iloc[0]) / v1.iloc[0]
                ret2 = (v2.iloc[-1] - v2.iloc[0]) / v2.iloc[0]
        else:
            ret1, ret2 = np.nan, np.nan
        if pd.notna(ret1) and pd.notna(ret2):
            calc.append({asset1_name: ret1, asset2_name: ret2})
            calc_dates.append(pd.to_datetime(d))
        records.append({
            "תאריך": d.strftime("%d/%m/%Y"),
            f"פתיחה {asset1_name}": safe_round(v1.iloc[0]) if len(v1)>0 else None,
            f"סגירה {asset1_name}": safe_round(v1.iloc[-1]) if len(v1)>0 else None,
            f"תשואה {asset1_name} (%)": safe_round(ret1, 100),
            f"פתיחה {asset2_name}": safe_round(v2.iloc[0]) if len(v2)>0 else None,
            f"סגירה {asset2_name}": safe_round(v2.iloc[-1]) if len(v2)>0 else None,
            f"תשואה {asset2_name} (%)": safe_round(ret2, 100),
            "הפרש (%)": safe_round(ret1 - ret2, 100) if pd.notna(ret1) and pd.notna(ret2) else None,
        })
    scatter_df = pd.DataFrame(calc)
    if not scatter_df.empty: scatter_df.index = calc_dates

elif mode == "⚡ תוך-יומי מפורט":
    filtered = raw_df.between_time(start_hour, end_hour).copy()
    if lag_minutes > 0:
        mins_map = {"5m": 5, "15m": 15, "30m": 30, "60m": 60}
        shift_periods = int(round(lag_minutes / mins_map[interval_choice]))
        if shift_periods > 0: filtered[ticker2_sym] = filtered[ticker2_sym].shift(shift_periods)
    returns_df_full = calculate_returns(filtered, use_log_returns)
    scatter_df = returns_df_full.dropna().rename(columns={ticker1_sym: asset1_name, ticker2_sym: asset2_name})
    for d, row in filtered.iterrows():
        r1 = returns_df_full.loc[d, ticker1_sym]
        r2 = returns_df_full.loc[d, ticker2_sym]
        if pd.isna(r1) and pd.isna(r2) and pd.isna(row[ticker1_sym]) and pd.isna(row[ticker2_sym]): continue
        records.append({
            "תאריך ושעה": d.strftime("%d/%m/%Y %H:%M"),
            f"שער {asset1_name}": safe_round(row[ticker1_sym]), f"תשואה {asset1_name} (%)": safe_round(r1, 100),
            f"שער {asset2_name}": safe_round(row[ticker2_sym]), f"תשואה {asset2_name} (%)": safe_round(r2, 100),
            "הפרש (%)": safe_round(r1 - r2, 100) if pd.notna(r1) and pd.notna(r2) else None,
        })

# ==========================================
# בדיקות
# ==========================================
if scatter_df.empty or len(scatter_df) < 3:
    st.warning("⚠️ לא נמצאו מספיק נקודות נתונים. נסה להגדיל את מספר הימים או לשנות את חלון השעות.")
    st.stop()

col_a, col_b = scatter_df.columns[0], scatter_df.columns[1]
stats_res = compute_stats(scatter_df[col_a], scatter_df[col_b])

if stats_res["corr"] > 0.999 and ticker1_sym != ticker2_sym:
    st.error("⚠️ **שגיאת Yahoo Finance:** קורלציה קרובה ל-1.0 מצביעה על נתונים כפולים. שנה את מספר הימים (למשל מ-365 ל-360) ונסה שוב.")

# ==========================================
# לוח תוצאות
# ==========================================
st.markdown("<div style='height: 1.5rem'></div>", unsafe_allow_html=True)

r_val  = stats_res["corr"]
r2_val = stats_res["r2"]
p_val  = stats_res["pvalue"]
n_val  = stats_res["n"]

# מדדים
st.markdown(f"""
<div class='metrics-grid'>
    <div class='metric-card blue'>
        <div class='metric-icon'>📈</div>
        <div class='metric-value'>{r_val:.3f}</div>
        <div class='metric-label'>קורלציה (Pearson r)</div>
    </div>
    <div class='metric-card green'>
        <div class='metric-icon'>📐</div>
        <div class='metric-value'>{r2_val:.3f}</div>
        <div class='metric-label'>R² — הסבר שונות</div>
    </div>
    <div class='metric-card amber'>
        <div class='metric-icon'>🔬</div>
        <div class='metric-value'>{pvalue_label(p_val)}</div>
        <div class='metric-label'>מובהקות סטטיסטית</div>
    </div>
    <div class='metric-card purple'>
        <div class='metric-icon'>📋</div>
        <div class='metric-value'>{n_val:,}</div>
        <div class='metric-label'>תצפיות בחישוב</div>
    </div>
</div>
""", unsafe_allow_html=True)

# פרשנות
strength  = "חזקה מאוד 🔥" if abs(r_val) >= 0.8 else "חזקה 💪" if abs(r_val) >= 0.6 else "בינונית ⚡" if abs(r_val) >= 0.35 else "חלשה 🌫️"
direction = "חיובית" if r_val > 0 else "שלילית"
badge_cls = "badge-pos" if r_val > 0.35 else "badge-neg" if r_val < -0.35 else "badge-neut"
sig_text  = '<span class="badge badge-sig">מובהקת סטטיסטית ✅</span>' if p_val < 0.05 else '<span class="badge badge-neut">לא מובהקת סטטיסטית ❌</span>'

st.markdown(f"""
<div class='insight-box'>
    &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
    נמצאה קורלציה <span class='badge {badge_cls}'>{direction} {strength}</span> 
    בין <b>{asset1_name}</b> לבין <b>{asset2_name}</b>, והיא {sig_text}.<br>
    ה-R² של <b>{r2_val*100:.1f}%</b> אומר שכ-{r2_val*100:.0f}% מהתנודות של נכס אחד מוסברות על ידי הנכס השני.
    {f"<br>⚠️ <b>שים לב:</b> הקורלציה אינה מובהקת — ייתכן שהתוצאה מקרית. שקול להגדיל את מספר הימים." if p_val >= 0.05 else ""}
</div>
""", unsafe_allow_html=True)

# ==========================================
# גרף CCF
# ==========================================
if show_ccf and len(scatter_df) > ccf_max_lag * 2:
    st.markdown("<p class='sec-title'>🔍 מפת הובלה — מי מוביל את מי?</p>", unsafe_allow_html=True)
    st.info("💡 **קריאת הגרף:** עמודה גבוהה בצד ימין (השהיה חיובית) = נכס 1 מוביל. עמודה גבוהה בשמאל (שלילית) = נכס 2 מוביל. מרכז (0) = תגובה בו-זמנית.")

    lags, corrs = list(range(-ccf_max_lag, ccf_max_lag + 1)), []
    for lag in lags:
        temp_b = scatter_df[col_b].shift(-lag)
        temp_df = pd.DataFrame({"a": scatter_df[col_a], "b": temp_b}).dropna()
        if len(temp_df) > 3:
            c, _ = stats.pearsonr(temp_df["a"], temp_df["b"])
            corrs.append(c)
        else: corrs.append(np.nan)

    ccf_df = pd.DataFrame({"השהיה (Lag)": lags, "קורלציה": corrs})
    max_idx = ccf_df["קורלציה"].idxmax()
    best_lag = ccf_df.loc[max_idx, "השהיה (Lag)"]
    best_corr = ccf_df.loc[max_idx, "קורלציה"]
    colors = ['rgba(59,130,246,0.7)'] * len(ccf_df)
    colors[ccf_df[ccf_df["השהיה (Lag)"] == best_lag].index[0]] = '#10b981'

    fig_ccf = px.bar(ccf_df, x="השהיה (Lag)", y="קורלציה")
    fig_ccf.update_traces(marker_color=colors, marker_line_width=0)
    fig_ccf.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(255,255,255,0.03)",
        margin=dict(t=10, b=20, l=10, r=10), height=280,
        xaxis=dict(showgrid=False, color="#64748b", zeroline=False),
        yaxis=dict(gridcolor="rgba(255,255,255,0.06)", color="#64748b", zeroline=True, zerolinecolor="rgba(255,255,255,0.15)"),
        font=dict(family="Heebo")
    )
    st.plotly_chart(fig_ccf, use_container_width=True)

    lead_text = f"**{col_a}** מוביל את **{col_b}**" if best_lag > 0 else f"**{col_b}** מוביל את **{col_a}**" if best_lag < 0 else "הנכסים מגיבים בו-זמנית."
    st.success(f"📌 **תובנה:** הקורלציה הגבוהה ביותר ({best_corr:.3f}) נמצאה בהשהיה **{best_lag}**. {lead_text}")
    st.divider()

# ==========================================
# גרפים ראשיים
# ==========================================
g1, g2 = st.columns(2, gap="medium")

with g1:
    st.markdown("<p class='sec-title'>📊 פיזור נתונים וקו מגמה</p>", unsafe_allow_html=True)
    fig_s = px.scatter(scatter_df, x=col_a, y=col_b, trendline="ols",
                       labels={col_a: f"תשואה {col_a}", col_b: f"תשואה {col_b}"})
    fig_s.update_traces(
        selector=dict(mode='markers'),
        marker=dict(size=7, opacity=0.7, color="#3b82f6",
                    line=dict(width=0.5, color="rgba(255,255,255,0.3)"))
    )
    fig_s.update_traces(selector=dict(type='scatter', mode='lines'), line=dict(color="#10b981", width=2))
    fig_s.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(255,255,255,0.03)",
        margin=dict(t=10, b=20, l=10, r=10), height=320,
        xaxis=dict(showgrid=False, color="#64748b", zeroline=False, tickfont=dict(family="JetBrains Mono", size=10)),
        yaxis=dict(gridcolor="rgba(255,255,255,0.06)", color="#64748b", zeroline=True, zerolinecolor="rgba(255,255,255,0.15)", tickfont=dict(family="JetBrains Mono", size=10)),
        font=dict(family="Heebo"), showlegend=False
    )
    st.plotly_chart(fig_s, use_container_width=True)

with g2:
    if show_rolling and len(scatter_df) >= rolling_window:
        st.markdown(f"<p class='sec-title'>📈 Rolling Correlation — חלון {rolling_window}</p>", unsafe_allow_html=True)
        rolling_corr = scatter_df[col_a].rolling(rolling_window).corr(scatter_df[col_b])
        fig_r = go.Figure()
        fig_r.add_hline(y=0, line_dash="dash", line_color="rgba(255,255,255,0.2)", line_width=1)
        fig_r.add_hline(y=0.5,  line_dash="dot", line_color="rgba(16,185,129,0.3)", line_width=1)
        fig_r.add_hline(y=-0.5, line_dash="dot", line_color="rgba(239,68,68,0.3)",  line_width=1)
        fig_r.add_trace(go.Scatter(
            x=rolling_corr.index, y=rolling_corr.values, mode="lines",
            fill="tozeroy",
            fillcolor="rgba(59,130,246,0.08)",
            line=dict(color="#3b82f6", width=2)
        ))
        fig_r.update_layout(
            yaxis=dict(range=[-1.1, 1.1], title="קורלציה", gridcolor="rgba(255,255,255,0.06)",
                       color="#64748b", zeroline=False, tickfont=dict(family="JetBrains Mono", size=10)),
            xaxis=dict(showgrid=False, color="#64748b", zeroline=False),
            margin=dict(t=10, b=20, l=10, r=10), height=320,
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(255,255,255,0.03)",
            font=dict(family="Heebo"), showlegend=False
        )
        st.plotly_chart(fig_r, use_container_width=True)
    else:
        st.info("💡 הפעל את אפשרות Rolling Correlation למעלה, או הגדל את מספר הימים.")

# ==========================================
# טבלה + ייצוא
# ==========================================
st.divider()
st.markdown("<p class='sec-title'>🗂️ נתונים מפורטים</p>", unsafe_allow_html=True)

summary_df = pd.DataFrame(records)

tab1, tab2 = st.tabs(["📋 טבלת נתונים", "📥 ייצוא"])

with tab1:
    st.dataframe(
        summary_df.style.background_gradient(cmap="Blues", subset=[c for c in summary_df.columns if "תשואה" in c or "הפרש" in c]),
        use_container_width=True, height=280
    )

with tab2:
    st.markdown("""
    <div style='color: #94a3b8; font-size: 0.9rem; direction: rtl; text-align: right; padding: 0.5rem 0;'>
        הנתונים ייצאו לקובץ Excel עם נוסחת CORREL חיה לאימות עצמאי.
    </div>
    """, unsafe_allow_html=True)
    
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        summary_df.to_excel(writer, index=False, sheet_name='Correlation Data')
        worksheet = writer.sheets['Correlation Data']
        try:
            cols = list(summary_df.columns)
            if mode == "⏱️ חלון שעות מסחר":
                ret1_col, ret2_col = f"תשואה {asset1_name} (%)", f"תשואה {asset2_name} (%)"
            else:
                ret1_col, ret2_col = f"תשואה {asset1_name} (%)", f"תשואה {asset2_name} (%)"
            ret1_idx, ret2_idx = cols.index(ret1_col) + 1, cols.index(ret2_col) + 1
            c1_let, c2_let = get_column_letter(ret1_idx), get_column_letter(ret2_idx)
            form_col_let = get_column_letter(len(cols) + 2)
            num_rows = len(summary_df)
            worksheet[f"{form_col_let}1"] = "קורלציה (Excel חי)"
            worksheet[f"{form_col_let}2"] = f"=CORREL({c1_let}2:{c1_let}{num_rows+1}, {c2_let}2:{c2_let}{num_rows+1})"
        except Exception:
            pass

    st.download_button(
        label="📥 הורד קובץ Excel",
        data=buffer,
        file_name=f"correlation_{ticker1_sym}_{ticker2_sym}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

# ==========================================
# FOOTER
# ==========================================
st.markdown(f"""
<div style='text-align: center; color: #334155; font-size: 0.78rem; padding: 2rem 0 0.5rem; direction: rtl;'>
    נתונים מ-Yahoo Finance · שעון ישראל (Asia/Jerusalem) · 
    <span style='font-family: JetBrains Mono, monospace;'>{asset1_name}</span> 
    &nbsp;↔&nbsp; 
    <span style='font-family: JetBrains Mono, monospace;'>{asset2_name}</span> · 
    {days_back} ימים · {n_val:,} תצפיות
</div>
""", unsafe_allow_html=True)
