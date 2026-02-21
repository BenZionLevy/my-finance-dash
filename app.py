import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from scipy import stats
import io
from openpyxl.utils import get_column_letter
from openpyxl.styles import Font, PatternFill

st.set_page_config(page_title="ניתוח קורלציות מקצועי", layout="wide", page_icon="📊")

# ==========================================
# פונקציות עזר קטנות
# ==========================================
def safe_round(val, mult=1.0):
    """פונקציה שמחזירה תא ריק (None) לאקסל במקום שגיאה במקרה של נתון חסר"""
    if pd.isna(val): return None
    return round(float(val) * mult, 2)

# ==========================================
# עיצוב CSS מותאם אישית
# ==========================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Heebo:wght@300;400;600;700&display=swap');
    
    .stApp {
        background: linear-gradient(rgba(248, 250, 252, 0.92), rgba(248, 250, 252, 0.97)), 
                    url('https://images.unsplash.com/photo-1551288049-bebda4e38f71?q=80&w=2070&auto=format&fit=crop');
        background-size: cover;
        background-attachment: fixed;
        background-position: center;
    }
    html, body, [class*="css"] {
        font-family: 'Heebo', sans-serif;
        direction: rtl;
    }
    .main-header {
        text-align: center;
        padding: 1.5rem 0 0.5rem 0;
        font-size: 2.5rem;
        font-weight: 700;
        background: linear-gradient(135deg, #0f172a 0%, #1e3a8a 50%, #1e40af 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    .sub-header {
        text-align: center;
        color: #475569;
        font-size: 1.1rem;
        margin-bottom: 2rem;
    }
    .stat-badge {
        display: inline-block;
        padding: 0.3rem 0.8rem;
        border-radius: 20px;
        font-size: 0.9rem;
        font-weight: 600;
        margin: 0.15rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .badge-green { background: #d1fae5; color: #065f46; border: 1px solid #a7f3d0; }
    .badge-red   { background: #fee2e2; color: #991b1b; border: 1px solid #fecaca; }
    .badge-blue  { background: #dbeafe; color: #1e40af; border: 1px solid #bfdbfe; }
    .badge-gray  { background: #f3f4f6; color: #374151; border: 1px solid #e5e7eb; }
    .section-title {
        font-size: 1.25rem;
        font-weight: 600;
        color: #1e293b;
        margin-bottom: 1rem;
        text-align: right;
        direction: rtl;
        border-bottom: 2px solid #cbd5e1;
        padding-bottom: 8px;
    }
    .info-box {
        background: rgba(255, 255, 255, 0.95);
        border-right: 4px solid #3b82f6;
        border-radius: 8px;
        padding: 1.2rem;
        color: #334155;
        direction: rtl;
        text-align: right;
        font-size: 1.05rem;
        margin-bottom: 2rem;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# הגדרות נכסים (Sidebar)
# ==========================================
DEFAULT_TICKERS = {
    "לאומי": "LUMI.TA",
    "פועלים": "POLI.TA",
    "דיסקונט": "DSCT.TA",
    "מדד ת\"א 35": "TA35.TA",
    "מדד ת\"א 125": "TA125.TA",
    "מדד בנקים 5": "TA-BANKS.TA",
    "S&P 500 Futures": "ES=F",
    'נאסד"ק 100': "NQ=F",
    "USD/ILS": "ILS=X",
    "XLF (פיננסים ארה\"ב)": "XLF"
}

with st.sidebar:
    st.markdown("<h3 style='direction:rtl; text-align:right;'>🎛️ הגדרות ניתוח</h3>", unsafe_allow_html=True)
    st.divider()

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

    st.divider()
    mode = st.radio("**מבנה הניתוח**", [
        "1. יומי: שער סגירה רשמי",
        "2. יומי: שעה קבועה ביום",
        "3. מהלך מסחר: חלון שעות",
        "4. תוך-יומי: קפיצות זמן"
    ])

    st.divider()
    start_hour, end_hour, target_hour = None, None, None
    interval_choice, lag_minutes = "1d", 0
    
    is_daily_mode = mode == "1. יומי: שער סגירה רשמי"
    max_days = 730 if is_daily_mode else 60
    default_days = 365 if is_daily_mode else 60

    if mode == "2. יומי: שעה קבועה ביום":
        target_hour = st.selectbox("בחר שעה קבועה:", [f"{h:02d}:00" for h in range(8, 23)], index=2)
        interval_choice = "5m"
    elif mode == "3. מהלך מסחר: חלון שעות" or mode == "4. תוך-יומי: קפיצות זמן":
        col_t1, col_t2 = st.columns(2)
        with col_t2: start_hour = st.selectbox("שעת התחלה:", [f"{h:02d}:00" for h in range(8, 23)], index=2)
        with col_t1: end_hour = st.selectbox("שעת סיום:", [f"{h:02d}:00" for h in range(8, 23)], index=8)
        if mode == "4. תוך-יומי: קפיצות זמן":
            int_map = {"5 דקות": "5m", "15 דקות": "15m", "30 דקות": "30m", "1 שעה": "60m"}
            interval_choice = int_map[st.selectbox("גודל קפיצה:", list(int_map.keys()))]
            lag_minutes = st.number_input("השהיה לנכס 2 (דקות):", min_value=0, max_value=600, value=0, step=5)
        else:
            interval_choice = "5m"

    days_back = st.number_input("ימים אחורה:", min_value=1, max_value=max_days, value=default_days)

    st.divider()
    show_rolling = st.checkbox("הצג גרף Rolling Correlation", value=True)
    if show_rolling:
        rolling_window = st.slider("חלון Rolling (מספר תצפיות):", min_value=5, max_value=100, value=20)

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

# ==========================================
# עיבוד הנתונים
# ==========================================
with st.spinner("מושך ומעבד נתונים..."):
    raw_df = fetch_data(ticker1_sym, ticker2_sym, days_back, interval_choice)

if raw_df.empty:
    st.error("לא ניתן למשוך נתונים. בדוק את חיבור האינטרנט או שהטיקרים נכונים.")
    st.stop()

scatter_df = pd.DataFrame()
records = []

if mode == "1. יומי: שער סגירה רשמי":
    returns_df_full = raw_df.pct_change()
    scatter_df = returns_df_full.dropna().rename(columns={ticker1_sym: asset1_name, ticker2_sym: asset2_name})
    
    for d, row in raw_df.iterrows():
        r1 = returns_df_full.loc[d, ticker1_sym]
        r2 = returns_df_full.loc[d, ticker2_sym]
        records.append({
            "תאריך": d.strftime("%d/%m/%Y"),
            f"שער סגירה {asset1_name}": safe_round(row[ticker1_sym]),
            f"תשואה {asset1_name} (%)": safe_round(r1, 100),
            f"שער סגירה {asset2_name}": safe_round(row[ticker2_sym]),
            f"תשואה {asset2_name} (%)": safe_round(r2, 100),
            "הפרש תשואות (%)": safe_round(r1 - r2, 100) if pd.notna(r1) and pd.notna(r2) else None,
        })

elif mode == "2. יומי: שעה קבועה ביום":
    target_end = f"{int(target_hour[:2]):02d}:59"
    hour_df = raw_df.between_time(target_hour, target_end).dropna(how="all")
    if not hour_df.empty:
        hour_df['date_str'] = hour_df.index.date.astype(str)
        daily = hour_df.groupby('date_str').first()
        returns_df_full = daily.pct_change()
        
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
        ret1 = (v1.iloc[-1] - v1.iloc[0]) / v1.iloc[0] if len(v1) >= 2 else np.nan
        ret2 = (v2.iloc[-1] - v2.iloc[0]) / v2.iloc[0] if len(v2) >= 2 else np.nan
        
        if pd.isna(ret1) and pd.isna(ret2): continue
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
            
    returns_df_full = filtered.pct_change()
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
# תצוגת האתר
# ==========================================
st.markdown(f"<h1 class='main-header'>ניתוח קורלציות מקצועי</h1>", unsafe_allow_html=True)
st.markdown(f"<p class='sub-header'><span dir='ltr'><b>{asset1_name}</b></span> מול <span dir='ltr'><b>{asset2_name}</b></span> | {days_back} ימים אחורה | שעון ישראל</p>", unsafe_allow_html=True)

if scatter_df.empty or len(scatter_df) < 3:
    st.warning("⚠️ לא נמצאו מספיק נתונים משותפים לחישוב קורלציה אמינה. נסה להגדיל את הימים או את חלון המסחר.")
    st.stop()

col_a, col_b = scatter_df.columns[0], scatter_df.columns[1]
stats_res = compute_stats(scatter_df[col_a], scatter_df[col_b])

# --- הגנה בפני הבאג של יאהו ---
if stats_res["corr"] > 0.999 and ticker1_sym != ticker2_sym:
    st.error("⚠️ **התראת נתונים:** הקורלציה יצאה קרובה ל-1.0 מושלם בין שני נכסים שונים. זהו באג ידוע בשרתי המטמון של Yahoo Finance שמחזיר נתונים כפולים כשמבקשים כמות ימים מאוד ספציפית (למשל 729). **מומלץ לשנות את כמות הימים ל-728 או 730 כדי לאפס את המטמון ולקבל תוצאה אמיתית.**")

c1, c2, c3, c4 = st.columns(4)
c1.metric("📈 קורלציה (Pearson)", f"{stats_res['corr']:.3f}")
c2.metric("📐 R² (הסבר שונות)", f"{stats_res['r2']:.3f}")
c3.metric("🔬 מובהקות", pvalue_label(stats_res['pvalue']))
c4.metric("📋 תצפיות בחישוב", stats_res['n'])

r_val = stats_res["corr"]
strength = "חזקה מאוד" if abs(r_val) >= 0.8 else "חזקה" if abs(r_val) >= 0.6 else "בינונית" if abs(r_val) >= 0.35 else "חלשה"
direction = "חיובית" if r_val > 0 else "שלילית"
badge_class = "badge-green" if r_val > 0.35 else "badge-red" if r_val < -0.35 else "badge-gray"
sig_text = "מובהקת סטטיסטית ✅" if stats_res["pvalue"] < 0.05 else "לא מובהקת סטטיסטית (ייתכן שזה מקרי) ❌"

st.markdown(f"""
<div class='info-box'>
    🧠 <b>פרשנות כמותית:</b> נמצאה קורלציה <span class='stat-badge {badge_class}'>{direction} {strength}</span> 
    והיא {sig_text}. <br>
    המשמעות של ה-R² היא ש-<b>{stats_res['r2']*100:.1f}%</b> מתנועת התשואות של נכס אחד מוסברת ע"י התנועה של הנכס השני.
</div>
""", unsafe_allow_html=True)

# --- גרפים ---
g1, g2 = st.columns([1, 1])

with g1:
    st.markdown("<p class='section-title'>פיזור נתונים וקו מגמה</p>", unsafe_allow_html=True)
    fig_scatter = px.scatter(scatter_df, x=col_a, y=col_b, trendline="ols", labels={col_a: f"תשואה {col_a}", col_b: f"תשואה {col_b}"})
    fig_scatter.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(255,255,255,0.7)")
    fig_scatter.update_traces(marker=dict(size=7, opacity=0.8, color="#3b82f6"))
    st.plotly_chart(fig_scatter, use_container_width=True)

with g2:
    if show_rolling and len(scatter_df) >= rolling_window:
        st.markdown(f"<p class='section-title'>Rolling Correlation (חלון של {rolling_window})</p>", unsafe_allow_html=True)
        rolling_corr = scatter_df[col_a].rolling(rolling_window).corr(scatter_df[col_b])
        fig_roll = go.Figure()
        fig_roll.add_hline(y=0, line_dash="dash", line_color="gray")
        fig_roll.add_trace(go.Scatter(x=rolling_corr.index, y=rolling_corr.values, mode="lines", fill="tozeroy", line=dict(color="#10b981", width=2)))
        fig_roll.update_layout(yaxis=dict(range=[-1.1, 1.1], title="קורלציה"), margin=dict(t=10, b=10, l=10, r=10), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(255,255,255,0.7)")
        st.plotly_chart(fig_roll, use_container_width=True)
    else:
        st.info("💡 המתן או בחר חלון זמן קצר יותר כדי לראות את ה-Rolling Correlation.")

# --- טבלת אקסל וקישורים תחתונים ---
st.divider()
summary_df = pd.DataFrame(records)
t1, t2 = st.columns([2, 1])

with t1:
    st.markdown("<p class='section-title'>טבלת נתונים מפורטת (כולל ימים ללא חפיפה)</p>", unsafe_allow_html=True)
    st.dataframe(summary_df, use_container_width=True, height=250)

with t2:
    st.markdown("<p class='section-title'>ייצוא ואימות</p>", unsafe_allow_html=True)
    
    # --- הזרקת נוסחת אקסל (CORREL) במקום פשוט לייצא טקסט ---
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        summary_df.to_excel(writer, index=False, sheet_name='Correlation Data')
        worksheet = writer.sheets['Correlation Data']
        
        try:
            # מציאת העמודות של התשואות באופן דינמי
            cols = list(summary_df.columns)
            ret1_idx = cols.index(f"תשואה {asset1_name} (%)") + 1
            ret2_idx = cols.index(f"תשואה {asset2_name} (%)") + 1
            
            c1_let = get_column_letter(ret1_idx)
            c2_let = get_column_letter(ret2_idx)
            form_col_let = get_column_letter(len(cols) + 2)
            num_rows = len(summary_df)
            
            # כתיבת הנוסחה
            worksheet[f"{form_col_let}1"] = "קורלציה (אקסל חי)"
            worksheet[f"{form_col_let}2"] = f"=CORREL({c1_let}2:{c1_let}{num_rows+1}, {c2_let}2:{c2_let}{num_rows+1})"
            
            # עיצוב בסיסי לתא הנוסחה שיהיה בולט
            worksheet[f"{form_col_let}1"].font = Font(bold=True)
            worksheet[f"{form_col_let}2"].fill = PatternFill(start_color="D1FAE5", end_color="D1FAE5", fill_type="solid")
        except ValueError:
            pass # למקרה נדיר שהעמודות משנות שם

    st.download_button(
        label="📥 הורד נתונים (Excel) + בדיקה", 
        data=buffer.getvalue(), 
        file_name=f"correlation_{asset1_name}_{asset2_name}.xlsx", 
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", 
        use_container_width=True
    )
    
    end_ts = int(pd.Timestamp.now().timestamp())
    start_ts = int((pd.Timestamp.now() - pd.Timedelta(days=days_back)).timestamp())
    l1 = f"https://finance.yahoo.com/chart/{ticker1_sym}?period1={start_ts}&period2={end_ts}&interval={interval_choice}"
    l2 = f"https://finance.yahoo.com/chart/{ticker2_sym}?period1={start_ts}&period2={end_ts}&interval={interval_choice}"
    
    st.markdown(f"""
    <div dir='rtl' style='margin-top: 15px;'>
        <a href='{l1}' target='_blank' style='text-decoration:none; color:#1e40af;'>🔗 אימות גרף ב-Yahoo: <span dir='ltr'><b>{asset1_name}</b></span></a><br><br>
        <a href='{l2}' target='_blank' style='text-decoration:none; color:#1e40af;'>🔗 אימות גרף ב-Yahoo: <span dir='ltr'><b>{asset2_name}</b></span></a>
    </div>
    """, unsafe_allow_html=True)

# ==========================================
# שורת תחתונה
# ==========================================
st.divider()
st.markdown(
    """
    <div style='text-align: center; color: #475569; font-size: 1.05rem; direction: rtl; padding: 15px; background-color: rgba(255,255,255,0.8); border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.05);'>
        <strong>האתר לצורכי מחקר, ועל אחריות המשתמש.</strong><br>
        לשיתופי פעולה ניתן לפנות לטלפון: <span dir='ltr' style='font-weight:600;'>054-8810248</span>
    </div>
    """, 
    unsafe_allow_html=True
)
