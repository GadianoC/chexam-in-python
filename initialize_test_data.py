import logging
import sys
from api.init_students import initialize_students
from api.analyze_all import analyze_all_students, analyze_class
from app.db.answer_key_db import get_all_answer_keys

logging.basicConfig(
    level=logging.INFO,
    format='[%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("chexam.initialize_test_data")

def main():
    answer_keys = get_all_answer_keys()
    if not answer_keys:
        logger.error("No answer keys found. Please create at least one answer key first.")
        return False
    
    answer_key_id = answer_keys[0]['id']
    answer_key_name = answer_keys[0]['name']
    
    logger.info(f"Initializing 30 example students for answer key '{answer_key_name}'...")
    if not initialize_students(30, 60):
        logger.error("Failed to initialize students.")
        return False
    
    logger.info("Analyzing all students...")
    results = analyze_all_students(answer_key_id)
    if not results:
        logger.error("Failed to analyze students.")
        return False
    
    logger.info(f"Successfully analyzed {len(results)} students.")
    
    logger.info("Analyzing class performance...")
    class_result = analyze_class(answer_key_id)
    if not class_result:
        logger.error("Failed to analyze class performance.")
        return False
    
    logger.info("Class analysis complete!")
    logger.info(f"Class average: {class_result.get('class_average')}%")
    logger.info(f"Passing rate: {class_result.get('passing_rate')}%")
    
    logger.info("Test data initialization complete!")
    return True

if __name__ == "__main__":
    main()
