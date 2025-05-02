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
2. Install Tesseract OCR:
   - Windows: Download and install from [GitHub](https://github.com/UB-Mannheim/tesseract/wiki)
   - macOS: `brew install tesseract`
   - Linux: `sudo apt install tesseract-ocr`
3. Run the app: `python main.py`

## OCR Example
To test the OCR functionality with an example image:
```
python ocr_example.py path/to/your/image.jpg --debug --output output.png
```

## Packaging for Android
- Use [Buildozer](https://buildozer.readthedocs.io/en/latest/) to build for Android.

## Next Steps
- Improve bubble detection accuracy
- Add answer key input and comparison UI
- Enhance OCR text extraction for specific document types
- Improve UI/UX
