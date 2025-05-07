import logging
from app.db.answer_key_db import get_answer_key
from app.db.student_db import (
    get_all_students, get_all_student_answers, 
    save_analysis_result, get_all_analysis_results
)
from api.gemini_analysis import analyze_bubble_answers, analyze_class_performance

logger = logging.getLogger("chexam.api.analyze_all")
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('[%(levelname)s] %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

def analyze_student(student_id, answer_key_id):
    from app.db.student_db import get_student, get_student_answers
    
    student = get_student(student_id=student_id)
    if not student:
        logger.error(f"Student with ID {student_id} not found")
        return None
    
    student_answers_data = get_student_answers(student_id, answer_key_id)
    if not student_answers_data:
        logger.error(f"No answers found for student ID {student_id} and answer key ID {answer_key_id}")
        return None
    
    answer_key = get_answer_key(key_id=answer_key_id)
    if not answer_key:
        logger.error(f"Answer key with ID {answer_key_id} not found")
        return None
    
    result = analyze_bubble_answers(
        answer_key['answers'],
        student_answers_data,
        student_name=student['name']
    )
    
    if result:
        save_analysis_result(student_id, answer_key_id, result)
        logger.info(f"Analysis complete for student {student['name']}")
        
        result['student_name'] = student['name']
        return result
    else:
        logger.error(f"Failed to analyze answers for student {student['name']}")
        return None

def analyze_all_students(answer_key_id=None):
    if answer_key_id is None:
        from app.db.answer_key_db import get_all_answer_keys
        answer_keys = get_all_answer_keys()
        if not answer_keys:
            logger.error("No answer keys found. Please create at least one answer key first.")
            return []
        answer_key_id = answer_keys[0]['id']
    
    students = get_all_students()
    if not students:
        logger.error("No students found. Please add some students first.")
        return []
    
    student_answers = get_all_student_answers(answer_key_id)
    if not student_answers:
        logger.error(f"No student answers found for answer key ID {answer_key_id}")
        return []
    
    results = []
    for student in students:
        has_answers = any(sa['student_id'] == student['id'] for sa in student_answers)
        if not has_answers:
            logger.info(f"Skipping student {student['name']} - no answers for this answer key")
            continue
        
        result = analyze_student(student['id'], answer_key_id)
        if result:
            results.append(result)
    
    logger.info(f"Completed analysis for {len(results)} students")
    return results

def analyze_class(answer_key_id=None):
    if answer_key_id is None:
        from app.db.answer_key_db import get_all_answer_keys
        answer_keys = get_all_answer_keys()
        if not answer_keys:
            logger.error("No answer keys found. Please create at least one answer key first.")
            return None
        answer_key_id = answer_keys[0]['id']
    
    answer_key = get_answer_key(key_id=answer_key_id)
    if not answer_key:
        logger.error(f"Answer key with ID {answer_key_id} not found")
        return None
    
    analyze_all_students(answer_key_id)
    
    analysis_results = get_all_analysis_results(answer_key_id)
    if not analysis_results:
        logger.error(f"No analysis results found for answer key ID {answer_key_id}")
        return None
    
    result = analyze_class_performance(analysis_results, answer_key_name=answer_key['name'])
    if result:
        logger.info(f"Class analysis complete for answer key '{answer_key['name']}'")
        return result
    else:
        logger.error(f"Failed to analyze class performance for answer key '{answer_key['name']}'")
        return None
