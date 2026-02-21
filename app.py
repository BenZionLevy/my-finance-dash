import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.express as px

# הגדרות תצוגה
st.set_page_config(page_title="ניתוח קורלציות", layout="wide")

# ==========================================
# 1. מנגנון סיסמה קלילה (1234)
# ==========================================
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.markdown("<h1 style='text-align: center;'>ניתוח קורלציות</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; direction: rtl;'>הזן קוד גישה כדי לצפות במערכת:</p>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        pwd = st.text_input("סיסמה:", type="password", key="pwd_input", label_visibility="collapsed")
        if pwd == "1234":
            st.session_state.authenticated = True
            st.rerun()
        elif pwd != "":
            st.error("קוד שגוי")
    st.stop() # עוצר את טעינת שאר האתר אם אין סיסמה

# ==========================================
# 2. האתר המרכזי (מוצג רק לאחר סיסמה)
# ==========================================
st.markdown("<h1 style='text-align: right;'>ניתוח קורלציות</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: right; font-size: 13px; color: gray; direction: rtl;'>הערה: כל השעות המוצגות באתר נקבעו לפי שעון ישראל.</p>", unsafe_allow_html=True)

# --- תפריט צד ---
st.sidebar.markdown("<div dir='rtl'><b>בחר נכסים, חלון זמן ביום, וקבל את הקורלציה כולל פירוט יומי להורדה.</b></div>", unsafe_allow_html=True)
st.sidebar.markdown("---")
st.sidebar.markdown("<h3 style='text-align: right; direction: rtl;'>הגדרות חיפוש</h3>", unsafe_allow_html=True)

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

start_hour, end_hour = st.sidebar.select_slider(
    "חלון זמן ביום",
    options=[f"{h:02d}:00" for h in range(8, 23)],
    value=("10:00", "16:00")
)

days_back = st.sidebar.number_input("ימים אחורה (עד 60)", min_value=1, max_value=60, value=14)

st.sidebar.markdown("---")
st.sidebar.markdown("<h4 style='text-align: right; direction: rtl;'>הגדרות מתקדמות</h4>", unsafe_allow_html=True)
lag_minutes = st.sidebar.number_input("השהיה לנכס 2 (בדקות)", min_value=0, max_value=600, value=0, step=5)

# --- פונקציית משיכת נתונים ---
@st.cache_data(ttl=600)
def get_data(ticker1, ticker2, days):
    t1 = default_tickers[ticker1]
    t2 = default_tickers[ticker2]
    
    df1 = yf.download(t1, period=f"{days}d", interval="5m")['Close']
    df2 = yf.download(t2, period=f"{days}d", interval="5m")['Close']
    
    if isinstance(df1, pd.DataFrame): df1 = df1.iloc[:, 0]
    if isinstance(df2, pd.DataFrame): df2 = df2.iloc[:, 0]
    
    full_df = pd.DataFrame({ticker1: df1, ticker2: df2})
    
    try:
        full_df.index = full_df.index.tz_convert('Asia/Jerusalem')
    except:
        pass 
        
    return full_df

with st.spinner('מנתח נתונים, זה עשוי לקחת מספר שניות...'):
    raw_df = get_data(asset1, asset2, days_back)
    
    if not raw_df.empty:
        filtered_df = raw_df.between_time(start_hour, end_hour)
        
        if filtered_df.empty:
            st.error("לא נמצאו נתונים בחלון הזמן שנבחר.")
        else:
            # --- חישובים ובניית הטבלה ---
            records = []
            dates = np.unique(filtered_df.index.date)
            for d in dates:
                day_data = filtered_df.loc[str(d)]
                if len(day_data) < 2: continue
                
                valid_1 = day_data[asset1].dropna()
                valid_2 = day_data[asset2].dropna()
                
                if len(valid_1) > 0 and len(valid_2) > 0:
                    s_t1, e_t1 = valid_1.index[0], valid_1.index[-1]
                    p1_s, p1_e = valid_1.iloc[0], valid_1.iloc[-1]
                    ret1 = (p1_e - p1_s) / p1_s
                    
                    s_t2, e_t2 = valid_2.index[0], valid_2.index[-1]
                    p2_s, p2_e = valid_2.iloc[0], valid_2.iloc[-1]
                    ret2 = (p2_e - p2_s) / p2_s
                    
                    records.append({
                        "תאריך": d.strftime("%d/%m/%Y"),
                        f"שעת התחלה {asset1}": s_t1.strftime("%H:%M"),
                        f"שער התחלה {asset1}": round(float(p1_s), 2),
                        f"שעת סיום {asset1}": e_t1.strftime("%H:%M"),
                        f"שער סיום {asset1}": round(float(p1_e), 2),
                        f"תשואה {asset1} (%)": round(float(ret1) * 100, 2),
                        f"שעת התחלה {asset2}": s_t2.strftime("%H:%M"),
                        f"שער התחלה {asset2}": round(float(p2_s), 2),
                        f"שעת סיום {asset2}": e_t2.strftime("%H:%M"),
                        f"שער סיום {asset2}": round(float(p2_e), 2),
                        f"תשואה {asset2} (%)": round(float(ret2) * 100, 2),
                    })
            
            summary_df = pd.DataFrame(records)

            returns_df = filtered_df.pct_change().dropna()
            
            if lag_minutes > 0:
                lag_steps = lag_minutes // 5
                returns_df[asset2] = returns_df[asset2].shift(lag_steps)
                returns_df = returns_df.dropna()
                
            corr_value = returns_df[asset1].corr(returns_df[asset2])
            num_obs = len(returns_df)
            
            # --- תצוגה ---
            col1, col2, col3 = st.columns(3)
            col1.metric(label="קורלציה סופית", value=f"{corr_value:.2f}")
            col2.metric(label="מספר תצפיות (בדיקות)", value=num_obs)
            col3.metric(label="השהיה שהופעלה", value=f"{lag_minutes} דקות")
            
            st.divider()
            
            c1, c2 = st.columns([1, 1])
            with c1:
                st.markdown("<h4 style='text-align: right; direction: rtl;'>פיזור נתונים</h4>", unsafe_allow_html=True)
                fig_scatter = px.scatter(returns_df, x=asset1, y=asset2)
                st.plotly_chart(fig_scatter, use_container_width=True)
                
            with c2:
                st.markdown("<h4 style='text-align: right; direction: rtl;'>תנועת מחירים מנורמלת</h4>", unsafe_allow_html=True)
                norm_df = (filtered_df.dropna() / filtered_df.dropna().iloc[0]) * 100
                fig_line = px.line(norm_df)
                st.plotly_chart(fig_line, use_container_width=True)

            st.divider()

            st.markdown("<h4 style='text-align: right; direction: rtl;'>טבלת סיכום יומית</h4>", unsafe_allow_html=True)
            st.dataframe(summary_df, use_container_width=True)
            
            csv = summary_df.to_csv(index=False, encoding='utf-8-sig')
            st.download_button(
                label="📥 הורד נתונים לאקסל (CSV)",
                data=csv,
                file_name=f"correlation_{asset1}_{asset2}.csv",
                mime="text/csv",
            )

    # --- 3. אזור קישורים שימושיים בתחתית הדף ---
    st.divider()
    st.markdown("<h4 style='text-align: right; direction: rtl;'>🔗 קישורים שימושיים לבדיקת נתונים:</h4>", unsafe_allow_html=True)
    st.markdown("""
    <div dir='rtl' style='text-align: right;'>
    <ul>
        <li><a href='https://finance.yahoo.com/' target='_blank'>Yahoo Finance (נוח לבדיקת שער הדולר וחוזים עתידיים)</a></li>
        <li><a href='https://il.investing.com/' target='_blank'>Investing.com ישראל (מצוין לבדיקת מניות ומדדים מקומיים)</a></li>
        <li><a href='https://www.bizportal.co.il/' target='_blank'>Bizportal (לנתוני זמן אמת של בורסת תל אביב)</a></li>
    </ul>
    </div>
    """, unsafe_allow_html=True)
