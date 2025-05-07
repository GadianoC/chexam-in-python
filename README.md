# Bubble Sheet Scanner (Kivy + OpenCV + Tesseract OCR)

## Overview
A mobile app for scanning bubble sheets using your device camera. Built with Kivy, OpenCV for bubble detection, and Tesseract OCR for document content extraction.

## Features
- Capture image from camera
- Detect sheet edges and warp to top-down view
- Detect filled bubbles using OpenCV
- Extract document text and structure using Tesseract OCR

## Project Structure
- `main.py`: App entry point
- `camera_widget.py`: Camera handling logic
- `app/processing/image_processing.py`: Edge detection, perspective transform, and document processing
- `app/processing/ocr_processing.py`: Text extraction using Tesseract OCR
- `answer_detection.py`: Bubble detection logic
- `ui_screens.py`: Kivy UI logic
- `requirements.txt`: Dependencies
- `ocr_example.py`: Example script demonstrating OCR integration

## How to Run
1. Install dependencies: `pip install -r requirements.txt`
2. Run the app: `python main.py`

## OCR Example
To test the OCR functionality with an example image:
```
python ocr_example.py path/to/your/image.jpg --debug --output output.png
```

## Packaging for Android
- Use [Buildozer](https://buildozer.readthedocs.io/en/latest/) to build for Android.

# Student Analysis System for Chexam

This document provides information about the Student Analysis System implemented in the Chexam application.

## Overview

The Student Analysis System allows teachers to:

1. Manage student records (add, view, delete)
2. Generate random test data for demonstration purposes
3. Analyze individual student performance against answer keys
4. View class-wide analysis and statistics

## Features

### Student Management
- Add new students with unique names
- View a list of all students
- Delete students
- Initialize example data with 30 random students

### Student Analysis
- Compare student answers with the correct answer key
- Calculate scores and percentages
- Identify correctly and incorrectly answered questions
- Generate insights about student strengths and weaknesses
- Provide personalized suggestions for improvement

### Class Analysis
- Calculate class average score and passing rate
- Identify highest and lowest scores
- Determine most frequently missed questions
- Identify best understood questions
- Generate insights about class strengths and weaknesses
- Provide teaching suggestions based on overall performance

## How to Use

### Student Management Screen
1. From the home screen, click "Student Management"
2. To add a student: Enter a name in the text field and click "Add Student"
3. To select a student: Click on a student name in the list
4. To delete a student: Select a student and click "Delete Selected Student"
5. To initialize example data: Click "Initialize 30 Example Students"

### Analyzing a Student
1. In the Student Management screen, select a student
2. Select an answer key (if multiple are available)
3. Click "Analyze Selected Student"
4. View the analysis results on the right side of the screen

### Class Analysis Screen
1. From the home screen, click "Class Analysis"
2. Select an answer key (if multiple are available)
3. Click "Analyze All Students"
4. View the class-wide analysis results

## Implementation Notes

The analysis system uses a combination of:

1. Gemini API (when available) for AI-powered analysis
2. A fallback mock analysis system when the Gemini API is unavailable

The mock analysis system provides similar functionality to the Gemini API, including:
- Score calculation
- Identification of strengths and weaknesses
- Generation of suggestions
- Class-wide statistical analysis

## Database Structure

The system uses SQLite with the following tables:

- `students`: Stores student information
- `student_answers`: Stores student answers for specific answer keys
- `analysis_results`: Stores analysis results for each student

## Future Improvements

Potential future enhancements:
- Export analysis results to PDF or CSV
- Track student progress over time
- Generate visual charts and graphs
- Compare performance across different tests
- Group students by performance level


# Chexam with Gemini Vision API Integration

## Overview
This project has been enhanced with Google's Gemini Vision API to improve bubble sheet detection accuracy. The Gemini Vision API replaces the traditional computer vision and OCR techniques previously used, providing more accurate and robust detection of filled bubbles on exam sheets.

## Setup Instructions

### 1. API Key
To use the Gemini Vision API, you need to obtain an API key:

1. Visit https://makersuite.google.com/app/apikey
2. Create a new API key
3. Create a `.env` file in the project root directory
4. Add your API key to the `.env` file:
   ```
   GEMINI_API_KEY=your_api_key_here
   ```

### 2. Dependencies
All required dependencies are already in the `requirements.txt` file. Make sure you have them installed:

```
pip install -r requirements.txt
```

## How It Works

### Bubble Sheet Detection
The application now uses Gemini Vision API to:

1. Detect the document boundaries (still using OpenCV)
2. Apply perspective transformation to get a top-down view
3. Send the processed image to Gemini Vision API
4. Interpret the API response to extract filled bubbles

### Rules for Bubble Detection
For each question (1-60), the system follows these rules:
- If exactly one bubble is filled (A, B, C, or D), that option is returned
- If no bubbles are filled, "blank" is returned
- If multiple bubbles are filled, "blank" is returned
- If the API can't determine the answer, "blank" is returned

## Usage

1. Launch the application: `python main.py`
2. Scan a bubble sheet using the scanner screen
3. Click "Analyze Answers" to process the image with Gemini Vision API
4. View the detected answers in the results panel

## Technical Details

### Image Size Limits
- The Gemini Vision API has a 20MB limit for images
- The application automatically resizes images if they exceed this limit

### API Response Format
The Gemini Vision API returns a JSON object with question numbers as keys and selected options as values:

```json
{
  "answers": {
    "1": "A",
    "2": "blank",
    "3": "C",
    ...
  }
}
```

## Troubleshooting

### API Key Issues
If you see an error about the API key:
- Make sure you've created a `.env` file with your API key
- Check that the API key is valid and active
- Verify that the `python-dotenv` package is installed

### Connection Issues
If the API calls fail:
- Check your internet connection
- Verify that your API key has the necessary permissions
- Check if you've reached API rate limits

### Image Processing Issues
If bubble detection is inaccurate:
- Ensure the document is well-lit and clearly visible
- Make sure the bubbles are properly filled
- Try adjusting the image before analysis (rotate if needed)

## Benefits Over Traditional Methods

1. **Improved Accuracy**: Gemini Vision can better handle variations in bubble sheets, lighting conditions, and image quality.

2. **Adaptability**: The API can recognize various bubble sheet formats without requiring specific parameter tuning.

3. **Contextual Understanding**: It understands the relationship between questions, options, and bubbles.

4. **Simplified Processing**: Eliminates the need for complex image preprocessing and bubble detection algorithms.

## Next Steps
- Improve bubble detection accuracy
- Enhance OCR data extraction for bubble detection
- Improve UI/UX
