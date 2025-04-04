import streamlit as st
import pandas as pd
import json
from io import StringIO
import io
import openpyxl
import traceback
import os


# פונקציה לטעינת קובץ DAT ושמירת התוכן ב-session state לקריאה חוזרת
def load_dat_file():
    if 'uploaded_dat_content' not in st.session_state:
        uploaded_file = st.file_uploader("בחר קובץ להעלאה", type=["dat", "txt"])
        if uploaded_file:
            # שמירה של תוכן הקובץ כ-StringIO כך שנוכל להשתמש בו מחדש
            try:
                # ניסיון קריאה עם קידודים שונים
                encodings = ['ISO-8859-8', 'windows-1255', 'utf-8', 'cp862']
                dat_content = None
                successful_encoding = None
                
                for encoding in encodings:
                    try:
                        # איפוס המצביע לתחילת הקובץ
                        uploaded_file.seek(0)
                        content = uploaded_file.getvalue().decode(encoding)
                        dat_content = StringIO(content)
                        successful_encoding = encoding
                        break
                    except UnicodeDecodeError:
                        continue
                
                if dat_content is None:
                    st.error(f"לא הצלחתי לקרוא את הקובץ. נסיתי את הקידודים: {', '.join(encodings)}. נסה להמיר את הקובץ לקידוד נתמך.")
                    st.info("טיפ: אם הקובץ מכיל עברית, הקידודים הנפוצים הם ISO-8859-8 או windows-1255.")
                    return None
                
                st.session_state['uploaded_dat_content'] = dat_content
                st.session_state['raw_dat_content'] = content
                st.session_state['file_name'] = uploaded_file.name
                st.session_state['file_encoding'] = successful_encoding
                
                # הצגת תצוגה מקדימה של הקובץ
                dat_content.seek(0)
                preview_lines = []
                for i, line in enumerate(dat_content):
                    if i < 5:  # מציג רק 5 שורות ראשונות
                        preview_lines.append(line.strip())
                    else:
                        break
                
                st.subheader(f"תצוגה מקדימה של הקובץ: {uploaded_file.name} (קידוד: {successful_encoding})")
                st.text("\n".join(preview_lines) + ("\n..." if len(preview_lines) == 5 else ""))
                
                # מחזיר את הפוינטר לתחילת הקובץ
                dat_content.seek(0)
                
                # יצירת טבלאות נפרדות לכל סוג רשומה וזיהוי אוטומטי של סוגי רשומות
                parse_dat_to_tables(dat_content)
                
            except Exception as e:
                st.error(f"שגיאה בקריאת הקובץ: {str(e)}.")
                st.error("פירוט השגיאה:")
                st.code(traceback.format_exc())
                st.info("עצות לפתרון: נסה לוודא שהקובץ בפורמט הנכון, בדוק את המבנה שלו, או נסה להמיר אותו לקידוד תקין.")
                return None
    return st.session_state.get('uploaded_dat_content', None)

# פונקציה חדשה לפירוק קובץ DAT לטבלאות נפרדות לפי סוג רשומה
def parse_dat_to_tables(dat_content):
    data = json_file()
    options = list(data.keys())
    
    # יצירת מילון לשמירת ה-DataFrames לפי סוגי רשומות
    dataframes = {}
    errors = {}
    unreadable_columns = {}
    
    for option in options:
        # איפוס `dat_content` כך שיהיה מוכן לקריאה חדשה עבור כל אפשרות
        dat_content.seek(0)
        # יצירת DataFrame לפי המידע מ-JSON עבור כל אפשרות
        current_info = pd.DataFrame(list(data[option].items()), columns=["שם עמודה", "מספר תווים"])
        try:
            df = pd.read_fwf(dat_content, widths=current_info['מספר תווים'], names=current_info['שם עמודה'], dtype=str)
            # בדיקה שקיימת עמודה "סוג רשומה"
            if 'סוג רשומה' not in df.columns:
                errors[option] = "העמודה 'סוג רשומה' לא נמצאה בנתונים"
                continue
                
            df = df[df['סוג רשומה'] == option]
            
            if not df.empty:
                # טיפול בערכים מספריים
                for col in df.columns:
                    df[col] = df[col].apply(lambda x: clean_numeric_value(x))
                
                # בדיקת עמודות לא קריאות (מכילות רק ערכים חסרים או לא תקינים)
                bad_columns = []
                for column in df.columns:
                    # בדיקה אם העמודה מכילה רק ערכים ריקים או לא תקינים
                    if df[column].isna().all() or (df[column] == '').all():
                        bad_columns.append(column)
                
                if bad_columns:
                    unreadable_columns[option] = bad_columns
                
                dataframes[option] = df.fillna('')
        except Exception as e:
            errors[option] = f"שגיאה: {str(e)}"
    
    # שמירת ה-DataFrames ב-session state לשימוש מאוחר יותר
    st.session_state['parsed_dataframes'] = dataframes
    st.session_state['unreadable_columns'] = unreadable_columns
    
    # הצגת שגיאות אם היו כאלה
    if errors:
        st.warning("התרחשו מספר שגיאות בזמן פירוק הנתונים:")
        for option, error in errors.items():
            st.warning(f"סוג רשומה {option}: {error}")
    
    # הצגת מידע על עמודות לא קריאות
    if unreadable_columns:
        st.warning("נמצאו עמודות שאינן קריאות או ריקות:")
        for option, columns in unreadable_columns.items():
            st.warning(f"סוג רשומה {option}: {len(columns)} עמודות לא קריאות")
            if len(columns) > 5:
                st.info(f"לדוגמה: {', '.join(columns[:5])}... ועוד {len(columns)-5} עמודות נוספות")
            else:
                st.info(f"העמודות: {', '.join(columns)}")

def json_file():
    # קריאת קובץ JSON ופרשנות הנתונים למילון פייתון
    try:
        file_path = 'aba.json'
        if not os.path.isfile(file_path):
            st.error(f"קובץ ההגדרות {file_path} לא נמצא בתיקיה הנוכחית.")
            st.info(f"נא לוודא שקובץ {file_path} קיים בתיקיה {os.getcwd()}")
            return {}
            
        with open(file_path, 'r', encoding='utf-8-sig') as file:
            data = json.load(file)
            return data
    except json.JSONDecodeError as e:
        st.error(f"שגיאה בקריאת קובץ JSON: {str(e)}")
        st.error("פירוט השגיאה:")
        st.code(traceback.format_exc())
        st.info("וודא שקובץ JSON תקין ובפורמט הנכון.")
        return {}
    except Exception as e:
        st.error(f"שגיאה בקריאת קובץ JSON: {str(e)}")
        st.error("פירוט השגיאה:")
        st.code(traceback.format_exc())
        return {}

# פונקציה להצגת כל תוכן הקובץ
def show_all_file_content():
    if 'raw_dat_content' in st.session_state and 'file_name' in st.session_state:
        st.subheader(f"תוכן מלא של הקובץ: {st.session_state['file_name']}")
        # הצגת תוכן הקובץ בתיבת טקסט גדולה כדי שיהיה נוח לקריאה
        st.text_area("תוכן הקובץ", st.session_state['raw_dat_content'], height=400)
        
        # הוספת כפתור להורדת הקובץ המקורי
        encoding = st.session_state.get('file_encoding', 'ISO-8859-8')
        st.download_button(
            label="הורד את הקובץ המקורי",
            data=st.session_state['raw_dat_content'].encode(encoding),
            file_name=st.session_state['file_name'],
            mime="text/plain"
        )

# פונקציה להמרת Excel לקובץ DAT
def excel_to_dat(excel_file, column_widths):
    try:
        df = pd.read_excel(excel_file)
        
        if 'סוג רשומה' not in df.columns:
            st.error("הקובץ חייב להכיל עמודה בשם 'סוג רשומה'")
            return None
        
        # המרת כל העמודות למחרוזות וניקוי מספרים עשרוניים
        df["סוג רשומה"] = df["סוג רשומה"].fillna('20.0').astype(str).replace('20.0', '20')
        
        # החלפת שמות העמודות לפי סוגי הרשומות
        df_groups = {}
        
        # מיון הנתונים לפי סוג רשומה
        record_types = df['סוג רשומה'].astype(str).unique()
        
        # ראשית נחלק את ה-DataFrame לקבוצות לפי סוג רשומה
        for record_type in record_types:
            if record_type not in column_widths:
                st.warning(f"סוג רשומה {record_type} אינו מוגדר בקובץ ההגדרות. שורות אלו לא יומרו.")
                continue
                
            record_df = df[df['סוג רשומה'].astype(str) == record_type]
            
            # מחלצים את שמות העמודות האמיתיים מקובץ ההגדרות
            real_column_names = list(column_widths[record_type].keys())
            
            # החלפת שמות העמודות לשמות האמיתיים
            record_columns = list(record_df.columns)
            rename_map = {}
            
            # נשמור תמיד על עמודת סוג רשומה
            for i, col_name in enumerate(record_columns):
                if col_name == 'סוג רשומה':
                    continue
                if i < len(real_column_names) and real_column_names[i] != col_name:
                    rename_map[col_name] = real_column_names[i]
            
            if rename_map:
                record_df = record_df.rename(columns=rename_map)
                st.info(f"הוחלפו שמות עמודות עבור סוג רשומה {record_type} לשמות המוגדרים בקובץ ההגדרות")
                
            df_groups[record_type] = record_df
        
        # יצירת מחרוזת DAT לפי רוחב העמודות המוגדר בקובץ JSON
        dat_lines = []
        
        # עיבוד כל קבוצת רשומות בנפרד
        for record_type, record_df in df_groups.items():
            record_widths = column_widths[record_type]
            
            for _, row in record_df.iterrows():
                try:
                    dat_line = ""
                    for col_name, width in record_widths.items():
                        # אם העמודה קיימת בקובץ Excel
                        if col_name in record_df.columns:
                            # המרה לסטרינג של כל סוגי הנתונים, כולל numpy.int64
                            value = str(row.get(col_name, ""))
                            # התאמת אורך למספר התווים המוגדר בקובץ JSON
                            value = value.ljust(width)[:width]
                        else:
                            # אם העמודה לא קיימת, יוצרים שדה ריק באורך המתאים
                            value = " " * width
                        
                        dat_line += value
                    
                    dat_lines.append(dat_line)
                except Exception as e:
                    st.warning(f"שגיאה בהמרת שורה: {str(e)}")
                    st.warning(f"השורה הבעייתית: {row}")
                    continue
        
        if not dat_lines:
            st.error("לא נוצרו שורות להמרה. בדוק את נתוני הקלט.")
            return None
            
        return "\n".join(dat_lines)
    except Exception as e:
        st.error(f"שגיאה כללית בהמרת קובץ Excel לקובץ DAT: {str(e)}")
        st.error("פירוט השגיאה:")
        st.code(traceback.format_exc())
        return None

# פונקציה לניקוי ערכים מספריים
def clean_numeric_value(value):
    if pd.isna(value):
        return ""
    
    # המרה למחרוזת
    string_value = str(value)
    
    # בדיקה אם זה מספר עם נקודה עשרונית
    if '.' in string_value:
        try:
            return str(int(string_value))
        except:
            # אם ההמרה למספר נכשלה, החזר את המחרוזת המקורית
            return string_value
    
    return string_value

# פונקציה לייצוא קובץ DAT
def export_dat(dataframes, record_types, column_info):
    try:
        dat_lines = []
        
        for record_type, df in zip(record_types, dataframes):
            # טיפול בערכים מספריים לפני הייצוא
            cleaned_df = df.copy()
            cleaned_df["סוג רשומה"] = cleaned_df["סוג רשומה"].astype(int, errors='ignore').astype(str)
                
            for _, row in cleaned_df.iterrows():
                try:
                    dat_line = ""
                    for col_name, width in column_info[record_type].items():
                        value = str(row.get(col_name, ""))
                        # התאמת אורך למספר התווים המוגדר בקובץ JSON
                        value = value.ljust(width)[:width]
                        dat_line += value
                    
                    dat_lines.append(dat_line)
                except Exception as e:
                    st.warning(f"שגיאה בייצוא שורה מסוג {record_type}: {str(e)}")
                    continue
        
        if not dat_lines:
            st.error("לא נוצרו שורות לייצוא. בדוק את הנתונים המקוריים.")
            return None
            
        return "\n".join(dat_lines)
    except Exception as e:
        st.error(f"שגיאה בייצוא קובץ DAT: {str(e)}")
        st.error("פירוט השגיאה:")
        st.code(traceback.format_exc())
        return None

def main():
    # טוען קובץ JSON ושומר אותו ב-session state
    data = json_file()
    
    if not data:
        st.error("לא נמצאו הגדרות בקובץ aba.json. האפליקציה לא תפעל כראוי ללא הגדרות אלו.")
        st.info("אנא וודא שקובץ aba.json תקין ונמצא באותה תיקייה כמו הקובץ הנוכחי.")
        st.stop()
        
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
    .record-header {
        background-color: #f0f0f0;
        padding: 10px;
        border-radius: 5px;
        margin-bottom: 10px;
        border-left: 4px solid #4CAF50;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown('<div class="custom-header"><h1 class="big-font">ניתוח קבצים</h1></div>', unsafe_allow_html=True)
    # רשימת אפשרויות מתוך הקובץ
    options = list(data.keys())
    
    # יוצר לשוניות לניווט בין האפשרויות השונות
    tab1, tab2, tab3 = st.tabs(["המרת DAT לאקסל", "המרת אקסל ל-DAT", "תצוגת קובץ DAT"])
    
    with tab1:
        # טוען את תוכן קובץ DAT ב-session state כ-StringIO
        dat_content = load_dat_file()
            
        # מציג את הטבלאות אם הנתונים קיימים
        if dat_content is not None and 'parsed_dataframes' in st.session_state:
            dataframes = st.session_state['parsed_dataframes']
            
            # בדיקה אם יש נתונים בקובץ
            if not dataframes:
                st.warning("לא נמצאו נתונים תואמים בקובץ או שמבנה הקובץ אינו מתאים למבנה המוגדר בקובץ ההגדרות.")
                st.info("אנא וודא שמבנה הקובץ תואם את ההגדרות ב-aba.json ושהקובץ מכיל עמודת 'סוג רשומה'.")
                
                # הצגת מידע נוסף על הקובץ לעזרה בפתרון בעיות
                if st.checkbox("הצג מידע נוסף על הקובץ"):
                    try:
                        st.session_state['uploaded_dat_content'].seek(0)
                        first_few_lines = []
                        for i, line in enumerate(st.session_state['uploaded_dat_content']):
                            if i < 10:
                                first_few_lines.append(line.strip())
                            else:
                                break
                        
                        st.subheader("10 השורות הראשונות בקובץ:")
                        st.code("\n".join(first_few_lines))
                        
                        st.subheader("אופציות קיימות מקובץ ההגדרות:")
                        for option in options:
                            st.write(f"סוג רשומה: {option}")
                            st.write(f"מספר עמודות מוגדרות: {len(data[option])}")
                            
                    except Exception as e:
                        st.error(f"שגיאה בהצגת מידע נוסף: {str(e)}")
            else:
                # הצגת הטבלאות לפי סוגי רשומות
                record_types = list(dataframes.keys())
                
                # אפשרות לבחור איזה סוגי רשומות להציג
                selected_record_types = st.multiselect(
                    "בחר סוגי רשומות להצגה:", 
                    record_types,
                    default=record_types
                )
                
                # הצגת הטבלאות שנבחרו
                for record_type in selected_record_types:
                    df = dataframes[record_type]
                    
                    # יצירת כותרת אטרקטיבית לכל טבלה
                    st.markdown(f'<div class="record-header"><h3>טבלה עבור סוג רשומה {record_type}</h3></div>', 
                                unsafe_allow_html=True)
                    
                    row_count = len(df)
                    col_count = len(df.columns)
                    st.write(f"מספר שורות: {row_count}, מספר עמודות: {col_count}")
                    
                    # האם יש עמודות לא קריאות לסוג רשומה זה
                    has_unreadable_columns = (
                        'unreadable_columns' in st.session_state and
                        record_type in st.session_state['unreadable_columns'] and
                        st.session_state['unreadable_columns'][record_type]
                    )
                    
                    if has_unreadable_columns:
                        unreadable_cols = st.session_state['unreadable_columns'][record_type]
                        st.warning(f"נמצאו {len(unreadable_cols)} עמודות לא קריאות בטבלה זו")
                        
                        # אפשרות להציג רק עמודות קריאות
                        show_only_readable = st.checkbox(f"הצג רק עמודות קריאות לסוג רשומה {record_type}")
                        if show_only_readable:
                            readable_columns = [col for col in df.columns if col not in unreadable_cols]
                            st.write(f"מציג {len(readable_columns)} עמודות קריאות מתוך {len(df.columns)} עמודות")
                            st.dataframe(df[readable_columns], selection_mode="multi-row", use_container_width=True)
                        else:
                            # הצגת הטבלה עם אפשרות לבחירת שורות
                            st.dataframe(df, selection_mode="multi-row", use_container_width=True)
                    else:
                        # הצגת הטבלה עם אפשרות לבחירת שורות
                        st.dataframe(df, selection_mode="multi-row", use_container_width=True)
            
                # הצגת מידע על עמודות לא קריאות
                if 'unreadable_columns' in st.session_state and st.session_state['unreadable_columns']:
                    with st.expander("פרטים על עמודות לא קריאות"):
                        st.warning("נמצאו עמודות שאינן קריאות או ריקות:")
                        for record_type, columns in st.session_state['unreadable_columns'].items():
                            st.warning(f"סוג רשומה {record_type}: {len(columns)} עמודות לא קריאות")
                            if len(columns) > 5:
                                st.info(f"לדוגמה: {', '.join(columns[:5])}... ועוד {len(columns)-5} עמודות נוספות")
                            else:
                                st.info(f"העמודות: {', '.join(columns)}")
                
                # הוספת אפשרות לייצוא לאקסל אם יש נתונים
                if dataframes:
                    st.write("ייצוא נתונים:")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        # ייצוא לאקסל
                        if st.button("ייצא לקובץ אקסל"):
                            try:
                                # יצירת קובץ אקסל
                                excel_buffer = io.BytesIO()
                                with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
                                    for record_type, df in dataframes.items():
                                        sheet_name = f"סוג רשומה {record_type}"
                                        df.to_excel(writer, sheet_name=sheet_name, index=False)
                                
                                # הורדת הקובץ
                                st.download_button(
                                    label="לחץ להורדת קובץ אקסל",
                                    data=excel_buffer.getvalue(),
                                    file_name="aba_export.xlsx",
                                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                                )
                            except Exception as e:
                                st.error(f"שגיאה בייצוא לאקסל: {str(e)}")
                                st.error("פירוט השגיאה:")
                                st.code(traceback.format_exc())
                    
                    with col2:
                        # ייצוא לקובץ DAT
                        if st.button("ייצא לקובץ DAT"):
                            try:
                                # הכנת הנתונים לייצוא
                                export_record_types = []
                                export_dataframes = []
                                
                                for record_type in record_types:
                                    export_record_types.append(record_type)
                                    export_dataframes.append(dataframes[record_type])
                                
                                # יצירת קובץ DAT
                                dat_content = export_dat(export_dataframes, export_record_types, data)
                                if dat_content:
                                    # תצוגה מקדימה של הקובץ DAT
                                    preview_lines = dat_content.split('\n')[:5]
                                    st.subheader("תצוגה מקדימה של קובץ DAT:")
                                    st.text("\n".join(preview_lines) + ("\n..." if len(preview_lines) == 5 else ""))
                                    
                                    # הורדת הקובץ
                                    encoding = st.selectbox(
                                        "בחר קידוד לקובץ היצוא:",
                                        ['ISO-8859-8', 'windows-1255', 'utf-8'],
                                        index=0
                                    )
                                    
                                    st.download_button(
                                        label="לחץ להורדת קובץ DAT",
                                        data=dat_content.encode(encoding),
                                        file_name="aba_export.dat",
                                        mime="text/plain"
                                    )
                            except Exception as e:
                                st.error(f"שגיאה בייצוא לקובץ DAT: {str(e)}")
                                st.error("פירוט השגיאה:")
                                st.code(traceback.format_exc())
                    
                    # הוספת אפשרות להצגת הקובץ המקורי
                    if st.checkbox("הצג את תוכן הקובץ המקורי"):
                        show_all_file_content()
    
    with tab2:
        st.header("המרת קובץ אקסל לקובץ DAT")
        
        # אפשרות להעלאת קובץ אקסל
        excel_file = st.file_uploader("בחר קובץ אקסל להעלאה", type=["xlsx", "xls"])
        
        if excel_file:
            try:
                # קריאת הקובץ והצגת תצוגה מקדימה
                preview_df = pd.read_excel(excel_file)
                preview_df["סוג רשומה"] = preview_df["סוג רשומה"].fillna('20.0').astype(str).replace('20.0', '20')
                print('preview_df:', list(preview_df["סוג רשומה"]))
                st.subheader("תצוגה מקדימה של הקובץ:")
                st.dataframe(preview_df.head(), use_container_width=True)
                
                # בדיקה שיש עמודת "סוג רשומה" בקובץ
                if 'סוג רשומה' not in preview_df.columns:
                    st.error("הקובץ חייב להכיל עמודה בשם 'סוג רשומה' כדי לזהות אוטומטית את סוג הרשומה")
                    st.info("נא להוסיף עמודה בשם 'סוג רשומה' לקובץ האקסל, ולמלא בה את סוג הרשומה המתאים לכל שורה (10, 20, 30, 40 או 50)")
                else:
                    # זיהוי אוטומטי של סוגי הרשומות בקובץ
                    found_record_types = preview_df['סוג רשומה'].astype(str).unique()
                    st.write(f"סוגי רשומות שזוהו בקובץ: {', '.join(found_record_types)}")
                    
                    # בדיקה שכל סוגי הרשומות מוגדרים ב-JSON
                    valid_record_types = [rt for rt in found_record_types if rt in data]
                    invalid_record_types = [rt for rt in found_record_types if rt not in data]
                    
                    if invalid_record_types:
                        st.warning(f"סוגי הרשומות הבאים לא מוגדרים בקובץ ההגדרות: {', '.join(invalid_record_types)}")
                        st.info(f"רק סוגי הרשומות הבאים מוגדרים בקובץ ההגדרות: {', '.join(options)}")
                    
                    # לחצן להמרה
                    if valid_record_types and st.button("המר לקובץ DAT"):
                        # המרת קובץ אקסל לקובץ DAT תוך זיהוי אוטומטי של סוג הרשומה
                        with st.spinner('מבצע המרה...'):
                            dat_content = excel_to_dat(excel_file, data)
                        
                        if dat_content:
                            # הצגת תצוגה מקדימה של הקובץ
                            preview_lines = dat_content.split('\n')[:5]
                            st.subheader("תצוגה מקדימה של קובץ DAT:")
                            st.text("\n".join(preview_lines) + ("\n..." if len(preview_lines) == 5 else ""))
                            
                            # בחירת קידוד לקובץ
                            encoding = st.selectbox(
                                "בחר קידוד לקובץ היצוא:",
                                ['ISO-8859-8', 'windows-1255', 'utf-8'],
                                index=0
                            )
                            
                            # הורדת הקובץ
                            st.download_button(
                                label="לחץ להורדת קובץ DAT",
                                data=dat_content.encode(encoding),
                                file_name="excel_to_dat_export.dat",
                                mime="text/plain"
                            )
            except Exception as e:
                st.error(f"שגיאה בקריאת קובץ האקסל: {str(e)}")
                st.error("פירוט השגיאה:")
                st.code(traceback.format_exc())
                st.info("טיפ: וודא שהקובץ הוא אכן בפורמט אקסל תקין ושהנתונים בו מסודרים בצורה נכונה.")
    
    with tab3:
        st.header("תצוגת קובץ DAT")
        # בדיקה אם יש קובץ DAT שהועלה
        if 'parsed_dataframes' in st.session_state and st.session_state['parsed_dataframes']:
            
            dataframes = st.session_state['parsed_dataframes']
            record_types = list(dataframes.keys())
            
            # רשימת בחירה של סוגי הרשומות
            selected_type = st.selectbox(
                "בחר סוג רשומה להצגה:",
                record_types
            )
            
            if selected_type:
                df = dataframes[selected_type]
                
                # אפשרויות תצוגה
                view_options = ["טבלה מלאה", "עמודות נבחרות", "סינון נתונים"]
                # אם יש עמודות לא קריאות, הוסף אפשרות להצגת רק עמודות קריאות
                if ('unreadable_columns' in st.session_state and 
                    selected_type in st.session_state['unreadable_columns'] and 
                    st.session_state['unreadable_columns'][selected_type]):
                    view_options.append("עמודות קריאות בלבד")
                
                view_option = st.radio(
                    "אפשרויות תצוגה:",
                    view_options,
                    horizontal=True
                )
                
                if view_option == "טבלה מלאה":
                    # הצגת הטבלה המלאה
                    st.markdown(f'<div class="record-header"><h3>טבלה עבור סוג רשומה {selected_type}</h3></div>', unsafe_allow_html=True)
                    st.dataframe(df, use_container_width=True)
                    
                elif view_option == "עמודות נבחרות":
                    # בחירת עמודות להצגה
                    columns = df.columns.tolist()
                    selected_columns = st.multiselect("בחר עמודות להצגה:", columns, default=columns[:5] if len(columns) > 5 else columns)
                    
                    if selected_columns:
                        st.markdown(f'<div class="record-header"><h3>עמודות נבחרות מטבלה {selected_type}</h3></div>', unsafe_allow_html=True)
                        st.dataframe(df[selected_columns], use_container_width=True)
                    else:
                        st.info("נא לבחור עמודות להצגה")
                        
                elif view_option == "עמודות קריאות בלבד":
                    # הצגת רק העמודות הקריאות
                    unreadable_cols = st.session_state['unreadable_columns'][selected_type]
                    readable_columns = [col for col in df.columns if col not in unreadable_cols]
                    
                    st.markdown(f'<div class="record-header"><h3>עמודות קריאות בלבד מטבלה {selected_type}</h3></div>', unsafe_allow_html=True)
                    st.write(f"מציג {len(readable_columns)} עמודות קריאות מתוך {len(df.columns)} עמודות")
                    st.write(f"הושמטו {len(unreadable_cols)} עמודות לא קריאות או ריקות")
                    
                    st.dataframe(df[readable_columns], use_container_width=True)
                        
                else:  # סינון נתונים
                    # בחירת עמודות לסינון
                    filter_column = st.selectbox("בחר עמודה לסינון:", df.columns.tolist())
                    
                    if filter_column:
                        # קבלת ערכים ייחודיים בעמודה
                        unique_values = df[filter_column].unique().tolist()
                        filter_value = st.selectbox(f"בחר ערך ב{filter_column}:", unique_values)
                        
                        filtered_df = df[df[filter_column] == filter_value]
                        st.markdown(f'<div class="record-header"><h3>נתונים מסוננים לפי {filter_column} = {filter_value}</h3></div>', unsafe_allow_html=True)
                        st.dataframe(filtered_df, use_container_width=True)
                
                # אפשרות ייצוא הטבלה הנוכחית
                if st.button("ייצא טבלה זו לאקסל"):
                    try:
                        excel_buffer = io.BytesIO()
                        with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
                            df.to_excel(writer, index=False)
                        
                        st.download_button(
                            label=f"הורד טבלה {selected_type} לאקסל",
                            data=excel_buffer.getvalue(),
                            file_name=f"table_type_{selected_type}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )
                    except Exception as e:
                        st.error(f"שגיאה בייצוא לאקסל: {str(e)}")
                        st.error("פירוט השגיאה:")
                        st.code(traceback.format_exc())
            
            # סטטיסטיקה כללית על הקובץ
            st.subheader("סטטיסטיקה על הקובץ:")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                total_rows = sum(len(df) for df in dataframes.values())
                st.metric("סה״כ שורות", total_rows)
                
            with col2:
                st.metric("סוגי רשומות", len(dataframes))
                
            with col3:
                # רשומה עם מספר השורות הגבוה ביותר
                max_rows_type = max(dataframes.items(), key=lambda x: len(x[1]))[0] if dataframes else "אין נתונים"
                st.metric("רשומה עם מירב השורות", f"{max_rows_type}")
            
            # טבלה סטטיסטית של התפלגות סוגי הרשומות
            stats_data = {
                "סוג רשומה": [],
                "מספר שורות": [],
                "מספר עמודות": [],
                "אחוז מכלל הרשומות": []
            }
            
            for record_type, df in dataframes.items():
                stats_data["סוג רשומה"].append(record_type)
                stats_data["מספר שורות"].append(len(df))
                stats_data["מספר עמודות"].append(len(df.columns))
                stats_data["אחוז מכלל הרשומות"].append(f"{(len(df) / total_rows * 100):.1f}%" if total_rows > 0 else "0%")
            
            st.subheader("התפלגות סוגי רשומות:")
            stats_df = pd.DataFrame(stats_data)
            st.table(stats_df)
                
        else:
            st.info("לא נמצא קובץ DAT שהועלה או שהקובץ ריק. אנא העלה קובץ DAT בלשונית הראשונה.")

main()
