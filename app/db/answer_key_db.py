import sqlite3
import os
import json
import logging
from pathlib import Path

logger = logging.getLogger("chexam.db.answer_key_db")
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('[%(levelname)s] %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

DB_PATH = Path(os.path.dirname(os.path.abspath(__file__))) / ".." / ".." / "data" / "chexam.db"
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

def initialize_db():
    try:
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS answer_keys (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            num_questions INTEGER NOT NULL,
            answers TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        conn.commit()
        conn.close()
        logger.info(f"Database initialized at {DB_PATH}")
        return True
    except Exception as e:
        logger.error(f"Error initializing database: {str(e)}")
        return False

def save_answer_key(name, num_questions, answers):

    try:
        answers_json = json.dumps(answers)
        
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()
        
        cursor.execute("SELECT id FROM answer_keys WHERE name = ?", (name,))
        existing = cursor.fetchone()
        
        if existing:
            cursor.execute(
                "UPDATE answer_keys SET num_questions = ?, answers = ? WHERE name = ?",
                (num_questions, answers_json, name)
            )
            key_id = existing[0]
            logger.info(f"Updated answer key '{name}' with ID {key_id}")
        else:
            cursor.execute(
                "INSERT INTO answer_keys (name, num_questions, answers) VALUES (?, ?, ?)",
                (name, num_questions, answers_json)
            )
            key_id = cursor.lastrowid
            logger.info(f"Saved new answer key '{name}' with ID {key_id}")
        
        conn.commit()
        conn.close()
        return key_id
    except Exception as e:
        logger.error(f"Error saving answer key: {str(e)}")
        return None

def get_answer_key(key_id=None, name=None):

    try:
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()
        
        if key_id is not None:
            cursor.execute("SELECT * FROM answer_keys WHERE id = ?", (key_id,))
        elif name is not None:
            cursor.execute("SELECT * FROM answer_keys WHERE name = ?", (name,))
        else:
            logger.error("Either key_id or name must be provided")
            conn.close()
            return None
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                'id': row[0],
                'name': row[1],
                'num_questions': row[2],
                'answers': json.loads(row[3]),
                'created_at': row[4]
            }
        else:
            return None
    except Exception as e:
        logger.error(f"Error getting answer key: {str(e)}")
        return None

def get_all_answer_keys():

    try:
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()
        
        cursor.execute("SELECT id, name, num_questions, created_at FROM answer_keys ORDER BY name")
        rows = cursor.fetchall()
        conn.close()
        
        return [
            {
                'id': row[0],
                'name': row[1],
                'num_questions': row[2],
                'created_at': row[3]
            }
            for row in rows
        ]
    except Exception as e:
        logger.error(f"Error getting all answer keys: {str(e)}")
        return []

def delete_answer_key(key_id=None, name=None):

    try:
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()
        
        if key_id is not None:
            cursor.execute("DELETE FROM answer_keys WHERE id = ?", (key_id,))
        elif name is not None:
            cursor.execute("DELETE FROM answer_keys WHERE name = ?", (name,))
        else:
            logger.error("Either key_id or name must be provided")
            conn.close()
            return False
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"Error deleting answer key: {str(e)}")
        return False

def get_answer_key_answers(key_id):
    try:
        answer_key = get_answer_key(key_id=key_id)
        
        if answer_key and 'answers' in answer_key:
            return answer_key['answers']
        else:
            logger.warning(f"No answers found for answer key ID {key_id}")
            return {}
    except Exception as e:
        logger.error(f"Error getting answer key answers: {str(e)}")
        return {}

initialize_db()
