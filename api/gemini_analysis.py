import google.generativeai as genai
import os
import json
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-pro")

def analyze_bubble_answers(correct_answers, student_answers):
    prompt = f"""
    Analyze the student's answers and return a JSON with:
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
    """

    response = model.generate_content(prompt)

    try:
        return json.loads(response.text.strip())
    except Exception as e:
        print(" Error parsing Gemini response:", e)
        print(" Raw output:", response.text)
        return None
