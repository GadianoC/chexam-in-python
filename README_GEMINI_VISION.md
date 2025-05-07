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
