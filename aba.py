import streamlit as st
import pandas as pd
import json
from io import StringIO


# פונקציה לטעינת קובץ DAT ושמירת התוכן ב-session state לקריאה חוזרת
def load_dat_file():
    if 'uploaded_dat_content' not in st.session_state:
        uploaded_file = st.file_uploader("בחר קובץ להעלאה", type=["dat", "txt"])
        if uploaded_file:
            # שמירה של תוכן הקובץ כ-StringIO כך שנוכל להשתמש בו מחדש
            dat_content = StringIO(uploaded_file.getvalue().decode('ISO-8859-8'))
            st.session_state['uploaded_dat_content'] = dat_content
    return st.session_state.get('uploaded_dat_content', None)

def json_file():
    # קריאת קובץ JSON ופרשנות הנתונים למילון פייתון
    with open('aba.json', 'r', encoding='utf-8-sig') as file:
        data = json.load(file)
        return data

def main():
    # טוען קובץ JSON ושומר אותו ב-session state
    data = json_file()
    st.markdown("""
                <link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+Hebrew:wdth,wght@95,100..900&display=swap" rel="stylesheet">
    <style>
    /* הגדרת הרקע */
    /* יישור כותרות וטקסט */
    .stMarkdown, .stTitle, .stHeader, .stText, .stSubtitle {
        text-align: right;
    }
    /* כיוון הרכיבים בתפריט הצד */
    .css-1d391kg, .css-1cpxqw2, .css-1lcbmhc {
        direction: rtl;
    }
    .stDataFrame table {
        direction: rtl;
    }
    .stTable, .stDataFrame {
        direction: rtl;
                font-family: 'Tahoma', sans-serif;
    }
    .stDataFrame table tbody tr td {
        text-align: right;
                font-family: 'Tahoma', sans-serif;
    }
    .stDataFrame table thead tr th {
                font-family: 'Tahoma', sans-serif;
        text-align: right;
    }
    .stApp {
                direction: rtl;
        text-align: right;
        background-image: url("https://img.freepik.com/free-photo/white-wall-background-with-scratches_1154-667.jpg?t=st=1731527165~exp=1731530765~hmac=624e045cc2bbdcb70ce903c6f85899d3246d137f55ac01a2f002b362144deeae&w=996"); /* הכנס כאן את הקישור לתמונת ה-GIF */
        background-size: cover;
        background-position: center;
        background-repeat: no-repeat;
        background-attachment: fixed;
    }
    .big-font {
        font-size:50px !important;
        font-family: "Noto Sans Hebrew", serif;
        
    }
    .custom-header {
        padding: 10px;
        text-align: center;
    }
    .stFileUploader > label {
        font-size: 18px;
        color: #4CAF50;
        font-weight: bold;
        font-family: "Noto Sans Hebrew", serif;
        text-align: center;
    }
    .stFileUploader input[type="dat"] {
        background-color: #4CAF50;
        font-family: 'Tahoma', sans-serif;
        color: white;
        padding: 10px 20px;
        border: none;
        border-radius: 5px;
        cursor: pointer;
    }
    .stFileUploader input[type="dat"]:hover {
        background-color: #45a049;
    }    /* טקסט רגיל (פסקאות) */
    .stText, .stMarkdown p {
        font-family: 'Tahoma', sans-serif;
        font-size: 16px;
        color: #333333;
        line-height: 1.6;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown('<div class="custom-header"><h1 class="big-font">ניתוח קבצים</h1></div>', unsafe_allow_html=True)
    # רשימת אפשרויות מתוך הקובץ
    options = list(data.keys())    
    # טוען את תוכן קובץ DAT ב-session state כ-StringIO
    dat_content = load_dat_file()
        
        # מציג את הטבלאות אם הנתונים קיימים
    if dat_content is not None:
        for option in options:
            # איפוס `dat_content` כך שיהיה מוכן לקריאה חדשה עבור כלa אפשרות
            dat_content.seek(0)
            # יצירת DataFrame לפי המידע מ-JSON עבור כל אפשרות
            current_info = pd.DataFrame(list(data[option].items()), columns=["שם עמודה", "מספר תווים"])
            df = pd.read_fwf(dat_content, widths=current_info['מספר תווים'], names=current_info['שם עמודה'], dtype=str)
            df = df[df['סוג רשומה'] == option]
            # הצגת הטבלה עבור האפשרות הנוכחית
            st.write(f"טבלה עבור {option}:")
            st.dataframe(df.fillna(''), selection_mode="multi-row")  # הצגת ה-DataFrame עם השלמת ערכים ריקים

main()
