import os
from api.save_answers import save_student_answers

def load_txt_answers(folder_path, correct_answers):
    for filename in os.listdir(folder_path):
        if filename.endswith(".txt"):
            student_name = os.path.splitext(filename)[0]
            with open(os.path.join(folder_path, filename), 'r') as file:
                student_answers = [line.strip().upper() for line in file if line.strip()]
                save_student_answers(student_name, correct_answers, student_answers)
                print(f"✅ Saved answers for {student_name}")
