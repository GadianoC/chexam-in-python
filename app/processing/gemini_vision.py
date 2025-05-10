import logging
import cv2
import numpy as np
from pathlib import Path
import base64
from io import BytesIO
import json
import re
import asyncio
import requests
import time
import os
from typing import Dict, List, Tuple, Optional, Any, Union

# Import secure storage for API keys
try:
    from ..utils.secure_storage import get_api_key, GEMINI_API_KEY as GEMINI_KEY_NAME
    SECURE_STORAGE_AVAILABLE = True
except ImportError:
    SECURE_STORAGE_AVAILABLE = False
    print("WARNING: secure_storage module not found. Falling back to environment variables.")

# Fallback to dotenv if needed
try:
    from dotenv import load_dotenv
    DOTENV_AVAILABLE = True
except ImportError:
    load_dotenv = lambda: None  
    DOTENV_AVAILABLE = False
    print("WARNING: python-dotenv module not found. Environment variables will not be loaded from .env file.")

GEMINI_AVAILABLE = False

logger = logging.getLogger("chexam.gemini_vision")
if not logger.handlers:
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(handler)

# Try to get API key from secure storage first
api_key = None
if SECURE_STORAGE_AVAILABLE:
    api_key = get_api_key(GEMINI_KEY_NAME)
    if api_key:
        GEMINI_AVAILABLE = True
        logger.info("Gemini API key found in secure storage")

# Fall back to environment variables if needed
if not api_key:
    if DOTENV_AVAILABLE:
        load_dotenv()
    
    api_key = os.environ.get("GEMINI_API_KEY")
    if api_key:
        GEMINI_AVAILABLE = True
        logger.info("Gemini API key found in environment variables")
    else:
        logger.warning("Gemini API key not found. Please add your API key in the Settings screen.")


GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro-vision:generateContent"

def optimize_image_for_gemini(image: np.ndarray) -> bytes:
    """
    Optimize an image for the Gemini Vision API by enhancing contrast, resizing and compressing it.
    
    Args:
        image: OpenCV image (numpy array)
        
    Returns:
        Bytes of the optimized JPEG image
    """
    img_enhanced = image.copy()
    
    if len(img_enhanced.shape) == 3:
        img_gray = cv2.cvtColor(img_enhanced, cv2.COLOR_BGR2GRAY)
    else:
        img_gray = img_enhanced.copy()
    
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    img_enhanced = clahe.apply(img_gray)
    
    img_enhanced = cv2.GaussianBlur(img_enhanced, (3, 3), 0)
    
    img_enhanced = cv2.adaptiveThreshold(
        img_enhanced, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 11, 2
    )
    
    
    img_enhanced = cv2.cvtColor(img_enhanced, cv2.COLOR_GRAY2BGR)
    
    max_dim = 1024
    height, width = img_enhanced.shape[:2]
    
    if max(height, width) > max_dim:
        scale = max_dim / max(height, width)
        new_width = int(width * scale)
        new_height = int(height * scale)
        img_enhanced = cv2.resize(img_enhanced, (new_width, new_height))
    
    encode_params = [int(cv2.IMWRITE_JPEG_QUALITY), 90]  
    _, img_bytes = cv2.imencode('.jpg', img_enhanced, encode_params)
    
    cv2.imwrite(f"gemini_enhanced_{int(time.time())}.png", img_enhanced)
    
    return img_bytes.tobytes()

def prepare_image_for_api(image: np.ndarray) -> Optional[Dict[str, str]]:
    """
    Prepare an image for the Gemini Vision API by optimizing and encoding it.
    
    Args:
        image: OpenCV image (numpy array)
        
    Returns:
        Dictionary with mime_type and base64-encoded image data, or None if Gemini is not available
    """
    if not GEMINI_AVAILABLE:
        logger.error("Cannot prepare image for API: Gemini is not available")
        return None
        
    img_bytes = optimize_image_for_gemini(image)
    
    return {
        "mime_type": "image/jpeg",
        "data": base64.b64encode(img_bytes).decode('utf-8')
    }

def detect_bubble_grid(image: np.ndarray) -> Dict[str, Any]:
    """
    Detect the bubble grid structure in the image.
    
    Args:
        image: OpenCV image (numpy array)
        
    Returns:
        Dictionary with grid information
    """
    grid_info = {
        "detected": False,
        "rows": 0,
        "columns": 0,
        "bubbles": []
    }
    
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image.copy()
    
    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    bubbles = []
    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)
        
        aspect_ratio = w / h
        if 0.8 <= aspect_ratio <= 1.2 and 10 <= w <= 50 and 10 <= h <= 50:
            bubbles.append((x, y, w, h))
    
    if len(bubbles) > 20:
        bubbles.sort(key=lambda b: b[1])
        
        row_y = []
        prev_y = -100
        for _, y, _, h in bubbles:
            center_y = y + h/2
            if abs(center_y - prev_y) > h/2:
                row_y.append(center_y)
                prev_y = center_y
        
        bubbles.sort(key=lambda b: b[0])
        
        col_x = []
        prev_x = -100
        for x, _, w, _ in bubbles:
            center_x = x + w/2
            if abs(center_x - prev_x) > w/2:
                col_x.append(center_x)
                prev_x = center_x
        
        grid_info["detected"] = True
        grid_info["rows"] = len(row_y)
        grid_info["columns"] = len(col_x)
        grid_info["bubbles"] = bubbles
    
    return grid_info

def create_spatial_reference_prompt(grid_info: Dict[str, Any], num_questions: int) -> str:
    """
    Create a spatial reference prompt based on the detected grid.
    
    Args:
        grid_info: Dictionary with grid information
        num_questions: Number of questions on the sheet
        
    Returns:
        Spatial reference prompt string
    """
    if not grid_info["detected"]:
        return "I couldn't detect a clear bubble grid structure in the image."
    
    return f"""
    SPATIAL REFERENCE:
    - I can see a grid with approximately {grid_info['rows']} rows and {grid_info['columns']} columns of bubbles.
    - There are {num_questions} questions on this sheet.
    - Each row likely represents one question with multiple choice options.
    - The bubbles are arranged in a grid pattern.
    """

def visualize_bubble_detection(image: np.ndarray, grid_info: Dict[str, Any]) -> Optional[np.ndarray]:
    """
    Create a visualization of the detected bubble grid.
    
    Args:
        image: OpenCV image (numpy array)
        grid_info: Dictionary with grid information
        
    Returns:
        Visualization image or None if no grid was detected
    """
    if not grid_info["detected"]:
        return None
    
    vis_image = image.copy()
    
    for x, y, w, h in grid_info["bubbles"]:
        cv2.rectangle(vis_image, (x, y), (x+w, y+h), (0, 255, 0), 2)
    
    return vis_image

async def process_bubble_sheet(image: np.ndarray, num_questions: int = 60, debug: bool = False) -> Optional[Dict[str, str]]:
    """
    Process a bubble sheet image using Gemini Vision API with enhanced spatial understanding.
    Uses direct API calls instead of the Google Generative AI package.
    
    Args:
        image: OpenCV image (numpy array)
        num_questions: Number of questions on the sheet (default: 60)
        debug: Whether to log debug information
        
    Returns:
        Dictionary with question numbers as keys and selected options as values
        (A, B, C, D or blank for no/multiple selections)
    """
    if not GEMINI_AVAILABLE:
        logger.error("Cannot process bubble sheet: Gemini Vision API is not available")
        logger.error("Please set your GEMINI_API_KEY in the .env file")
        return None
    
    try:
        grid_info = detect_bubble_grid(image)
        if debug and grid_info["detected"]:
            logger.debug(f"Detected bubble grid with {grid_info['rows']} rows and {grid_info['columns']} columns")
        
        spatial_prompt = create_spatial_reference_prompt(grid_info, num_questions)
        
        image_part = prepare_image_for_api(image)
        if image_part is None:
            return None
            
        if debug:
            vis_image = visualize_bubble_detection(image, grid_info)
            if vis_image is not None:
                debug_path = f"gemini_analysis_{int(time.time())}_bubble_detection.png"
                cv2.imwrite(debug_path, vis_image)
                logger.debug(f"Saved bubble detection visualization to {debug_path}")
        
        prompt = f"""
        You are an expert in analyzing bubble sheet (OMR) answer forms. 
        
        TASK: Analyze this bubble sheet image and identify which bubbles are filled in for each question.
        
        IMPORTANT DETAILS:
        - The image contains a multiple-choice answer sheet with questions numbered from 1 to {num_questions}.
        - Each question has options A, B, C, and D arranged horizontally.
        - Questions are numbered from top to bottom (1 at the top, increasing as you go down).
        - Bubbles are organized in a grid pattern with 4 columns (A, B, C, D) and {num_questions} rows.
        - A bubble is considered marked if it appears darker than the surrounding bubbles.
        - Even partially filled bubbles should be considered as marked.
        - The image may be low contrast - look carefully for subtle differences in shading.
        - Some bubbles may be lightly filled - any darkening compared to empty bubbles should be considered as marked.
        
        {spatial_prompt}
        
        ANALYSIS INSTRUCTIONS:
        1. Carefully examine each row of bubbles (each question).
        2. For each question (1-{num_questions}), determine which option (A, B, C, or D) is marked.
        3. If no option is marked or multiple options are marked for a question, indicate "blank".
        4. The bubbles may appear as circles or ovals and may be filled with pencil or pen.
        5. Focus on the relative darkness/lightness of each bubble to determine if it's filled.
        6. The image might be slightly rotated or skewed - adjust your analysis accordingly.
        7. You MUST identify answers for ALL questions from 1 to {num_questions}.
        8. Pay extra attention to subtle differences in shading - even lightly filled bubbles should be detected.
        9. If you're unsure about a bubble, compare it to definitely empty bubbles to see if there's any difference.
        
        FORMAT YOUR RESPONSE AS JSON ONLY:
        {{
          "1": "A",
          "2": "blank",
          "3": "C",
          "4": "D",
          ... (continue for all questions)
        }}
        
        IMPORTANT: Your response must ONLY contain a JSON object with question numbers as keys and answers as values.
        Do not include any explanations, comments, or additional text outside the JSON structure.
        """
        
        if debug:
            logger.debug(f"Sending image to Gemini Vision API with enhanced spatial understanding prompt")
        
        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": prompt},
                        {"inline_data": image_part}
                    ]
                }
            ],
            "generation_config": {
                "temperature": 0.1,
                "top_p": 0.95,
                "top_k": 40,
                "max_output_tokens": 2048,
            }
        }
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        
        response = await asyncio.to_thread(
            requests.post,
            f"{GEMINI_API_URL}?key={api_key}",
            headers=headers,
            json=payload
        )
        
        if response.status_code != 200:
            logger.error(f"Gemini API request failed with status code {response.status_code}")
            logger.error(f"Response: {response.text}")
            return None
        
        response_json = response.json()
        
        try:
            try:
                response_text = response_json["candidates"][0]["content"]["parts"][0]["text"]
            except (KeyError, IndexError) as e:
                logger.error(f"Failed to extract text from Gemini API response: {str(e)}")
                logger.error(f"Response: {response_json}")
                return None
            
            logger.debug(f"Raw response from Gemini: {response_text}")
            
            answers = {}
            
            import re
            
            json_match = re.search(r'\{[\s\S]*?\}', response_text)
            
            if json_match:
                json_str = json_match.group(0)
                logger.debug(f"Extracted JSON string: {json_str}")
                
                try:
                    answers = json.loads(json_str)
                    logger.info(f"Successfully extracted {len(answers)} answers from Gemini Vision API")
                except json.JSONDecodeError as e:
                    logger.error(f"Error parsing JSON from Gemini response: {str(e)}")
                    logger.error(f"JSON string that failed to parse: {json_str}")
                    
                    try:
                        clean_json = re.sub(r'[^{}\[\]:,"\d\w\s.-]', '', json_str)
                        clean_json = clean_json.replace("'", '"')
                        clean_json = re.sub(r',\s*\}', '}', clean_json)
                        clean_json = re.sub(r',\s*\]', ']', clean_json)
                        clean_json = re.sub(r'//.*?\n', '', clean_json)
                        clean_json = re.sub(r'/\*.*?\*/', '', clean_json, flags=re.DOTALL)
                        
                        answers = json.loads(clean_json)
                        logger.info(f"Successfully extracted {len(answers)} answers after cleanup")
                    except json.JSONDecodeError as e:
                        logger.error(f"Failed to parse JSON even after cleanup: {str(e)}")
                        
                        try:
                            pairs = re.findall(r'"(\d+)"\s*:\s*"([A-Da-d]|blank)"', json_str)
                            if pairs:
                                for q_num, answer in pairs:
                                    answers[q_num] = answer.upper()
                                logger.info(f"Successfully extracted {len(answers)} answers using regex pattern matching")
                        except Exception as e:
                            logger.error(f"Failed to extract answers using regex: {str(e)}")
            
            if not answers:
                try:
                    pairs = re.findall(r'"(\d+)"\s*:\s*"([A-Da-d]|blank)"', response_text)
                    if pairs:
                        for q_num, answer in pairs:
                            answers[q_num] = answer.upper()
                        logger.info(f"Successfully extracted {len(answers)} answers using regex pattern matching on full text")
                except Exception as e:
                    logger.error(f"Failed to extract answers using regex on full text: {str(e)}")
                    
            
            if not answers:
                logger.debug("Attempting to extract answers line by line")
                lines = response_text.strip().split('\n')
                for line in lines:
                    match = re.search(r'(?:Question\s*)?"?(\d+)"?\s*[:.]?\s*"?([A-Da-d]|blank)"?', line)
                    if match:
                        q_num, answer = match.groups()
                        answers[q_num] = answer.upper()
                
                if answers:
                    logger.debug(f"Extracted {len(answers)} answers from line-by-line parsing")
            
            if debug:
                debug_path = f"gemini_content_{int(time.time())}.txt"
                with open(debug_path, 'w') as f:
                    f.write(response_text)
                logger.debug(f"Saved Gemini response to {debug_path}")
                
                if answers:
                    vis_image = image.copy()
                    for q_num, answer in sorted(answers.items(), key=lambda x: int(x[0])):
                        y_pos = 30 + (int(q_num) - 1) * 30
                        cv2.putText(vis_image, f"Q{q_num}: {answer}", (10, y_pos), 
                                  cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                    
                    debug_path = f"gemini_content_{int(time.time())}_bubble_detection.png"
                    cv2.imwrite(debug_path, vis_image)
                    logger.debug(f"Saved answer visualization to {debug_path}")
            
            formatted_answers = {}
            for i in range(1, num_questions + 1):
                question_key = str(i)
                if question_key in answers:
                    answer = answers[question_key].upper()
                    if answer in ['A', 'B', 'C', 'D']:
                        formatted_answers[question_key] = answer
                    else:
                        formatted_answers[question_key] = "blank"
                else:
                    formatted_answers[question_key] = "blank"
                    
            result = {
                "answers": formatted_answers,
                "score": 0,
                "percentage": 0,
                "summary": "No answer key available for comparison"
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error parsing Gemini response: {str(e)}")
            if 'response_text' in locals():
                logger.error(f"Response text: {response_text}")
            if debug and 'response_text' in locals():
                debug_path = f"gemini_error_{int(time.time())}.txt"
                with open(debug_path, 'w') as f:
                    f.write(response_text)
                logger.debug(f"Saved error response to {debug_path}")
            return None
        
    except Exception as e:
        logger.error(f"Failed to process bubble sheet with Gemini Vision API: {str(e)}")
        return None

def get_teacher_answer_key(key_id=None, key_name=None):
    """
    Get the teacher's answer key from the database.
    
    Args:
        key_id: ID of the answer key to use (optional)
        key_name: Name of the answer key to use (optional)
        
    Returns:
        Dictionary with question numbers as keys and correct answers as values
    """
    try:
        from ..ui.answer_key import AnswerKey
        from ..db.answer_key_db import get_all_answer_keys, get_answer_key
        
        if key_id is None and key_name is None:
            answer_keys = get_all_answer_keys() 
            if answer_keys and len(answer_keys) > 0:
                answer_keys.sort(key=lambda x: x['id'], reverse=True)
                most_recent = answer_keys[0]
                logger.info(f"Using most recent answer key: {most_recent['name']}")
                
           
                answer_key = AnswerKey(most_recent['num_questions'], most_recent['name'], most_recent['id'])
                answer_key.key = {int(k): v for k, v in most_recent['answers'].items()}
                return answer_key.get_all_answers()
            else:
                logger.warning("No answer key found in database")
                return None
        
        answer_key_data = get_answer_key(key_id, key_name)
        if answer_key_data:
            answer_key = AnswerKey(answer_key_data['num_questions'], answer_key_data['name'], answer_key_data['id'])
            answer_key.key = {int(k): v for k, v in answer_key_data['answers'].items()}
            return answer_key.get_all_answers()
        else:
            if key_id:
                logger.warning(f"No answer key found with ID {key_id}")
            elif key_name:
                logger.warning(f"No answer key found with name {key_name}")
            return None
    
    except Exception as e:
        logger.error(f"Error getting teacher answer key: {str(e)}")
        return None

def compare_answers(student_answers, teacher_key_id=None, teacher_key_name=None):
    """
    Compare student answers with the teacher's answer key.
    
    Args:
        student_answers: Dictionary with question numbers as keys and student answers as values
        teacher_key_id: ID of the teacher's answer key to use (optional)
        teacher_key_name: Name of the teacher's answer key to use (optional)
        
    Returns:
        Dictionary with comparison results
    """
    teacher_answers = get_teacher_answer_key(teacher_key_id, teacher_key_name)
    
    if not teacher_answers:
        logger.warning("No teacher answer key available for comparison")
        return {
            "score": 0,
            "total": 0,
            "percentage": 0,
            "details": {}
        }
    
    score = 0
    details = {}
    
    for q_num, correct_answer in teacher_answers.items():
        student_answer = student_answers.get(q_num, "blank")
        is_correct = student_answer == correct_answer
        
        if is_correct:
            score += 1
        
        details[q_num] = {
            "student_answer": student_answer,
            "correct_answer": correct_answer,
            "is_correct": is_correct
        }
    
    total = len(teacher_answers)
    percentage = round((score / total) * 100) if total > 0 else 0
    
    return {
        "score": score,
        "total": total,
        "percentage": percentage,
        "details": details
    }

def process_document_with_gemini(image: np.ndarray, debug_save_path: Optional[str] = None, debug: bool = False) -> Dict[str, Any]:
    """
    Process a document image with Gemini Vision API.
    This is a synchronous wrapper around the async process_bubble_sheet function.
    
    Args:
        image: OpenCV image (numpy array)
        debug_save_path: Path to save debug images (optional)
        debug: Whether to log debug information
        
    Returns:
        Dictionary with processing results
    """
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    try:
        answers = loop.run_until_complete(process_bubble_sheet(image, debug=debug))
        
        return {
            "gemini_results": answers,
            "debug_path": debug_save_path
        }
    except Exception as e:
        logger.error(f"Error processing document with Gemini Vision API: {str(e)}")
        return {
            "gemini_results": {},
            "debug_path": debug_save_path,
            "error": str(e)
        }
