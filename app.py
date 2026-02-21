import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

# הגדרות תצוגה
st.set_page_config(page_title="Intraday Correlation Pro", layout="wide")

st.title("🔍 ניתוח קורלציות תוך-יומי לפי שעות")
st.write("ניתוח קשרים בין נכסים בחלונות זמן ספציפיים")

# --- תפריט צד ---
st.sidebar.header("הגדרות חיפוש")

# רשימת נכסים - שים לב לתיקון בנאסד"ק (עטוף בגרש בודד)
default_tickers = {
    "לאומי": "LUMI.TA",
    "פועלים": "POLI.TA",
    "דיסקונט": "DSCT.TA",
    "S&P 500 Futures": "ES=F",
    'נאסד"ק 100': "NQ=F", 
    "USD/ILS": "ILS=X",
    "XLF (פיננסים ארה\"ב)": "XLF"
}

selected_names = st.sidebar.multiselect("בחר נכסים לניתוח", list(default_tickers.keys()), default=["לאומי", "S&P 500 Futures", "USD/ILS"])

start_hour, end_hour = st.sidebar.select_slider(
    "בחר חלון זמן ביום (שעון ישראל)",
    options=[f"{h:02d}:00" for h in range(8, 23)],
    value=("10:00", "16:00")
)

days_back = st.sidebar.number_input("ימים אחורה (מקסימום 60)", min_value=1, max_value=60, value=30)

@st.cache_data(ttl=600)
def get_intraday_data(names, days):
    data_list = []
    for name in names:
        ticker = default_tickers[name]
        # משיכת נתונים
        df = yf.download(ticker, period=f"{days}d", interval="5m")['Close']
        df.name = name
        data_list.append(df)
    
    if not data_list:
        return pd.DataFrame()
        
    full_df = pd.concat(data_list, axis=1)
    # המרה לשעון ישראל
    try:
        full_df.index = full_df.index.tz_convert('Asia/Jerusalem')
    except:
        pass 
    return full_df

if selected_names:
    with st.spinner('מנתח נתונים...'):
        raw_df = get_intraday_data(selected_names, days_back)
        
        if not raw_df.empty:
            # סינון שעות
            filtered_df = raw_df.between_time(start_hour, end_hour)
            
            if filtered_df.empty:
                st.error("לא נמצאו נתונים בחלון הזמן שנבחר.")
            else:
                returns_df = filtered_df.pct_change().dropna()

                col1, col2 = st.columns([1, 1])
                with col1:
                    st.subheader(f"📊 קורלציה בין {start_hour} ל-{end_hour}")
                    corr = returns_df.corr()
                    fig_corr = px.imshow(corr, text_auto='.2f', color_continuous_scale='RdBu_r')
                    st.plotly_chart(fig_corr, use_container_width=True)

                with col2:
                    st.subheader("📈 תנועה יחסית")
                    norm_df = (filtered_df / filtered_df.iloc[0]) * 100
                    fig_line = px.line(norm_df)
                    st.plotly_chart(fig_line, use_container_width=True)
else:
    st.warning("בחר לפחות מניה אחת בתפריט הצד")
