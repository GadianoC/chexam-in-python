import sqlite3
import json

def save_student_answers(student_name, correct, student):
    conn = sqlite3.connect("results.db")
    c = conn.cursor()
    c.execute('''
        INSERT INTO student_answers (
            student_name, correct_answers, student_answers
        ) VALUES (?, ?, ?)
    ''', (
        student_name,
        json.dumps(correct),
        json.dumps(student)
    ))
    conn.commit()
    conn.close()
