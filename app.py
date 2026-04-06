import streamlit as st
import google.generativeai as genai
import os

st.set_page_config(page_title="עוזרת אדריכלית AI", layout="wide")
st.title("🏗️ הצ'אט האדריכלי - מומחה רישוי")

if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.error("חסר מפתח API ב-Secrets.")
    st.stop()

# ניסיון לאתר את המודל הטוב ביותר הפתוח למפתח שלך
try:
    available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
    if not available_models:
        st.error("אין גישה למודלים. בדוק את מפתח ה-API.")
        st.stop()
    best_model = available_models[0].replace('models/', '')
    model = genai.GenerativeModel(best_model)
except Exception as e:
    st.error(f"שגיאת התחברות: {e}")
    st.stop()

# --- טעינת החוקים מקובץ הטקסט ---
law_text = ""
law_file_path = "rules.txt" # זה השם של הקובץ שיצרנו בצעד 1

if os.path.exists(law_file_path):
    with open(law_file_path, "r", encoding="utf-8") as f:
        law_text = f.read()
# --------------------------------

with st.sidebar:
    st.header("📂 קבצי הפרויקט")
    uploaded_file = st.file_uploader("העלי תוכנית לניתוח", type=["pdf", "png", "jpg", "jpeg"])
    
    if uploaded_file:
        st.success("התוכנית נטענה!")
        st.session_state.file_data = uploaded_file.getvalue()
        st.session_state.file_type = uploaded_file.type

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("מה תרצי שאבדוק בתוכנית לפי החוק?"):
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    contents = []
    
    # חיבור החוקים לשאלה
    if law_text:
        instructions = f"את עוזרת אדריכלית מומחית. להלן חוקי התכנון והבנייה הרלוונטיים:\n\n{law_text}\n\nנתחי את התוכנית ועני על השאלה אך ורק על פי הכללים המופיעים בחוקים אלו."
    else:
         instructions = "את עוזרת אדריכלית מומחית. עני לפי חוקי התכנון והבניה."
    
    contents.append(instructions)

    if "file_data" in st.session_state:
        contents.append({"mime_type": st.session_state.file_type, "data": st.session_state.file_data})
        
    contents.append(f"השאלה: {prompt}")

    with st.chat_message("assistant"):
        with st.spinner("בודק את התוכנית מול החוקים..."):
            try:
                response = model.generate_content(contents)
                st.markdown(response.text)
                st.session_state.messages.append({"role": "assistant", "content": response.text})
            except Exception as e:
                st.error(f"שגיאה בניתוח: {e}")
