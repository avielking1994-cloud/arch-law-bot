import streamlit as st
import google.generativeai as genai

st.set_page_config(page_title="עוזרת אדריכלית AI", layout="centered")

st.title("🏗️ עוזרת אדריכלית חכמה (Gemini)")
st.subheader("בדיקת תוכניות מול חוקי התכנון והבנייה")

# התחברות לג'מיני - כאן המערכת קוראת את המפתח מתוך ה-Secrets
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.error("חסר מפתח API של גוגל ב-Secrets.")
    st.stop()

model = genai.GenerativeModel('gemini-1.5-pro')

uploaded_file = st.file_uploader("העלי תוכנית (תמונה או PDF)", type=["pdf", "png", "jpg", "jpeg"])

if uploaded_file:
    st.info("הקובץ נטען. המערכת מוכנה לניתוח.")
    
    user_question = st.text_input("מה תרצי שאבדוק בתוכנית?")
    
    if st.button("נתח תוכנית") and user_question:
        with st.spinner("ג'מיני מנתח את התוכנית..."):
            img_data = uploaded_file.read()
            contents = [
                "את עוזרת אדריכלית מומחית. נתחי את התוכנית המצורפת ועני על השאלה בהתאם לחוקי התכנון והבנייה בישראל.",
                user_question,
                {"mime_type": uploaded_file.type, "data": img_data}
            ]
            
            try:
                response = model.generate_content(contents)
                st.markdown("### תוצאות הבדיקה:")
                st.write(response.text)
            except Exception as e:
                st.error(f"שגיאה בניתוח: {e}")

st.markdown("---")
st.caption("פותח עבור אשתי האדריכלית ❤️")
