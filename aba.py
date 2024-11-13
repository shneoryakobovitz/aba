import streamlit as st
import pandas as pd
import json
from io import StringIO


# פונקציה לטעינת קובץ DAT ושמירת התוכן ב-session state לקריאה חוזרת
def load_dat_file():
    if 'uploaded_dat_content' not in st.session_state:
        uploaded_file = st.file_uploader("בחר קובץ להעלאה", type="dat")
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

"""
df = pd.read_csv('10-format.csv', encoding='utf-8-sig')
df.set_index('title', inplace=True)
df = df['len'].to_dict()
print(df)
"""