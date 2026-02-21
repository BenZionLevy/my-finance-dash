import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

st.set_page_config(page_title="Intraday Correlation Pro", layout="wide")

st.title("🔍 ניתוח קורלציות תוך-יומי לפי שעות")
st.write("בחר טווח שעות ומניות כדי לראות איך הקשר משתנה בזמנים ספציפיים ביום")

# --- תפריט צד להגדרות ---
st.sidebar.header("הגדרות חיפוש")

# 1. בחירת מניות (רשימה דינמית)
default_tickers = {
    "לאומי": "LUMI.TA",
    "פועלים": "POLI.TA",
    "דיסקונט": "DSCT.TA",
    "S&P 500 Futures": "ES=F",
    "נאסד"ק 100": "NQ=F",
    "USD/ILS": "ILS=X",
    "XLF (פיננסים ארה\"ב)": "XLF"
}
selected_names = st.sidebar.multiselect("בחר נכסים לניתוח", list(default_tickers.keys()), default=["לאומי", "S&P 500 Futures", "USD/ILS"])

# 2. בחירת שעות (סליידר)
start_hour, end_hour = st.sidebar.select_slider(
    "בחר חלון זמן ביום (שעון ישראל)",
    options=[f"{h:02d}:00" for h in range(8, 23)],
    value=("10:00", "16:00")
)

# 3. בחירת טווח ימים (מוגבל ל-60 יום עבור נתונים תוך-יומיים חינמיים)
days_back = st.sidebar.number_input("ימים אחורה (מקסימום 60 לנתוני דקות)", min_value=1, max_value=60, value=30)

@st.cache_data(ttl=600)
def get_intraday_data(names, days):
    data_list = []
    for name in names:
        ticker = default_tickers[name]
        # משיכת נתונים באינטרוול של 5 דקות
        df = yf.download(ticker, period=f"{days}d", interval="5m")['Close']
        df.name = name
        data_list.append(df)
    
    full_df = pd.concat(data_list, axis=1)
    full_df.index = full_df.index.tz_convert('Asia/Jerusalem') # המרה לשעון ישראל
    return full_df

if selected_names:
    with st.spinner('מנתח נתונים...'):
        raw_df = get_intraday_data(selected_names, days_back)
        
        # --- סינון לפי שעות ---
        # הופכים את המחרוזות של השעות לאובייקטי זמן
        filtered_df = raw_df.between_time(start_hour, end_hour)
        
        if filtered_df.empty:
            st.error("לא נמצאו נתונים בחלון הזמן שנבחר. נסה להרחיב את השעות.")
        else:
            # חישוב תשואות בתוך החלון הנבחר
            returns_df = filtered_df.pct_change().dropna()

            # --- תצוגה ---
            col1, col2 = st.columns([1, 1])

            with col1:
                st.subheader(f"📊 קורלציה בין {start_hour} ל-{end_hour}")
                corr = returns_df.corr()
                fig_corr = px.imshow(corr, text_auto='.2f', color_continuous_scale='RdBu_r')
                st.plotly_chart(fig_corr, use_container_width=True)

            with col2:
                st.subheader("📈 תנועה יחסית בחלון הזמן")
                # נרמול הנתונים לתחילת כל יום מסחר בגרף
                norm_df = (filtered_df / filtered_df.iloc[0]) * 100
                fig_line = px.line(norm_df)
                st.plotly_chart(fig_line, use_container_width=True)
            
            # הצגת הנתונים הגולמיים
            if st.checkbox("הצג טבלת נתונים גולמיים"):
                st.write(filtered_df.tail(100))
else:
    st.warning("בחר לפחות מניה אחת בתפריט הצד")
