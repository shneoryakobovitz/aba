import streamlit as st
import pandas as pd
from io import StringIO
from st_aggrid import AgGrid, GridOptionsBuilder
from st_aggrid.shared import GridUpdateMode
import json



def main():
        # הוספת CSS מותאם אישית
    st.markdown("""
        <style>
        body {
            direction: rtl;
            text-align: right;
        }
        </style>
    """, unsafe_allow_html=True)

    st.title("העלאה, הצגה והורדה של קובץ CSV")
        # שלב 1: העלאת קובץ
    uploaded_file_json = st.file_uploader("בחר קובץ לדינמיות", type="json")
    if uploaded_file_json:
        data = json.load(uploaded_file_json)
    
        options = data.keys()
        # יצירת תיבת בחירה
        selected_option = st.selectbox("בחר אפשרות:", options)
        # המרה ל-DataFrame להצגה כטבלה
        current_info = pd.DataFrame(list(data[selected_option].items()), columns=["שם עמודה", "מספר תווים"], index=None)
        # הצגת הטבלה
        gb = GridOptionsBuilder.from_dataframe(current_info)
        gb.configure_default_column(editable=True)  # הגדרת כל העמודות כניתנות לעריכה
        grid_options = gb.build()

        # הצגת הטבלה הניתנת לעריכה
        grid_response = AgGrid(
            current_info,
            gridOptions=grid_options,
            update_mode=GridUpdateMode.VALUE_CHANGED,
        )

        # קבלת הנתונים המעודכנים
        updated_info = pd.DataFrame(grid_response['data'])
        
    # שלב 1: העלאת קובץ
    uploaded_file = st.file_uploader("בחר קובץ להעלאה", type="dat")
        # רשימת אפשרויות
    
    if uploaded_file is not None:
        # שלב 2: קריאת והצגת הנתונים מהקובץ
        df = pd.read_fwf(uploaded_file, widths=updated_info['מספר תווים'], names=updated_info['שם עמודה'], encoding='ISO-8859-8')
        # הגדרת הגדרות הטבלה
        gb = GridOptionsBuilder.from_dataframe(df)
        gb.configure_default_column(editable=True)  # הגדרת כל העמודות כניתנות לעריכה
        grid_options = gb.build()

        # הצגת הטבלה הניתנת לעריכה
        grid_response = AgGrid(
            df,
            gridOptions=grid_options,
            update_mode=GridUpdateMode.VALUE_CHANGED,
        )

        # קבלת הנתונים המעודכנים
        updated_df = pd.DataFrame(grid_response['data'])
        # הצגת הטבלה לאחר עריכה
        st.write("טבלה מעודכנת:")
        st.dataframe(updated_df)
        # שלב 3: הורדה של הקובץ כ-CSV לאחר עיבוד
        csv = df.to_csv(index=False, encoding='utf-8-sig')

        st.download_button(
            label="הורד את הקובץ כ-CSV",
            data=csv,
            
            file_name='modified_data.csv',
            mime='text/csv',
        )



main()