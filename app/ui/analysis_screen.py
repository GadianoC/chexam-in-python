from api.init_db import init_db
from api.load_txts_and_save import load_txt_answers
from api.analyze_all import analyze_all_students

# Define correct answers once
correct_answers = ['A', 'B', 'C', 'D', 'A', 'B', 'C']

# Initialize DB and load students
init_db()
load_txt_answers("student_txts", correct_answers)

# Run Gemini analysis on all
analyze_all_students()
