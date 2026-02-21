import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.express as px

st.set_page_config(page_title="ניתוח קורלציות", layout="wide")

# ==========================================
# מנגנון סיסמה חכם (הסיסמה הוסתרה מהטקסט)
# ==========================================
if st.query_params.get("pwd") == "1234":
    st.session_state.authenticated = True
elif 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.markdown("<h1 style='text-align: center;'>ניתוח קורלציות</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; direction: rtl;'>הזן קוד גישה ולחץ Enter (שמור במועדפים לכניסה אוטומטית בעתיד):</p>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        pwd = st.text_input("סיסמה:", type="password", key="pwd_input", label_visibility="collapsed")
        if pwd == "1234":
            st.session_state.authenticated = True
            st.query_params.pwd = "1234"
            st.rerun()
        elif pwd != "":
            st.error("קוד שגוי")
    st.stop()

# ==========================================
# תפריט צד (Sidebar)
# ==========================================
st.markdown("<h1 style='text-align: right;'>ניתוח קורלציות</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: right; font-size: 13px; color: gray; direction: rtl;'>הערה: כל השעות המוצגות באתר נקבעו לפי שעון ישראל.</p>", unsafe_allow_html=True)

st.sidebar.markdown("<h3 style='text-align: right; direction: rtl;'>הגדרות נכסים</h3>", unsafe_allow_html=True)

default_tickers = {
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

asset1 = st.sidebar.selectbox("נכס 1", list(default_tickers.keys()), index=0)
asset2 = st.sidebar.selectbox("נכס 2", list(default_tickers.keys()), index=6)

st.sidebar.markdown("---")
st.sidebar.markdown("<h3 style='text-align: right; direction: rtl;'>מבנה הניתוח</h3>", unsafe_allow_html=True)

mode = st.sidebar.radio("בחר סוג נתונים לחישוב:", [
    "1. יומי: שער סגירה רשמי",
    "2. יומי: שעה קבועה ביום",
    "3. מהלך מסחר: משעה עד שעה כל יום",
    "4. תוך-יומי: קפיצות זמן מוגדרות"
])

# הגדרות משתנות בהתאם למצב שנבחר
start_hour, end_hour, target_hour = None, None, None
interval_choice, lag_minutes = "5m", 0
max_days = 60 if mode != "1. יומי: שער סגירה רשמי" else 730

if mode == "2. יומי: שעה קבועה ביום":
    target_hour = st.sidebar.selectbox("בחר שעה קבועה:", [f"{h:02d}:00" for h in range(8, 23)], index=8)
    interval_choice = "5m"
elif mode == "3. מהלך מסחר: משעה עד שעה כל יום":
    start_hour, end_hour = st.sidebar.select_slider("חלון זמן יומי", options=[f"{h:02d}:00" for h in range(8, 23)], value=("10:00", "16:00"))
    interval_choice = "5m"
elif mode == "4. תוך-יומי: קפיצות זמן מוגדרות":
    start_hour, end_hour = st.sidebar.select_slider("חלון זמן ביום", options=[f"{h:02d}:00" for h in range(8, 23)], value=("10:00", "16:00"))
    int_options = {"5 דקות": "5m", "15 דקות": "15m", "30 דקות": "30m", "1 שעה": "60m"}
    choice = st.sidebar.selectbox("גודל קפיצת זמן:", list(int_options.keys()))
    interval_choice = int_options[choice]
    lag_minutes = st.sidebar.number_input("השהיה לנכס 2 (בדקות)", min_value=0, max_value=600, value=0, step=5)
elif mode == "1. יומי: שער סגירה רשמי":
    interval_choice = "1d"

days_back = st.sidebar.number_input("ימים אחורה (ברירת מחדל 60)", min_value=1, max_value=max_days, value=60)

# ==========================================
# פונקציית משיכת נתונים
# ==========================================
@st.cache_data(ttl=600)
def get_data(ticker1, ticker2, days, yf_interval):
    t1 = default_tickers[ticker1]
    t2 = default_tickers[ticker2]
    
    df1 = yf.download(t1, period=f"{days}d", interval=yf_interval)['Close']
    df2 = yf.download(t2, period=f"{days}d", interval=yf_interval)['Close']
    
    if isinstance(df1, pd.DataFrame): df1 = df1.iloc[:, 0]
    if isinstance(df2, pd.DataFrame): df2 = df2.iloc[:, 0]
    
    full_df = pd.DataFrame({ticker1: df1, ticker2: df2})
    try:
        # טיפול באזורי זמן גם כשהנתון הוא יומי
        if full_df.index.tz is None:
            full_df.index = full_df.index.tz_localize('UTC').tz_convert('Asia/Jerusalem')
        else:
            full_df.index = full_df.index.tz_convert('Asia/Jerusalem')
    except:
        pass 
    return full_df

# ==========================================
# עיבוד והצגת הנתונים
# ==========================================
with st.spinner('מנתח נתונים, זה עשוי לקחת מספר שניות...'):
    raw_df = get_data(asset1, asset2, days_back, interval_choice)
    scatter_df = pd.DataFrame()
    records = []
    
    if not raw_df.empty:
        # --- מצב 1: יומי שער סגירה ---
        if mode == "1. יומי: שער סגירה רשמי":
            returns_df = raw_df.pct_change().dropna()
            scatter_df = returns_df
            for d, row in raw_df.iterrows():
                if d in returns_df.index:
                    records.append({
                        "תאריך": d.strftime("%d/%m/%Y"),
                        f"שער סגירה {asset1}": round(float(row[asset1]), 2),
                        f"תשואה {asset1} (%)": round(float(returns_df.loc[d, asset1]) * 100, 2),
                        f"שער סגירה {asset2}": round(float(row[asset2]), 2),
                        f"תשואה {asset2} (%)": round(float(returns_df.loc[d, asset2]) * 100, 2),
                    })
                    
        # --- מצב 2: שעה קבועה ---
        elif mode == "2. יומי: שעה קבועה ביום":
            target_time = pd.to_datetime(target_hour).time()
            hour_df = raw_df.at_time(target_time)
            if not hour_df.empty:
                returns_df = hour_df.pct_change().dropna()
                scatter_df = returns_df
                for d, row in hour_df.iterrows():
                    if d in returns_df.index:
                        records.append({
                            "תאריך": d.strftime("%d/%m/%Y"),
                            "שעה נדגמת": d.strftime("%H:%M"),
                            f"שער {asset1}": round(float(row[asset1]), 2),
                            f"תשואה {asset1} (%)": round(float(returns_df.loc[d, asset1]) * 100, 2),
                            f"שער {asset2}": round(float(row[asset2]), 2),
                            f"תשואה {asset2} (%)": round(float(returns_df.loc[d, asset2]) * 100, 2),
                        })
            else:
                st.warning("לא נמצאו מספיק נתונים לשעה הספציפית שנבחרה.")

        # --- מצב 3: מהלך מסחר (משעה עד שעה) ---
        elif mode == "3. מהלך מסחר: משעה עד שעה כל יום":
            filtered_df = raw_df.between_time(start_hour, end_hour)
            dates = np.unique(filtered_df.index.date)
            calc_returns = []
            for d in dates:
                day_data = filtered_df.loc[str(d)]
                if len(day_data) < 2: continue
                
                valid_1 = day_data[asset1].dropna()
                valid_2 = day_data[asset2].dropna()
                
                if len(valid_1) > 0 and len(valid_2) > 0:
                    p1_s, p1_e = valid_1.iloc[0], valid_1.iloc[-1]
                    p2_s, p2_e = valid_2.iloc[0], valid_2.iloc[-1]
                    ret1 = (p1_e - p1_s) / p1_s
                    ret2 = (p2_e - p2_s) / p2_s
                    calc_returns.append({asset1: ret1, asset2: ret2})
                    
                    records.append({
                        "תאריך": d.strftime("%d/%m/%Y"),
                        f"פתיחת חלון {asset1}": round(float(p1_s), 2),
                        f"סיום חלון {asset1}": round(float(p1_e), 2),
                        f"תשואה יומית בחלון {asset1} (%)": round(float(ret1) * 100, 2),
                        f"פתיחת חלון {asset2}": round(float(p2_s), 2),
                        f"סיום חלון {asset2}": round(float(p2_e), 2),
                        f"תשואה יומית בחלון {asset2} (%)": round(float(ret2) * 100, 2),
                    })
            scatter_df = pd.DataFrame(calc_returns)

        # --- מצב 4: אינטרוולים (קפיצות מוגדרות) ---
        elif mode == "4. תוך-יומי: קפיצות זמן מוגדרות":
            filtered_df = raw_df.between_time(start_hour, end_hour)
            if lag_minutes > 0:
                # חישוב כמה "קפיצות" צריך להשהות לפי סוג האינטרוול
                int_mins_map = {"5m": 5, "15m": 15, "30m": 30, "60m": 60}
                lag_steps = lag_minutes // int_mins_map[interval_choice]
                filtered_df[asset2] = filtered_df[asset2].shift(lag_steps)
                
            returns_df = filtered_df.pct_change().dropna()
            scatter_df = returns_df
            for d, row in filtered_df.iterrows():
                if d in returns_df.index:
                    records.append({
                        "תאריך ושעה": d.strftime("%d/%m/%Y %H:%M"),
                        f"שער {asset1}": round(float(row[asset1]), 2),
                        f"תשואה {asset1} (%)": round(float(returns_df.loc[d, asset1]) * 100, 2),
                        f"שער {asset2}": round(float(row[asset2]), 2),
                        f"תשואה {asset2} (%)": round(float(returns_df.loc[d, asset2]) * 100, 2),
                    })

        # ==========================================
        # אזור התצוגה המרכזי
        # ==========================================
        summary_df = pd.DataFrame(records)
        
        if not scatter_df.empty:
            corr_value = scatter_df[asset1].corr(scatter_df[asset2])
            num_obs = len(scatter_df)
            
            col1, col2, col3 = st.columns(3)
            col1.metric(label="קורלציה סופית", value=f"{corr_value:.2f}")
            col2.metric(label="מספר תצפיות בחישוב", value=num_obs)
            col3.metric(label="השהיה שהופעלה", value=f"{lag_minutes} דקות" if lag_minutes > 0 else "ללא")
            
            st.divider()
            
            c1, c2 = st.columns([1, 1])
            with c1:
                st.markdown("<h4 style='text-align: right; direction: rtl;'>פיזור נתונים</h4>", unsafe_allow_html=True)
                fig_scatter = px.scatter(scatter_df, x=asset1, y=asset2, trendline="ols" if num_obs > 2 else None)
                st.plotly_chart(fig_scatter, use_container_width=True)
                
            with c2:
                st.markdown("<h4 style='text-align: right; direction: rtl;'>טבלת נתונים לבדיקה באקסל</h4>", unsafe_allow_html=True)
                st.dataframe(summary_df, use_container_width=True)
                csv = summary_df.to_csv(index=False, encoding='utf-8-sig')
                st.download_button(
                    label="📥 הורד נתונים לאקסל (CSV)",
                    data=csv,
                    file_name=f"correlation_{asset1}_{asset2}.csv",
                    mime="text/csv",
                    use_container_width=True
                )
        else:
            st.error("לא נמצאו מספיק נתונים לחישוב קורלציה בחלון הנבחר.")

    # --- קישורים דינמיים לפי בחירת התקופה ---
    st.divider()
    t1_sym = default_tickers[asset1]
    t2_sym = default_tickers[asset2]
    end_ts = int(pd.Timestamp.now().timestamp())
    start_ts = int((pd.Timestamp.now() - pd.Timedelta(days=days_back)).timestamp())

    link_t1 = f"https://finance.yahoo.com/chart/{t1_sym}?period1={start_ts}&period2={end_ts}&interval={interval_choice}"
    link_t2 = f"https://finance.yahoo.com/chart/{t2_sym}?period1={start_ts}&period2={end_ts}&interval={interval_choice}"

    st.markdown("<h4 style='text-align: right; direction: rtl;'>🔗 קישורים דינמיים לאימות הנתונים:</h4>", unsafe_allow_html=True)
    st.markdown(f"""
    <div dir='rtl' style='text-align: right;'>
    <ul>
        <li><a href='{link_t1}' target='_blank'>גרף ביאהו פיננס: <b>{asset1}</b></a></li>
        <li><a href='{link_t2}' target='_blank'>גרף ביאהו פיננס: <b>{asset2}</b></a></li>
    </ul>
    </div>
    """, unsafe_allow_html=True)
