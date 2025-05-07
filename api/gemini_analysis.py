import os
import json
import logging
import requests
import random
import math
import os
from collections import Counter
from dotenv import load_dotenv

logger = logging.getLogger("chexam.api.gemini_analysis")
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('[%(levelname)s] %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1/models/gemini-1.0-pro:generateContent"
USE_MOCK_ANALYSIS = True

if not API_KEY:
    logger.warning("Gemini API key not found in environment variables. Set GEMINI_API_KEY to use Gemini API.")
    USE_MOCK_ANALYSIS = True
else:
    logger.info("Gemini API key found in environment variables")
    
def mock_analyze_student(correct_answers, student_answers, student_name):
    correct_indices = []
    wrong_indices = []
    
    for q_num, correct_option in correct_answers.items():
        if q_num in student_answers and student_answers[q_num] == correct_option:
            correct_indices.append(q_num)
        else:
            wrong_indices.append(q_num)
    
    total_questions = len(correct_answers)
    correct_count = len(correct_indices)
    percentage = round((correct_count / total_questions) * 100, 1) if total_questions > 0 else 0
    score = f"{correct_count}/{total_questions}"
    
    strengths = generate_mock_strengths(correct_indices, correct_answers)
    weaknesses = generate_mock_weaknesses(wrong_indices, correct_answers)
    suggestions = generate_mock_suggestions(percentage, wrong_indices)
    
    return {
        "score": score,
        "percentage": percentage,
        "correct_indices": correct_indices,
        "wrong_indices": wrong_indices,
        "strengths": strengths,
        "weaknesses": weaknesses,
        "suggestions": suggestions
    }

def generate_mock_strengths(correct_indices, correct_answers):
    if not correct_indices:
        return "No particular strengths identified."
    
    # Group questions by tens
    groups = {}
    for q in correct_indices:
        group = (int(q) - 1) // 10
        groups[group] = groups.get(group, 0) + 1
    
    # Find the strongest group
    strongest_group = max(groups.items(), key=lambda x: x[1], default=(0, 0))
    group_start = strongest_group[0] * 10 + 1
    group_end = min((strongest_group[0] + 1) * 10, 60)
    
    strength_templates = [
        f"Strong performance in questions {group_start}-{group_end}.",
        f"Good understanding of concepts tested in questions {group_start}-{group_end}.",
        f"Demonstrated proficiency in the topics covered in questions {group_start}-{group_end}."
    ]
    
    return random.choice(strength_templates)

def generate_mock_weaknesses(wrong_indices, correct_answers):
    if not wrong_indices:
        return "No significant weaknesses identified."
    
    # Group questions by tens
    groups = {}
    for q in wrong_indices:
        group = (int(q) - 1) // 10
        groups[group] = groups.get(group, 0) + 1
    
    # Find the weakest group
    weakest_group = max(groups.items(), key=lambda x: x[1], default=(0, 0))
    group_start = weakest_group[0] * 10 + 1
    group_end = min((weakest_group[0] + 1) * 10, 60)
    
    weakness_templates = [
        f"Struggled with questions {group_start}-{group_end}.",
        f"Needs improvement in concepts tested in questions {group_start}-{group_end}.",
        f"Difficulty with the topics covered in questions {group_start}-{group_end}."
    ]
    
    return random.choice(weakness_templates)

def generate_mock_suggestions(percentage, wrong_indices):
    if percentage >= 90:
        return "Continue with current study methods. Consider helping peers who are struggling."
    
    if percentage >= 70:
        return "Review the questions you missed and focus on those specific topics."
    
    if percentage >= 50:
        return "Dedicate more time to studying the sections where you missed multiple questions."
    
    return "Consider seeking additional help or tutoring for the topics covered in this test."

def mock_analyze_class(analysis_results, answer_key_name):
    if not analysis_results:
        return None
    
    percentages = [result.get("percentage", 0) for result in analysis_results]
    class_average = round(sum(percentages) / len(percentages), 1) if percentages else 0
    passing_count = sum(1 for p in percentages if p >= 60)
    passing_rate = round((passing_count / len(percentages)) * 100, 1) if percentages else 0
    
    highest_score = max(percentages) if percentages else 0
    lowest_score = min(percentages) if percentages else 0
    
    all_correct = []
    all_wrong = []
    
    for result in analysis_results:
        all_correct.extend(result.get("correct_indices", []))
        all_wrong.extend(result.get("wrong_indices", []))
    
    correct_counter = Counter(all_correct)
    wrong_counter = Counter(all_wrong)
    
    most_missed = [q for q, _ in wrong_counter.most_common(5)]
    best_understood = [q for q, _ in correct_counter.most_common(5)]
    
    class_strengths = generate_mock_class_strengths(best_understood, class_average)
    class_weaknesses = generate_mock_class_weaknesses(most_missed, class_average)
    teaching_suggestions = generate_mock_teaching_suggestions(class_average, passing_rate, most_missed)
    
    return {
        "class_average": class_average,
        "passing_rate": passing_rate,
        "highest_score": highest_score,
        "lowest_score": lowest_score,
        "most_missed_questions": most_missed,
        "best_understood_questions": best_understood,
        "class_strengths": class_strengths,
        "class_weaknesses": class_weaknesses,
        "teaching_suggestions": teaching_suggestions
    }

def generate_mock_class_strengths(best_understood, class_average):
    if not best_understood:
        return "No particular class strengths identified."
    
    # Group questions by tens
    groups = {}
    for q in best_understood:
        group = (int(q) - 1) // 10
        groups[group] = groups.get(group, 0) + 1
    
    # Find the strongest group
    strongest_group = max(groups.items(), key=lambda x: x[1], default=(0, 0))
    group_start = strongest_group[0] * 10 + 1
    group_end = min((strongest_group[0] + 1) * 10, 60)
    topic_area = f"questions {group_start}-{group_end}"
    
    if class_average >= 80:
        return f"The class demonstrates excellent understanding of {topic_area}."
    elif class_average >= 60:
        return f"The class shows good grasp of {topic_area}."
    else:
        return f"Despite overall challenges, the class performed relatively well in {topic_area}."

def generate_mock_class_weaknesses(most_missed, class_average):
    if not most_missed:
        return "No significant class weaknesses identified."
    
    groups = {}
    for q in most_missed:
        group = (int(q) - 1) // 10
        groups[group] = groups.get(group, 0) + 1
    
    weakest_group = max(groups.items(), key=lambda x: x[1], default=(0, 0))
    group_start = weakest_group[0] * 10 + 1
    group_end = min((weakest_group[0] + 1) * 10, 60)
    topic_area = f"questions {group_start}-{group_end}"
    
    if class_average < 60:
        return f"The class struggled significantly with {topic_area}."
    elif class_average < 80:
        return f"The class needs additional support with {topic_area}."
    else:
        return f"While overall performance was strong, some students had difficulty with {topic_area}."

def generate_mock_teaching_suggestions(class_average, passing_rate, most_missed):
    if class_average >= 80 and passing_rate >= 90:
        return "The class is performing well. Consider introducing more advanced material or enrichment activities."
    
    if class_average >= 70:
        return "Review the most commonly missed questions with the entire class and provide targeted practice."
    
    if class_average >= 60:
        return "Consider re-teaching concepts from the sections with the most missed questions and provide additional practice opportunities."
    
    return "A comprehensive review of the material is recommended. Consider alternative teaching methods and providing additional support resources."

def analyze_bubble_answers(correct_answers, student_answers, student_name="Student"):
    if USE_MOCK_ANALYSIS or not API_KEY:
        logger.info(f"Using mock analysis for {student_name}")
        return mock_analyze_student(correct_answers, student_answers, student_name)
        
    prompt = f"""
    Analyze {student_name}'s answers on a multiple-choice test and return a JSON with:
    {{
      "score": "x/y", 
      "percentage": number, 
      "correct_indices": [list of question numbers], 
      "wrong_indices": [list of question numbers], 
      "strengths": "short summary", 
      "weaknesses": "short summary", 
      "suggestions": "short summary" 
    }}

    Correct Answers: {correct_answers}
    Student Answers: {student_answers}
    
    Make sure your response is ONLY the JSON object with no additional text.
    """

    try:
        logger.info(f"Analyzing answers for {student_name} using Gemini API...")
        
        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": prompt}
                    ]
                }
            ],
            "generationConfig": {
                "temperature": 0.2,
                "topK": 32,
                "topP": 0.95,
                "maxOutputTokens": 1024,
            }
        }
        
        response = requests.post(
            f"{GEMINI_API_URL}?key={API_KEY}",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code != 200:
            logger.error(f"API request failed with status code {response.status_code}: {response.text}")
            logger.info(f"Falling back to mock analysis for {student_name}")
            return mock_analyze_student(correct_answers, student_answers, student_name)
            
        response_data = response.json()
        
        if not response_data.get("candidates"):
            logger.error("No candidates in API response")
            logger.info(f"Falling back to mock analysis for {student_name}")
            return mock_analyze_student(correct_answers, student_answers, student_name)
            
        response_text = ""
        for part in response_data["candidates"][0]["content"]["parts"]:
            if "text" in part:
                response_text += part["text"]
        
        response_text = response_text.strip()
        
        if response_text.startswith("```json") and response_text.endswith("```"):
            response_text = response_text[7:-3].strip()
        elif response_text.startswith("```") and response_text.endswith("```"):
            response_text = response_text[3:-3].strip()
            
        result = json.loads(response_text)
        
        required_fields = ["score", "percentage", "correct_indices", "wrong_indices", 
                          "strengths", "weaknesses", "suggestions"]
        for field in required_fields:
            if field not in result:
                result[field] = "" if field in ["strengths", "weaknesses", "suggestions"] else []
                
        if isinstance(result["percentage"], str):
            try:
                result["percentage"] = float(result["percentage"].strip("%"))
            except:
                result["percentage"] = 0.0
                
        logger.info(f"Analysis complete for {student_name}")
        return result
    except Exception as e:
        logger.error(f"Error analyzing answers for {student_name}: {str(e)}")
        if 'response' in locals():
            logger.error(f"API response: {response.text}")
        logger.info(f"Falling back to mock analysis for {student_name}")
        return mock_analyze_student(correct_answers, student_answers, student_name)

def analyze_class_performance(analysis_results, answer_key_name="Answer Key"):
    if not analysis_results:
        logger.error("No analysis results provided for class analysis")
        return None
    
    if USE_MOCK_ANALYSIS or not API_KEY:
        logger.info(f"Using mock analysis for class with answer key '{answer_key_name}'")
        return mock_analyze_class(analysis_results, answer_key_name)
        
    class_summary = {
        "student_count": len(analysis_results),
        "average_score": sum(r.get("percentage", 0) for r in analysis_results) / len(analysis_results) if analysis_results else 0,
        "passing_rate": sum(1 for r in analysis_results if r.get("percentage", 0) >= 60) / len(analysis_results) * 100 if analysis_results else 0,
    }
    
    all_correct = []
    all_wrong = []
    for result in analysis_results:
        all_correct.extend(result.get("correct_indices", []))
        all_wrong.extend(result.get("wrong_indices", []))
    
    correct_counter = Counter(all_correct)
    wrong_counter = Counter(all_wrong)
    
    most_missed = [q for q, _ in wrong_counter.most_common(5)]
    best_understood = [q for q, _ in correct_counter.most_common(5)]
    
    class_summary["most_missed_questions"] = most_missed
    class_summary["best_understood_questions"] = best_understood
    
    try:
        student_data = []
        for result in analysis_results:
            student_data.append({
                "name": result.get("student_name", "Student"),
                "score": result.get("score", "0/0"),
                "percentage": result.get("percentage", 0),
                "correct_indices": result.get("correct_indices", []),
                "wrong_indices": result.get("wrong_indices", [])
            })
            
        prompt = f"""
        Analyze the performance of a class of {len(student_data)} students on the "{answer_key_name}" test.
        Here's the data for each student:
        {json.dumps(student_data, indent=2)}
        
        Return a JSON with:
        {{
          "class_average": number,
          "passing_rate": number,
          "highest_score": number,
          "lowest_score": number,
          "most_missed_questions": [list of question numbers],
          "best_understood_questions": [list of question numbers],
          "class_strengths": "short summary",
          "class_weaknesses": "short summary",
          "teaching_suggestions": "short summary"
        }}
        
        Make sure your response is ONLY the JSON object with no additional text.
        """

        logger.info(f"Analyzing class performance for {len(student_data)} students using Gemini API...")
        
        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": prompt}
                    ]
                }
            ],
            "generationConfig": {
                "temperature": 0.2,
                "topK": 32,
                "topP": 0.95,
                "maxOutputTokens": 1024,
            }
        }
        
        response = requests.post(
            f"{GEMINI_API_URL}?key={API_KEY}",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code != 200:
            logger.error(f"API request failed with status code {response.status_code}: {response.text}")
            logger.info("Falling back to mock analysis for class performance")
            return mock_analyze_class(analysis_results, answer_key_name)
            
        response_data = response.json()
        
        if not response_data.get("candidates"):
            logger.error("No candidates in API response")
            logger.info("Falling back to mock analysis for class performance")
            return mock_analyze_class(analysis_results, answer_key_name)
            
        response_text = ""
        for part in response_data["candidates"][0]["content"]["parts"]:
            if "text" in part:
                response_text += part["text"]
        
        response_text = response_text.strip()
        
        if response_text.startswith("```json") and response_text.endswith("```"):
            response_text = response_text[7:-3].strip()
        elif response_text.startswith("```") and response_text.endswith("```"):
            response_text = response_text[3:-3].strip()
            
        result = json.loads(response_text)
        
        required_fields = ["class_average", "passing_rate", "highest_score", "lowest_score", 
                          "most_missed_questions", "best_understood_questions", 
                          "class_strengths", "class_weaknesses", "teaching_suggestions"]
        for field in required_fields:
            if field not in result:
                result[field] = "" if field in ["class_strengths", "class_weaknesses", "teaching_suggestions"] else []
                
        for field in ["class_average", "passing_rate", "highest_score", "lowest_score"]:
            if isinstance(result[field], str):
                try:
                    result[field] = float(result[field].strip("%"))
                except:
                    result[field] = 0.0
                    
        logger.info("Class performance analysis complete")
        return result
    except Exception as e:
        logger.error(f"Error analyzing class performance: {str(e)}")
        if 'response' in locals():
            logger.error(f"API response: {response.text}")
        logger.info("Falling back to mock analysis for class performance")
        return mock_analyze_class(analysis_results, answer_key_name)
    except Exception as e:
        logger.error(f"Error analyzing class performance: {str(e)}")
        if 'response' in locals():
            logger.error(f"API response: {response.text}")
        logger.info("Falling back to mock analysis for class performance")
        return mock_analyze_class(analysis_results, answer_key_name)
