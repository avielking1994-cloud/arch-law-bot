import streamlit as st
import openai

# הגדרות עיצוב בסיסיות (מתאים לאדריכלות - נקי ולבן)
st.set_page_config(page_title="עוזרת אדריכלית AI", layout="centered")

st.title("🏗️ עוזרת אדריכלית חכמה")
st.subheader("בדיקת תוכניות מול חוקי התכנון והבנייה")

# התחברות לבינה המלאכותית (את המפתח נגדיר בשלב הבא בלוח הבקרה)
if "OPENAI_API_KEY" in st.secrets:
    openai.api_key = st.secrets["OPENAI_API_KEY"]
else:
    st.error("חסר מפתח API. יש להגדיר אותו ב-Secrets של Streamlit.")

# ממשק העלאת קבצים
uploaded_file = st.file_uploader("העלי תוכנית (PDF או תמונה)", type=["pdf", "png", "jpg", "jpeg"])

if uploaded_file:
    st.info("הקובץ נטען בהצלחה. המערכת מוכנה לניתוח.")
    
    # תיבת צ'אט לשאלות
    user_question = st.text_input("מה תרצי שאבדוק בתוכנית?")
    
    if user_question:
        with st.spinner("מנתחת את התוכנית מול ספר החוקים..."):
            # כאן המערכת תשלח את השאלה לבינה המלאכותית
            # בשלב זה אני שם לך תשובה זמנית כדי שתראה שהאתר עובד
            st.success(f"קיבלתי את השאלה: '{user_question}'. בשלב הבא נחבר את מודל ה-Vision שיודע לקרוא את השרטוט עצמו.")

st.markdown("---")
st.caption("פותח עבור אשתי האדריכלית ❤️")
