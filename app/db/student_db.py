import sqlite3
import os
import json
import logging
import random
from pathlib import Path
from datetime import datetime

logger = logging.getLogger("chexam.db.student_db")
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('[%(levelname)s] %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

DB_PATH = Path(os.path.dirname(os.path.abspath(__file__))) / ".." / ".." / "data" / "chexam.db"
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

def initialize_student_db():
    try:
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS student_answers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            answer_key_id INTEGER NOT NULL,
            answers TEXT NOT NULL,
            analyzed BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (student_id) REFERENCES students (id) ON DELETE CASCADE,
            FOREIGN KEY (answer_key_id) REFERENCES answer_keys (id) ON DELETE CASCADE
        )
        ''')
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS analysis_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            answer_key_id INTEGER NOT NULL,
            score TEXT NOT NULL,
            percentage REAL NOT NULL,
            correct_indices TEXT NOT NULL,
            wrong_indices TEXT NOT NULL,
            strengths TEXT NOT NULL,
            weaknesses TEXT NOT NULL,
            suggestions TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (student_id) REFERENCES students (id) ON DELETE CASCADE,
            FOREIGN KEY (answer_key_id) REFERENCES answer_keys (id) ON DELETE CASCADE
        )
        ''')
        
        conn.commit()
        conn.close()
        logger.info(f"Student database tables initialized at {DB_PATH}")
        return True
    except Exception as e:
        logger.error(f"Error initializing student database: {str(e)}")
        return False

def add_student(name):
    try:
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()
        
        cursor.execute("SELECT id FROM students WHERE name = ?", (name,))
        existing = cursor.fetchone()
        
        if existing:
            logger.info(f"Student '{name}' already exists with ID {existing[0]}")
            conn.close()
            return existing[0]
        
        cursor.execute(
            "INSERT INTO students (name) VALUES (?)",
            (name,)
        )
        student_id = cursor.lastrowid
        
        conn.commit()
        conn.close()
        logger.info(f"Added new student '{name}' with ID {student_id}")
        return student_id
    except Exception as e:
        logger.error(f"Error adding student: {str(e)}")
        return None

def get_student(student_id=None, name=None):
    try:
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()
        
        if student_id is not None:
            cursor.execute("SELECT * FROM students WHERE id = ?", (student_id,))
        elif name is not None:
            cursor.execute("SELECT * FROM students WHERE name = ?", (name,))
        else:
            logger.error("Either student_id or name must be provided")
            conn.close()
            return None
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                'id': row[0],
                'name': row[1],
                'created_at': row[2]
            }
        else:
            return None
    except Exception as e:
        logger.error(f"Error getting student: {str(e)}")
        return None

def get_all_students():
    try:
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()
        
        cursor.execute("SELECT id, name, created_at FROM students ORDER BY name")
        rows = cursor.fetchall()
        conn.close()
        
        return [
            {
                'id': row[0],
                'name': row[1],
                'created_at': row[2]
            }
            for row in rows
        ]
    except Exception as e:
        logger.error(f"Error getting all students: {str(e)}")
        return []

def delete_student(student_id=None, name=None):
    try:
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()
        
        if student_id is not None:
            cursor.execute("DELETE FROM students WHERE id = ?", (student_id,))
        elif name is not None:
            cursor.execute("DELETE FROM students WHERE name = ?", (name,))
        else:
            logger.error("Either student_id or name must be provided")
            conn.close()
            return False
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"Error deleting student: {str(e)}")
        return False

def save_student_answers(student_id, answer_key_id, answers):
    try:
        answers_json = json.dumps(answers)
        
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT id FROM student_answers WHERE student_id = ? AND answer_key_id = ?",
            (student_id, answer_key_id)
        )
        existing = cursor.fetchone()
        
        if existing:
            cursor.execute(
                "UPDATE student_answers SET answers = ?, analyzed = 0 WHERE id = ?",
                (answers_json, existing[0])
            )
            cursor.execute(
                "DELETE FROM analysis_results WHERE student_id = ? AND answer_key_id = ?",
                (student_id, answer_key_id)
            )
            answer_id = existing[0]
            logger.info(f"Updated answers for student ID {student_id} with answer key ID {answer_key_id}")
        else:
            cursor.execute(
                "INSERT INTO student_answers (student_id, answer_key_id, answers) VALUES (?, ?, ?)",
                (student_id, answer_key_id, answers_json)
            )
            answer_id = cursor.lastrowid
            logger.info(f"Saved new answers for student ID {student_id} with answer key ID {answer_key_id}")
        
        conn.commit()
        conn.close()
        return answer_id
    except Exception as e:
        logger.error(f"Error saving student answers: {str(e)}")
        return None

def get_student_answers(student_id, answer_key_id):

    try:
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT id, answers, analyzed, created_at FROM student_answers WHERE student_id = ? AND answer_key_id = ?",
            (student_id, answer_key_id)
        )
        row = cursor.fetchone()
        conn.close()
        
        if row and row[1]:
            return json.loads(row[1])
        else:
            logger.warning(f"No answers found for student ID {student_id} and answer key ID {answer_key_id}")
            return {}
    except Exception as e:
        logger.error(f"Error getting student answers: {str(e)}")
        return {}

def get_all_student_answers(answer_key_id=None):
    try:
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()
        
        if answer_key_id is not None:
            cursor.execute("""
                SELECT sa.id, s.id, s.name, sa.answer_key_id, sa.answers, sa.analyzed, sa.created_at
                FROM student_answers sa
                JOIN students s ON sa.student_id = s.id
                WHERE sa.answer_key_id = ?
                ORDER BY s.name
            """, (answer_key_id,))
        else:
            cursor.execute("""
                SELECT sa.id, s.id, s.name, sa.answer_key_id, sa.answers, sa.analyzed, sa.created_at
                FROM student_answers sa
                JOIN students s ON sa.student_id = s.id
                ORDER BY s.name
            """)
        
        rows = cursor.fetchall()
        conn.close()
        
        return [
            {
                'id': row[0],
                'student_id': row[1],
                'student_name': row[2],
                'answer_key_id': row[3],
                'answers': json.loads(row[4]),
                'analyzed': bool(row[5]),
                'created_at': row[6]
            }
            for row in rows
        ]
    except Exception as e:
        logger.error(f"Error getting all student answers: {str(e)}")
        return []

def save_analysis_result(student_id, answer_key_id, result):
    try:
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT id FROM analysis_results WHERE student_id = ? AND answer_key_id = ?",
            (student_id, answer_key_id)
        )
        existing = cursor.fetchone()
        
        correct_indices_json = json.dumps(result.get("correct_indices", []))
        wrong_indices_json = json.dumps(result.get("wrong_indices", []))
        
        if existing:
            cursor.execute(
                """
                UPDATE analysis_results SET 
                    score = ?, percentage = ?, 
                    correct_indices = ?, wrong_indices = ?,
                    strengths = ?, weaknesses = ?, suggestions = ?
                WHERE id = ?
                """,
                (
                    result.get("score", "0/0"),
                    result.get("percentage", 0),
                    correct_indices_json,
                    wrong_indices_json,
                    result.get("strengths", ""),
                    result.get("weaknesses", ""),
                    result.get("suggestions", ""),
                    existing[0]
                )
            )
            result_id = existing[0]
            logger.info(f"Updated analysis result for student ID {student_id} with answer key ID {answer_key_id}")
        else:
            cursor.execute(
                """
                INSERT INTO analysis_results (
                    student_id, answer_key_id, score, percentage,
                    correct_indices, wrong_indices,
                    strengths, weaknesses, suggestions
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    student_id,
                    answer_key_id,
                    result.get("score", "0/0"),
                    result.get("percentage", 0),
                    correct_indices_json,
                    wrong_indices_json,
                    result.get("strengths", ""),
                    result.get("weaknesses", ""),
                    result.get("suggestions", "")
                )
            )
            result_id = cursor.lastrowid
            logger.info(f"Saved new analysis result for student ID {student_id} with answer key ID {answer_key_id}")
        
        cursor.execute(
            "UPDATE student_answers SET analyzed = 1 WHERE student_id = ? AND answer_key_id = ?",
            (student_id, answer_key_id)
        )
        
        conn.commit()
        conn.close()
        return result_id
    except Exception as e:
        logger.error(f"Error saving analysis result: {str(e)}")
        return None

def get_analysis_result(student_id, answer_key_id):
    """
    Get an analysis result from the database.
    
    Args:
        student_id: ID of the student
        answer_key_id: ID of the answer key
        
    Returns:
        Dictionary with analysis result, or None if not found
    """
    try:
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()
        
        cursor.execute(
            """
            SELECT id, score, percentage, correct_indices, wrong_indices,
                   strengths, weaknesses, suggestions, created_at
            FROM analysis_results
            WHERE student_id = ? AND answer_key_id = ?
            """,
            (student_id, answer_key_id)
        )
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                'id': row[0],
                'score': row[1],
                'percentage': row[2],
                'correct_indices': json.loads(row[3]),
                'wrong_indices': json.loads(row[4]),
                'strengths': row[5],
                'weaknesses': row[6],
                'suggestions': row[7],
                'created_at': row[8]
            }
        else:
            return None
    except Exception as e:
        logger.error(f"Error getting analysis result: {str(e)}")
        return None

def get_all_analysis_results(answer_key_id=None):
    try:
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()
        
        if answer_key_id is not None:
            cursor.execute(
                """
                SELECT ar.id, s.id, s.name, ar.answer_key_id, ar.score, ar.percentage,
                       ar.correct_indices, ar.wrong_indices,
                       ar.strengths, ar.weaknesses, ar.suggestions, ar.created_at
                FROM analysis_results ar
                JOIN students s ON ar.student_id = s.id
                WHERE ar.answer_key_id = ?
                ORDER BY s.name
                """,
                (answer_key_id,)
            )
        else:
            cursor.execute(
                """
                SELECT ar.id, s.id, s.name, ar.answer_key_id, ar.score, ar.percentage,
                       ar.correct_indices, ar.wrong_indices,
                       ar.strengths, ar.weaknesses, ar.suggestions, ar.created_at
                FROM analysis_results ar
                JOIN students s ON ar.student_id = s.id
                ORDER BY s.name
                """
            )
        
        rows = cursor.fetchall()
        conn.close()
        
        return [
            {
                'id': row[0],
                'student_id': row[1],
                'student_name': row[2],
                'answer_key_id': row[3],
                'score': row[4],
                'percentage': row[5],
                'correct_indices': json.loads(row[6]),
                'wrong_indices': json.loads(row[7]),
                'strengths': row[8],
                'weaknesses': row[9],
                'suggestions': row[10],
                'created_at': row[11]
            }
            for row in rows
        ]
    except Exception as e:
        logger.error(f"Error getting all analysis results: {str(e)}")
        return []

def generate_random_student_data(num_students=30, num_questions=60):
    try:
        from app.db.answer_key_db import get_all_answer_keys
        
        answer_keys = get_all_answer_keys()
        if not answer_keys:
            logger.error("No answer keys found. Please create at least one answer key first.")
            return False
        
        answer_key_id = answer_keys[0]['id']
        
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()
        
        first_names = [
            "James", "Mary", "John", "Patricia", "Robert", "Jennifer", "Michael", "Linda", 
            "William", "Elizabeth", "David", "Barbara", "Richard", "Susan", "Joseph", "Jessica", 
            "Thomas", "Sarah", "Charles", "Karen", "Christopher", "Nancy", "Daniel", "Lisa", 
            "Matthew", "Margaret", "Anthony", "Betty", "Mark", "Sandra", "Donald", "Ashley", 
            "Steven", "Kimberly", "Paul", "Emily", "Andrew", "Donna", "Joshua", "Michelle"
        ]
        
        last_names = [
            "Smith", "Johnson", "Williams", "Jones", "Brown", "Davis", "Miller", "Wilson", 
            "Moore", "Taylor", "Anderson", "Thomas", "Jackson", "White", "Harris", "Martin", 
            "Thompson", "Garcia", "Martinez", "Robinson", "Clark", "Rodriguez", "Lewis", "Lee", 
            "Walker", "Hall", "Allen", "Young", "Hernandez", "King", "Wright", "Lopez", 
            "Hill", "Scott", "Green", "Adams", "Baker", "Gonzalez", "Nelson", "Carter"
        ]
        
        for i in range(num_students):
            first_name = random.choice(first_names)
            last_name = random.choice(last_names)
            name = f"{first_name} {last_name}"
            
            cursor.execute("INSERT INTO students (name) VALUES (?)", (name,))
            student_id = cursor.lastrowid
            
            answers = {str(q): random.choice(['A', 'B', 'C', 'D']) for q in range(1, num_questions + 1)}
            answers_json = json.dumps(answers)
            
            cursor.execute(
                "INSERT INTO student_answers (student_id, answer_key_id, answers) VALUES (?, ?, ?)",
                (student_id, answer_key_id, answers_json)
            )
        
        conn.commit()
        conn.close()
        logger.info(f"Generated {num_students} random students with answers for {num_questions} questions")
        return True
    except Exception as e:
        logger.error(f"Error generating random student data: {str(e)}")
        return False

initialize_student_db()
