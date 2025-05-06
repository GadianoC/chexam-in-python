import sqlite3
import json
from api.gemini_analysis import analyze_bubble_answers

def analyze_all_students():
    conn = sqlite3.connect("results.db")
    c = conn.cursor()

    # Get all unanalyzed students
    c.execute('SELECT id, student_name, correct_answers, student_answers FROM student_answers WHERE analyzed = 0')
    students = c.fetchall()

    for student in students:
        student_id, name, correct_json, student_json = student
        correct = json.loads(correct_json)
        answers = json.loads(student_json)

        print(f" Analyzing {name}...")
        result = analyze_bubble_answers(correct, answers)

        if result:
            c.execute('''
                INSERT INTO analysis_results (
                    student_id, score, percentage,
                    correct_indices, wrong_indices,
                    strengths, weaknesses, suggestions
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                student_id,
                result.get("score"),
                result.get("percentage"),
                json.dumps(result.get("correct_indices")),
                json.dumps(result.get("wrong_indices")),
                result.get("strengths"),
                result.get("weaknesses"),
                result.get("suggestions")
            ))

            # Mark as analyzed
            c.execute('UPDATE student_answers SET analyzed = 1 WHERE id = ?', (student_id,))
            print(f"Done analyzing {name}.")
        else:
            print(f"Failed to analyze {name}.")

    conn.commit()
    conn.close()
