import streamlit as st
import google.generativeai as genai

st.set_page_config(page_title="עוזרת אדריכלית AI", layout="wide")

st.title("🏗️ הצ'אט האדריכלי")
st.subheader("העלי תוכנית בצד, וכתבי לי למטה מה לבדוק")

# התחברות בטוחה לג'מיני דרך ה-Secrets
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.error("חסר מפתח API של גוגל ב-Secrets. אנא בדוק את הגדרות האתר.")
    st.stop()

# שימוש במודל יציב
model = genai.GenerativeModel('gemini-1.5-flash')

# יצירת זיכרון לשיחה
if "messages" not in st.session_state:
    st.session_state.messages = []

# סרגל צד להעלאת קבצים
with st.sidebar:
    st.header("📂 קבצי הפרויקט")
    uploaded_file = st.file_uploader("העלי תוכנית (תמונה או PDF)", type=["pdf", "png", "jpg", "jpeg"])
    
    if uploaded_file:
        st.success("הקובץ נטען ומוכן לעבודה!")
        st.session_state.file_data = uploaded_file.getvalue()
        st.session_state.file_type = uploaded_file.type

# הצגת היסטוריית השיחה
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# שורת הכתיבה למשתמשת
if prompt := st.chat_input("כתבי כאן הוראות, שאלות, או מה תרצי שאבדוק..."):
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    # הרכבת הבקשה לג'מיני
    contents = ["את עוזרת אדריכלית מומחית. תמיד תעני במקצועיות, באופן ברור, ובהתאם לחוקי התכנון והבנייה בישראל."]
    
    for msg in st.session_state.messages:
        contents.append(f"{msg['role']}: {msg['content']}")
        
    if "file_data" in st.session_state:
        contents.append({"mime_type": st.session_state.file_type, "data": st.session_state.file_data})

    # פנייה למודל וקבלת תשובה
    with st.chat_message("assistant"):
        with st.spinner("מנתח את הנתונים..."):
            try:
                response = model.generate_content(contents)
                st.markdown(response.text)
                st.session_state.messages.append({"role": "assistant", "content": response.text})
            except Exception as e:
                st.error(f"קרתה תקלה מול השרת של גוגל: {e}")
