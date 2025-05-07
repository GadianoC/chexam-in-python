import logging
from app.db.student_db import generate_random_student_data

# Set up logging
logger = logging.getLogger("chexam.api.init_students")
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('[%(levelname)s] %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

def initialize_students(num_students=30, num_questions=60):

    logger.info(f"Initializing database with {num_students} random students...")
    success = generate_random_student_data(num_students, num_questions)
    
    if success:
        logger.info("Student initialization complete!")
        return True
    else:
        logger.error("Failed to initialize students")
        return False

if __name__ == "__main__":
    initialize_students()
