import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.express as px

# הגדרות תצוגה
st.set_page_config(page_title="Intraday Correlation Pro", layout="wide")

st.title("🔍 ניתוח קורלציות (כולל השהיה וטבלת אקסל)")
st.write("בחר נכסים, חלון זמן ביום, וקבל את הקורלציה כולל פירוט יומי להורדה.")

# --- תפריט צד ---
st.sidebar.header("הגדרות חיפוש")

default_tickers = {
    "לאומי": "LUMI.TA",
    "פועלים": "POLI.TA",
    "דיסקונט": "DSCT.TA",
    "S&P 500 Futures": "ES=F",
    'נאסד"ק 100': "NQ=F", 
    "USD/ILS": "ILS=X",
    "XLF (פיננסים ארה\"ב)": "XLF"
}

asset1 = st.sidebar.selectbox("נכס 1 (לדוגמה: מניה מקומית)", list(default_tickers.keys()), index=0)
asset2 = st.sidebar.selectbox("נכס 2 (להשוואה, לדוגמה: מדד/דולר)", list(default_tickers.keys()), index=3)

start_hour, end_hour = st.sidebar.select_slider(
    "חלון זמן ביום (שעון ישראל)",
    options=[f"{h:02d}:00" for h in range(8, 23)],
    value=("10:00", "16:00")
)

days_back = st.sidebar.number_input("ימים אחורה (עד 60)", min_value=1, max_value=60, value=14)

st.sidebar.markdown("---")
st.sidebar.subheader("הגדרות מתקדמות")
lag_minutes = st.sidebar.number_input("השהיה לנכס 2 (בדקות)", min_value=0, max_value=600, value=0, step=5, help="לדוגמה: 60 = נכס 2 נמצא בהשהיה של שעה אחורה.")

@st.cache_data(ttl=600)
def get_data(ticker1, ticker2, days):
    t1 = default_tickers[ticker1]
    t2 = default_tickers[ticker2]
    
    # משיכת נתונים מיאהו
    df1 = yf.download(t1, period=f"{days}d", interval="5m")['Close']
    df2 = yf.download(t2, period=f"{days}d", interval="5m")['Close']
    
    # הבטחה שהנתונים יתנהגו כעמודה בודדת ולא כטבלה מורכבת
    if isinstance(df1, pd.DataFrame): 
        df1 = df1.iloc[:, 0]
    if isinstance(df2, pd.DataFrame): 
        df2 = df2.iloc[:, 0]
    
    # חיבור העמודות לטבלה אחת עם השמות הנכונים שבחרת
    full_df = pd.DataFrame({ticker1: df1, ticker2: df2})
    
    # המרת אזור זמן לישראל
    try:
        full_df.index = full_df.index.tz_convert('Asia/Jerusalem')
    except:
        pass 
        
    return full_df

with st.spinner('מנתח נתונים, זה ייקח כמה שניות...'):
    raw_df = get_data(asset1, asset2, days_back)
    
    if not raw_df.empty:
        # סינון חלון הזמן הרלוונטי
        filtered_df = raw_df.between_time(start_hour, end_hour)
        
        if filtered_df.empty:
            st.error("לא נמצאו נתונים בחלון הזמן שנבחר.")
        else:
            # --- 1. בניית טבלת סיכום יומית ---
            records = []
            dates = np.unique(filtered_df.index.date)
            for d in dates:
                day_data = filtered_df.loc[str(d)]
                if len(day_data) < 2: continue
                
                valid_1 = day_data[asset1].dropna()
                valid_2 = day_data[asset2].dropna()
                
                if len(valid_1) > 0 and len(valid_2) > 0:
                    # נתוני נכס 1
                    s_t1, e_t1 = valid_1.index[0], valid_1.index[-1]
                    p1_s, p1_e = valid_1.iloc[0], valid_1.iloc[-1]
                    ret1 = (p1_e - p1_s) / p1_s
                    
                    # נתוני נכס 2
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

            # --- 2. חישוב קורלציה + השהיה ---
            returns_df = filtered_df.pct_change().dropna()
            
            if lag_minutes > 0:
                lag_steps = lag_minutes // 5 # כל קפיצה היא 5 דקות
                returns_df[asset2] = returns_df[asset2].shift(lag_steps)
                returns_df = returns_df.dropna()
                
            corr_value = returns_df[asset1].corr(returns_df[asset2])
            num_obs = len(returns_df)
            
            # --- תצוגה עליונה ---
            col1, col2, col3 = st.columns(3)
            col1.metric(label=f"קורלציה סופית ({asset1} מול {asset2})", value=f"{corr_value:.2f}")
            col2.metric(label="מספר תצפיות (בדיקות) שחושבו", value=num_obs)
            col3.metric(label="השהיה שהופעלה לנכס 2", value=f"{lag_minutes} דקות")
            
            st.divider()
            
            # --- גרפים ---
            c1, c2 = st.columns([1, 1])
            with c1:
                st.subheader("פיזור נתונים")
                fig_scatter = px.scatter(returns_df, x=asset1, y=asset2, labels={asset1: f"תשואת {asset1}", asset2: f"תשואת {asset2} (בהשהיה)"})
                st.plotly_chart(fig_scatter, use_container_width=True)
                
            with c2:
                st.subheader("תנועת מחירים מנורמלת")
                norm_df = (filtered_df.dropna() / filtered_df.dropna().iloc[0]) * 100
                fig_line = px.line(norm_df)
                st.plotly_chart(fig_line, use_container_width=True)

            st.divider()

            # --- הצגת טבלה והורדה ---
            st.subheader("📅 טבלת סיכום יומית (שערים ותשואות)")
            st.dataframe(summary_df, use_container_width=True)
            
            # יצירת קובץ CSV תקין בעברית לאקסל
            csv = summary_df.to_csv(index=False, encoding='utf-8-sig')
            st.download_button(
                label="📥 הורד נתונים לאקסל (CSV)",
                data=csv,
                file_name=f"correlation_data_{asset1}_{asset2}.csv",
                mime="text/csv",
            )
