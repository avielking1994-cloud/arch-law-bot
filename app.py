import streamlit as st
import google.generativeai as genai

st.set_page_config(page_title="עוזרת אדריכלית AI", layout="wide")

st.title("🏗️ הצ'אט האדריכלי")

# התחברות
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.error("חסר מפתח API של גוגל ב-Secrets.")
    st.stop()

# 1. משיכת רשימת המודלים שזמינים למפתח שלך
try:
    available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
    
    if not available_models:
        st.error("המפתח תקין, אבל גוגל לא נותנת לו גישה לאף מודל. ייתכן ויש בעיה בחשבון ה-Google AI Studio שלך.")
        st.stop()
        
    # 2. בחירה אוטומטית של המודל הראשון שזמין (מסירים את המילה 'models/' כדי למנוע שגיאות)
    best_model = available_models[0].replace('models/', '')
    
    # הצגת הודעה קטנה למעלה כדי שתדע איזה מודל נבחר
    st.success(f"מחובר בהצלחה למודל: {best_model}")
    
    # 3. הגדרת המודל
    model = genai.GenerativeModel(best_model)

except Exception as e:
    st.error(f"שגיאה בטעינת המודלים: {e}")
    st.stop()

# סרגל צד להעלאת תוכנית
with st.sidebar:
    st.header("📂 קבצי הפרויקט")
    uploaded_file = st.file_uploader("העלי תוכנית (תמונה או PDF)", type=["pdf", "png", "jpg", "jpeg"])
    
    if uploaded_file:
        st.success("הקובץ נטען ומוכן לעבודה!")
        st.session_state.file_data = uploaded_file.getvalue()
        st.session_state.file_type = uploaded_file.type

# זיכרון שיחה
if "messages" not in st.session_state:
    st.session_state.messages = []

# הצגת השיחה
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# שורת ההקלטה
if prompt := st.chat_input("כתבי כאן הוראות, שאלות, או מה תרצי שאבדוק..."):
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    # בניית הבקשה
    contents = []
    
    if "file_data" in st.session_state:
        contents.append({"mime_type": st.session_state.file_type, "data": st.session_state.file_data})
        
    prompt_text = f"הנחיית מערכת: את עוזרת אדריכלית מומחית. תמיד תעני במקצועיות ובהתאם לחוקי התכנון והבנייה בישראל.\n\nשאלת המשתמש: {prompt}"
    contents.append(prompt_text)

    # פנייה למודל
    with st.chat_message("assistant"):
        with st.spinner("מנתח את התוכנית..."):
            try:
                response = model.generate_content(contents)
                st.markdown(response.text)
                st.session_state.messages.append({"role": "assistant", "content": response.text})
            except Exception as e:
                st.error(f"שגיאה בניתוח התוכן: {e}")
