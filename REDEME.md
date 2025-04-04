DAT to Excel Converter

This application converts DAT files to Excel files and vice versa based on predefined formatting rules outlined in the configuration file (ABA.JSON). It features an intuitive user interface developed with the Streamlit library.

Features

Upload and Convert DAT Files: Upload your DAT file, specify the table type (available types: 10, 20, 30, 40, 50), and the application automatically generates a structured table according to column definitions.

Excel Export: Easily export the generated tables to Excel format.

DAT Export: Export processed data back to a DAT file format, preserving the fixed-width column structure.

Excel to DAT Conversion: Upload Excel files to convert them back to DAT format according to specified formatting rules.

How to Use

DAT to Excel Conversion

Upload your .DAT file through the Streamlit interface.

The system will automatically identify and display all record types (10, 20, 30, 40, 50) found in the file by looking at the "סוג רשומה" column.

The data is processed and displayed in a structured table format, separated by record type.

Optionally export the data as an Excel file (each record type in its own worksheet) or back to a DAT file.

Excel to DAT Conversion

Upload your Excel file via the provided upload option.

Specify the relevant table type (10, 20, 30, 40, 50) to match predefined rules.

The system checks formatting rules from ABA.JSON.

It generates and allows downloading of a correctly formatted DAT file.

Requirements

Python 3.8 or later

Streamlit

Pandas

OpenPyXL

Installation

pip install streamlit pandas openpyxl

Running the Application

streamlit run app.py

Ensure ABA.JSON is correctly configured and placed in the same directory as the application.

ממיר קבצים מסוג DAT לאקסל

אפליקציה זו ממירה קבצים מסוג DAT לאקסל ולהיפך לפי חוקים קבועים ומתועדים בקובץ ההגדרות (ABA.JSON). המערכת כוללת ממשק נוח ופשוט המבוסס על ספריית Streamlit.

תכונות

העלאה והמרת קבצי DAT: העלו קובץ DAT, והמערכת תזהה אוטומטית את סוגי הטבלאות (סוגים זמינים: 10, 20, 30, 40, 50) לפי עמודת "סוג רשומה" ותייצר טבלה לפי מבנה העמודות בקובץ התיעוד.

ייצוא לאקסל: אפשרות קלה לייצא את הטבלה המתקבלת לקובץ אקסל.

ייצוא לקובץ DAT: אפשרות לייצא את הנתונים חזרה לפורמט DAT, תוך שמירה על מבנה העמודות קבועות הרוחב.

המרת אקסל ל-DAT: אפשרות להעלות קובץ אקסל ולהמיר אותו לקובץ DAT תקין, לפי כללים מתועדים.

הוראות שימוש

המרת DAT לאקסל

העלו את הקובץ .DAT דרך הממשק של Streamlit.

המערכת תזהה אוטומטית את כל סוגי הרשומות (10, 20, 30, 40, 50) הקיימים בקובץ על ידי בדיקת עמודת "סוג רשומה".

המידע מוצג בטבלה מובנית, מחולקת לפי סוג רשומה.

ניתן לייצא את הנתונים לקובץ אקסל (כל סוג רשומה בגליון נפרד) או חזרה לקובץ DAT.

המרת אקסל ל-DAT

העלו את קובץ האקסל שברצונכם להמיר.

בחרו את סוג הטבלה המתאים (10, 20, 30, 40, 50) לפי הכללים הקבועים.

המערכת בודקת את כללי המרווחים והפורמט מתוך ABA.JSON.

המערכת מייצרת ומאפשרת הורדה של קובץ DAT תקין.

דרישות

Python 3.8 ומעלה

Streamlit

Pandas

OpenPyXL

התקנה

pip install streamlit pandas openpyxl

הפעלת האפליקציה

streamlit run app.py

וודאו שהקובץ ABA.JSON מוגדר נכון ונמצא באותה תיקייה עם קובצי האפליקציה.

