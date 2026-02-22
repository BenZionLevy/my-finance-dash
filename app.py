import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from scipy import stats
import io
from openpyxl.utils import get_column_letter

# הגדרת העמוד חייבת להיות הפקודה הראשונה
st.set_page_config(page_title="ניתוח קורלציות מקצועי", layout="wide", page_icon="📊")

# ==========================================
# פונקציות עזר קטנות
# ==========================================
def safe_round(val, mult=1.0):
    if pd.isna(val): return None
    return round(float(val) * mult, 2)

# ==========================================
# עיצוב CSS מותאם אישית (מודרני ומותאם לנייד)
# ==========================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Rubik:wght@300;400;500;600;700&display=swap');
    
    /* עיצוב כללי ורקע */
    .stApp {
        background: #f8fafc;
    }
    html, body, [class*="css"] {
        font-family: 'Rubik', sans-serif;
        direction: rtl;
    }

    /* כותרות ראשיות */
    .main-header {
        text-align: center;
        padding: 2rem 0 0.5rem 0;
        font-size: 2.8rem;
        font-weight: 800;
        background: linear-gradient(135deg, #0f172a 0%, #2563eb 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin-bottom: 0;
    }
    .sub-header {
        text-align: center;
        color: #64748b;
        font-size: 1.1rem;
        font-weight: 400;
        margin-bottom: 2.5rem;
    }

    /* עיצוב כרטיסיות עבור מדדים (Metrics) */
    div[data-testid="stMetric"] {
        background-color: white;
        border-radius: 12px;
        padding: 1rem;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -2px rgba(0, 0, 0, 0.05);
        border: 1px solid #e2e8f0;
        transition: transform 0.2s ease-in-out;
    }
    div[data-testid="stMetric"]:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
    }
    
    /* תגיות צבעוניות */
    .stat-badge {
        display: inline-block;
        padding: 0.35rem 0.8rem;
        border-radius: 20px;
        font-size: 0.95rem;
        font-weight: 600;
        margin: 0.15rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .badge-green { background: #ecfdf5; color: #047857; border: 1px solid #a7f3d0; }
    .badge-red   { background: #fef2f2; color: #b91c1c; border: 1px solid #fecaca; }
    .badge-blue  { background: #eff6ff; color: #1d4ed8; border: 1px solid #bfdbfe; }
    .badge-gray  { background: #f8fafc; color: #475569; border: 1px solid #e2e8f0; }
    
    /* כותרות אזורים */
    .section-title {
        font-size: 1.35rem;
        font-weight: 700;
        color: #1e293b;
        margin-top: 2rem;
        margin-bottom: 1.5rem;
        text-align: right;
        direction: rtl;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    .section-title::after {
        content: "";
        flex: 1;
        height: 2px;
        background: #e2e8f0;
        margin-right: 15px;
        border-radius: 2px;
    }

    /* קופסת תובנות / מסקנות */
    .info-box {
        background: white;
        border-right: 5px solid #3b82f6;
        border-radius: 10px;
        padding: 1.5rem;
        color: #334155;
        direction: rtl;
        text-align: right;
        font-size: 1.1rem;
        line-height: 1.6;
        margin: 1.5rem 0 2.5rem 0;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
    }

    /* === התאמות למסכים קטנים (סמארטפונים) === */
    @media (max-width: 768px) {
        .main-header { font-size: 2rem; padding: 1rem 0; }
        .sub-header { font-size: 0.95rem; margin-bottom: 1.5rem; }
        .info-box { font-size: 1rem; padding: 1.2rem; }
        .section-title { font-size: 1.2rem; }
        div[data-testid="stMetric"] { margin-bottom: 0.5rem; }
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# כותרת ראשית
# ==========================================
st.markdown(f"<h1 class='main-header'>ניתוח קורלציות מקצועי</h1>", unsafe_allow_html=True)
st.markdown(f"<p class='sub-header'>מצא קשרים מובהקים בין נכסים פיננסיים בלחיצת כפתור</p>", unsafe_allow_html=True)

# ==========================================
# שלב 1: הגדרות נכסים (בתוך חלונית נפתחת מעוצבת)
# ==========================================
DEFAULT_TICKERS = {
    "לאומי": "LUMI.TA", "פועלים": "POLI.TA", "דיסקונט": "DSCT.TA",
    "מדד ת\"א 35": "TA35.TA", "מדד ת\"א 125": "TA125.TA", "מדד בנקים 5": "TA-BANKS.TA",
    "S&P 500 Futures": "ES=F", 'נאסד"ק 100': "NQ=F", "USD/ILS": "ILS=X", "XLF (פיננסים ארה\"ב)": "XLF"
}

st.markdown("<div class='section-title'>⚙️ שלב 1: הגדרות הניתוח</div>", unsafe_allow_html=True)

with st.expander("לחץ כאן לפתיחה/סגירה של פאנל ההגדרות", expanded=True):
    col_opt1, col_opt2, col_opt3 = st.columns(3)
    
    with col_opt1:
        st.markdown("**1️⃣ בחירת נכסים**")
        use_custom = st.checkbox("הזן טיקר חופשי (מתקדם)", value=False)
        if use_custom:
            custom1 = st.text_input("טיקר 1 (לדוגמה: AAPL)", value="AAPL").upper().strip()
            custom2 = st.text_input("טיקר 2 (לדוגמה: MSFT)", value="MSFT").upper().strip()
            asset1_name, asset2_name = custom1, custom2
            ticker1_sym, ticker2_sym = custom1, custom2
        else:
            ticker_names = list(DEFAULT_TICKERS.keys())
            asset1_name = st.selectbox("נכס 1", ticker_names, index=0)
            asset2_name = st.selectbox("נכס 2", ticker_names, index=8)
            ticker1_sym = DEFAULT_TICKERS[asset1_name]
            ticker2_sym = DEFAULT_TICKERS[asset2_name]
            
        if ticker1_sym == ticker2_sym:
            st.error("⚠️ בחרת את אותו נכס פעמיים. אנא בחר שני נכסים שונים.")
            st.stop()

    with col_opt2:
        st.markdown("**2️⃣ זמנים וסוג תשואה**")
        mode = st.radio("מבנה הניתוח:", [
            "1. יומי: שער סגירה רשמי", "2. יומי: שעה קבועה ביום",
            "3. מהלך מסחר: חלון שעות", "4. תוך-יומי: קפיצות זמן"
        ])
        return_type = st.radio("סוג תשואה:", ["אחוז שינוי רגיל (Simple)", "תשואה לוגריתמית (Log)"])
        use_log_returns = "לוגריתמית" in return_type

    with col_opt3:
        st.markdown("**3️⃣ חלון זמן ומתקדם**")
        start_hour, end_hour, target_hour = None, None, None
        interval_choice, lag_minutes = "1d", 0
        
        is_daily_mode = mode == "1. יומי: שער סגירה רשמי"
        max_days = 730 if is_daily_mode else 60
        default_days = 365 if is_daily_mode else 60

        if mode == "2. יומי: שעה קבועה ביום":
            target_hour = st.selectbox("בחר שעה קבועה:", [f"{h:02d}:00" for h in range(8, 23)], index=2)
            interval_choice = "5m"
        elif mode in ["3. מהלך מסחר: חלון שעות", "4. תוך-יומי: קפיצות זמן"]:
            col_h1, col_h2 = st.columns(2)
            with col_h1: start_hour = st.selectbox("שעת התחלה:", [f"{h:02d}:00" for h in range(8, 23)], index=2)
            with col_h2: end_hour = st.selectbox("שעת סיום:", [f"{h:02d}:00" for h in range(8, 23)], index=8)
            
            if mode == "4. תוך-יומי: קפיצות זמן":
                int_map = {"5 דקות": "5m", "15 דקות": "15m", "30 דקות": "30m", "1 שעה": "60m"}
                interval_choice = int_map[st.selectbox("גודל קפיצה:", list(int_map.keys()))]
                lag_minutes = st.number_input("השהיה לנכס 2 (בדקות):", min_value=0, max_value=600, value=0, step=5)
            else:
                interval_choice = "5m"

        days_back = st.number_input("כמה ימים אחורה לנתח?", min_value=1, max_value=max_days, value=default_days)
    
    st.divider()
    c_adv1, c_adv2 = st.columns(2)
    with c_adv1:
        show_rolling = st.checkbox("הצג מפת קורלציה מתגלגלת (Rolling Correlation)", value=True)
        if show_rolling:
            rolling_window = st.slider("גודל חלון Rolling:", min_value=5, max_value=100, value=20)
    with c_adv2:
        show_ccf = st.checkbox("🔍 מצא מי מגיב למי (Cross-Correlation)", value=False)
        if show_ccf:
            ccf_max_lag = st.slider("מספר השהיות מקסימלי לבדיקה:", min_value=1, max_value=20, value=10)

# ==========================================
# פונקציות חישוב ומשיכה
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
    return f"p = {p:.3f} ❌ לא מובהק"

def calculate_returns(df, is_log):
    if is_log:
        return np.log(df / df.shift(1))
    return df.pct_change()

# ==========================================
# עיבוד הנתונים
# ==========================================
with st.spinner("🔄 שואב ומעבד נתונים מהרשת..."):
    raw_df = fetch_data(ticker1_sym, ticker2_sym, days_back, interval_choice)

if raw_df.empty:
    st.error("❌ לא ניתן למשוך נתונים. בדוק את חיבור האינטרנט או ודא שהטיקרים נכונים.")
    st.stop()

scatter_df = pd.DataFrame()
records = []

if mode == "1. יומי: שער סגירה רשמי":
    returns_df_full = calculate_returns(raw_df, use_log_returns)
    scatter_df = returns_df_full.dropna().rename(columns={ticker1_sym: asset1_name, ticker2_sym: asset2_name})
    
    for d, row in raw_df.iterrows():
        r1 = returns_df_full.loc[d, ticker1_sym]
        r2 = returns_df_full.loc[d, ticker2_sym]
        records.append({
            "תאריך": d.strftime("%d/%m/%Y"),
            f"סגירה {asset1_name}": safe_round(row[ticker1_sym]),
            f"תשואה {asset1_name} (%)": safe_round(r1, 100),
            f"סגירה {asset2_name}": safe_round(row[ticker2_sym]),
            f"תשואה {asset2_name} (%)": safe_round(r2, 100),
            "הפרש תשואות (%)": safe_round(r1 - r2, 100) if pd.notna(r1) and pd.notna(r2) else None,
        })

elif mode == "2. יומי: שעה קבועה ביום":
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
                "הפרש תשואות (%)": safe_round(r1 - r2, 100) if pd.notna(r1) and pd.notna(r2) else None,
            })

elif mode == "3. מהלך מסחר: חלון שעות":
    filtered = raw_df.between_time(start_hour, end_hour)
    dates = np.unique(filtered.index.date)
    calc, calc_dates = [], []
    
    for d in dates:
        try:
            day = filtered.loc[str(d)]
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
            f"תשואת חלון {asset1_name} (%)": safe_round(ret1, 100),
            f"פתיחה {asset2_name}": safe_round(v2.iloc[0]) if len(v2)>0 else None, 
            f"סגירה {asset2_name}": safe_round(v2.iloc[-1]) if len(v2)>0 else None,
            f"תשואת חלון {asset2_name} (%)": safe_round(ret2, 100),
            "הפרש תשואות (%)": safe_round(ret1 - ret2, 100) if pd.notna(ret1) and pd.notna(ret2) else None,
        })
        
    scatter_df = pd.DataFrame(calc)
    if not scatter_df.empty: scatter_df.index = calc_dates

elif mode == "4. תוך-יומי: קפיצות זמן":
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
            "הפרש תשואות (%)": safe_round(r1 - r2, 100) if pd.notna(r1) and pd.notna(r2) else None,
        })

# ==========================================
# שלב 2: תצוגת תוצאות (לוח מחוונים)
# ==========================================
st.markdown("<div class='section-title'>📊 שלב 2: תוצאות הניתוח</div>", unsafe_allow_html=True)
st.markdown(f"<p class='sub-header' style='margin-bottom: 1rem;'><span dir='ltr'><b>{asset1_name}</b></span> מול <span dir='ltr'><b>{asset2_name}</b></span> | {days_back} ימי מסחר אחרונים | שעון ישראל</p>", unsafe_allow_html=True)

if scatter_df.empty or len(scatter_df) < 3:
    st.warning("⚠️ לא נמצאו מספיק נתונים משותפים לחישוב קורלציה אמינה. נסה להגדיל את כמות הימים או את חלון המסחר.")
    st.stop()

col_a, col_b = scatter_df.columns[0], scatter_df.columns[1]
stats_res = compute_stats(scatter_df[col_a], scatter_df[col_b])

if stats_res["corr"] > 0.999 and ticker1_sym != ticker2_sym:
    st.error("⚠️ **התראת נתונים:** הקורלציה יצאה קרובה ל-1.0. זהו באג מוכר של Yahoo Finance המחזיר נתונים כפולים בתאריכים מסוימים. נסה לשנות את כמות הימים ל-728 או 730 כדי לתקן זאת.")

# כרטיסיות נתונים מרחפות
c1, c2, c3, c4 = st.columns(4)
c1.metric("📈 קורלציה (Pearson)", f"{stats_res['corr']:.3f}")
c2.metric("📐 R² (אחוז הסבר שונות)", f"{stats_res['r2']:.3f}")
c3.metric("🔬 מובהקות סטטיסטית", pvalue_label(stats_res['pvalue']))
c4.metric("📋 תצפיות בחישוב", stats_res['n'])

r_val = stats_res["corr"]
strength = "חזקה מאוד" if abs(r_val) >= 0.8 else "חזקה" if abs(r_val) >= 0.6 else "בינונית" if abs(r_val) >= 0.35 else "חלשה"
direction = "חיובית" if r_val > 0 else "שלילית"
badge_class = "badge-green" if r_val > 0.35 else "badge-red" if r_val < -0.35 else "badge-gray"
sig_text = "מובהקת סטטיסטית ✅" if stats_res["pvalue"] < 0.05 else "לא מובהקת סטטיסטית (ייתכן שזה מקרי) ❌"

st.markdown(f"""
<div class='info-box'>
    🧠 <b>מה זה אומר בשפה פשוטה?</b> נמצאה קורלציה <span class='stat-badge {badge_class}'>{direction} {strength}</span> 
    והיא {sig_text}. <br><br>
    המשמעות של מדד ה-R² היא ש-<b>{stats_res['r2']*100:.1f}%</b> מתנועת התשואות (מבוסס {return_type.split()[0]}) של נכס אחד ניתנת להסבר על ידי התנועה של הנכס השני.
</div>
""", unsafe_allow_html=True)

# ==========================================
# שלב 3: ויזואליזציה (גרפים)
# ==========================================
st.markdown("<div class='section-title'>📉 שלב 3: ויזואליזציה</div>", unsafe_allow_html=True)

# --- גרף CCF ---
if show_ccf and len(scatter_df) > ccf_max_lag * 2:
    st.info("💡 **איך לקרוא את מפת ההובלה?** הגרף בודק מי מגיב למי. אם העמודה הגבוהה ביותר נמצאת בצד הימני, **נכס 1 מוביל**. אם בשמאלי, **נכס 2 מוביל**. מרכז ב-0 = מגיבים יחד.")
    
    lags = list(range(-ccf_max_lag, ccf_max_lag + 1))
    corrs = []
    
    for lag in lags:
        temp_b = scatter_df[col_b].shift(-lag)
        temp_df = pd.DataFrame({"a": scatter_df[col_a], "b": temp_b}).dropna()
        if len(temp_df) > 3:
            c, _ = stats.pearsonr(temp_df["a"], temp_df["b"])
            corrs.append(c)
        else:
            corrs.append(np.nan)
            
    ccf_df = pd.DataFrame({"השהיה (Lag)": lags, "קורלציה": corrs})
    fig_ccf = px.bar(ccf_df, x="השהיה (Lag)", y="קורלציה", title="מפת הובלה (Cross-Correlation)", template="plotly_white")
    
    max_idx = ccf_df["קורלציה"].idxmax()
    best_lag = ccf_df.loc[max_idx, "השהיה (Lag)"]
    best_corr = ccf_df.loc[max_idx, "קורלציה"]
    colors = ['#3b82f6'] * len(ccf_df)
    colors[ccf_df[ccf_df["השהיה (Lag)"] == best_lag].index[0]] = '#ef4444' # הדגשת העמודה המובילה
    
    fig_ccf.update_traces(marker_color=colors)
    fig_ccf.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", margin=dict(t=40, b=20), title_x=0.5)
    st.plotly_chart(fig_ccf, use_container_width=True)
    
    lead_text = f"**{col_a}** מוביל את **{col_b}**" if best_lag > 0 else f"**{col_b}** מוביל את **{col_a}**" if best_lag < 0 else "הנכסים מגיבים באותו זמן בדיוק (אין הובלה)."
    st.success(f"📌 **תובנת מערכת:** הקורלציה החזקה ביותר ({best_corr:.3f}) נמצאה בהשהיה של **{best_lag}**. מסקנה: {lead_text}")

# --- שאר הגרפים ---
g1, g2 = st.columns([1, 1])
with g1:
    fig_scatter = px.scatter(scatter_df, x=col_a, y=col_b, trendline="ols", 
                             labels={col_a: f"תשואה {col_a}", col_b: f"תשואה {col_b}"},
                             title="פיזור נתונים וקו מגמה", template="plotly_white")
    fig_scatter.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", title_x=0.5)
    fig_scatter.update_traces(marker=dict(size=8, opacity=0.7, color="#2563eb", line=dict(width=1, color="DarkSlateGrey")))
    st.plotly_chart(fig_scatter, use_container_width=True)

with g2:
    if show_rolling and len(scatter_df) >= rolling_window:
        rolling_corr = scatter_df[col_a].rolling(rolling_window).corr(scatter_df[col_b])
        fig_roll = go.Figure()
        fig_roll.add_hline(y=0, line_dash="dash", line_color="#cbd5e1")
        fig_roll.add_trace(go.Scatter(x=rolling_corr.index, y=rolling_corr.values, mode="lines", fill="tozeroy", 
                                      line=dict(color="#10b981", width=2.5), fillcolor="rgba(16, 185, 129, 0.2)"))
        fig_roll.update_layout(title=f"קורלציה מתגלגלת (חלון זמן: {rolling_window})", title_x=0.5,
                               yaxis=dict(range=[-1.1, 1.1], title="מדד קורלציה"), 
                               margin=dict(t=40, b=20, l=10, r=10), 
                               template="plotly_white", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig_roll, use_container_width=True)
    elif show_rolling:
        st.info("💡 המתן או בחר חלון זמן קצר יותר כדי לראות את ה-Rolling Correlation.")

# ==========================================
# שלב 4: נתונים גולמיים וייצוא
# ==========================================
st.markdown("<div class='section-title'>📋 שלב 4: נתונים גולמיים וייצוא לאקסל</div>", unsafe_allow_html=True)
summary_df = pd.DataFrame(records)
t1, t2 = st.columns([2, 1])

with t1:
    st.dataframe(summary_df, use_container_width=True, height=250)

with t2:
    st.markdown("<br>", unsafe_allow_html=True) # ריווח קל
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        summary_df.to_excel(writer, index=False, sheet_name='Correlation Data')
        worksheet = writer.sheets['Correlation Data']
        try:
            cols = list(summary_df.columns)
            if mode == "3. מהלך מסחר: חלון שעות":
                ret1_col, ret2_col = f"תשואת חלון {asset1_name} (%)", f"תשואת חלון {asset2_name} (%)"
            else:
                ret1_col, ret2_col = f"תשואה {asset1_name} (%)", f"תשואה {asset2_name} (%)"
                
            ret1_idx, ret2_idx = cols.index(ret1_col) + 1, cols.index(ret2_col) + 1
            c1_let, c2_let = get_column_letter(ret1_idx), get_column_letter(ret2_idx)
            form_col_let = get_column_letter(len(cols) + 2)
            num_rows = len(summary_df)
            
            worksheet[f"{form_col_let}1"] = "קורלציה (אקסל חי)"
            worksheet[f"{form_col_let}2"] = f"=CORREL({c1_let}2:{c1_let}{num_rows+1}, {c2_let}2:{c2_let}{num_rows+1})"
        except Exception as e:
            pass

    st.download_button(
        label="📥 הורד את הנתונים המלאים לאקסל",
        data=buffer,
        file_name=f"correlation_{ticker1_sym}_{ticker2_sym}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
        type="primary"
    )
