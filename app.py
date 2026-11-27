
import streamlit as st
import pandas as pd
import sqlite3
import matplotlib.pyplot as plt
import seaborn as sns

st.set_page_config(
    page_title="InsightHub",
    page_icon="🎓",
    layout="wide"
)

st.title("🎓 InsightHub")
st.subheader("Student Performance Analytics Dashboard")

# Connect to database
conn = sqlite3.connect("insighthub.db")

# Load student data
df = pd.read_sql_query("SELECT * FROM students", conn)

st.write("Explore student performance, attendance and academic insights.")

# Key Performance Indicators

total_students = len(df)
total_departments = df['department'].nunique()
average_attendance = df['attendance_percentage'].mean()
average_marks = df['internal_marks'].mean()

col1, col2, col3, col4 = st.columns(4)

col1.metric("Total Students", total_students)
col2.metric("Departments", total_departments)
col3.metric("Average Attendance", f"{average_attendance:.2f}%")
col4.metric("Average Internal Marks", f"{average_marks:.2f}")

# -----------------------------------
# 1. STUDENT DISTRIBUTION BY DEPARTMENT
# -----------------------------------

st.header("1. Department Analysis")

department_data = pd.read_sql_query("""
SELECT department, COUNT(*) AS total_students
FROM students
GROUP BY department
ORDER BY department
""", conn)

st.bar_chart(
    department_data.set_index("department"),
    y="total_students"
)

# -----------------------------------
# 2. GRADE DISTRIBUTION
# -----------------------------------

st.header("2. Grade Distribution")

grade_data = pd.read_sql_query("""
SELECT final_grade, COUNT(*) AS total_students
FROM students
GROUP BY final_grade
ORDER BY final_grade
""", conn)

fig, ax = plt.subplots(figsize=(6, 4))
ax.pie(
    grade_data["total_students"],
    labels=grade_data["final_grade"],
    autopct="%1.1f%%",
    startangle=90
)
ax.set_title("Student Grade Distribution")
st.pyplot(fig)
plt.close(fig)

# -----------------------------------
# 3. AVERAGE INTERNAL MARKS
# -----------------------------------

st.header("3. Academic Performance by Department")

marks_data = pd.read_sql_query("""
SELECT department,
       ROUND(AVG(internal_marks), 2) AS average_marks
FROM students
GROUP BY department
ORDER BY department
""", conn)

st.bar_chart(
    marks_data.set_index("department"),
    y="average_marks"
)

# -----------------------------------
# 4. AVERAGE ATTENDANCE
# -----------------------------------

st.header("4. Attendance Analysis")

attendance_data = pd.read_sql_query("""
SELECT department,
       ROUND(AVG(attendance_percentage), 2) AS average_attendance
FROM students
GROUP BY department
ORDER BY department
""", conn)

st.bar_chart(
    attendance_data.set_index("department"),
    y="average_attendance"
)

# -----------------------------------
# 5. BACKLOG DISTRIBUTION
# -----------------------------------

st.header("5. Backlog Analysis")

backlog_data = pd.read_sql_query("""
SELECT backlogs,
       COUNT(*) AS total_students
FROM students
WHERE backlogs IS NOT NULL
GROUP BY backlogs
ORDER BY backlogs
""", conn)

st.bar_chart(
    backlog_data.set_index("backlogs"),
    y="total_students"
)

# -----------------------------------
# 6. TOP 5 STUDENTS
# -----------------------------------

st.header("6. Top 5 Students")

top_students = pd.read_sql_query("""
SELECT student_id, student_name, department,
       internal_marks, final_grade
FROM students
WHERE internal_marks IS NOT NULL
ORDER BY internal_marks DESC
LIMIT 5
""", conn)

st.dataframe(top_students, width="stretch")

conn.close()
