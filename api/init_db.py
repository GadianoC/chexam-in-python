import sqlite3

def init_db():
    conn = sqlite3.connect("results.db")
    c = conn.cursor()

    # Raw student answers
    c.execute('''
        CREATE TABLE IF NOT EXISTS student_answers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_name TEXT,
            correct_answers TEXT,
            student_answers TEXT,
            analyzed INTEGER DEFAULT 0
        )
    ''')

    # Gemini analysis results
    c.execute('''
        CREATE TABLE IF NOT EXISTS analysis_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER,
            score TEXT,
            percentage INTEGER,
            correct_indices TEXT,
            wrong_indices TEXT,
            strengths TEXT,
            weaknesses TEXT,
            suggestions TEXT,
            FOREIGN KEY(student_id) REFERENCES student_answers(id)
        )
    ''')

    conn.commit()
    conn.close()
