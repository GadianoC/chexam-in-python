import cv2
import numpy as np
import pytesseract
import logging
import os
from pathlib import Path

# Configure logging
logger = logging.getLogger("chexam.ocr_processing")
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('[%(levelname)s] %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    # Set default level to ERROR to reduce console spam
    logger.setLevel(logging.ERROR)

# Check for Tesseract path in common locations
def find_tesseract_path():
    """
    Attempt to find Tesseract OCR installation path on Windows.
    Returns the path if found, None otherwise.
    """
    common_paths = [
        r'C:\Program Files\Tesseract-OCR\tesseract.exe',
        r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe',
        os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Programs', 'Tesseract-OCR', 'tesseract.exe'),
        os.path.join(os.environ.get('PROGRAMFILES', ''), 'Tesseract-OCR', 'tesseract.exe'),
        os.path.join(os.environ.get('PROGRAMFILES(X86)', ''), 'Tesseract-OCR', 'tesseract.exe')
    ]
    
    for path in common_paths:
        if os.path.isfile(path):
            return path
    
    return None

# Try to set Tesseract path automatically
tesseract_path = find_tesseract_path()
if tesseract_path:
    pytesseract.pytesseract.tesseract_cmd = tesseract_path
    logger.info(f"Found Tesseract at: {tesseract_path}")
else:
    logger.warning("Tesseract not found in common locations. Please install Tesseract OCR or set path manually.")

def select_best_preprocessing_method(image):
    """
    Automatically select the best preprocessing method based on image characteristics.
    
    Args:
        image: Input grayscale image
        
    Returns:
        String name of the best preprocessing method to use
    """
    # Ensure we're working with grayscale
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image.copy()
    
    # Calculate image statistics
    mean_val = np.mean(gray)
    std_val = np.std(gray)
    
    # Calculate histogram
    hist = cv2.calcHist([gray], [0], None, [256], [0, 256])
    hist_normalized = hist.flatten() / hist.sum()
    
    # Calculate entropy as a measure of information content
    entropy = -np.sum(hist_normalized * np.log2(hist_normalized + 1e-7))
    
    # Decision logic based on image characteristics
    if std_val < 40:  # Low contrast image
        return 'high_contrast'
    elif entropy > 7.0:  # High detail/noise image
        return 'adaptive'
    elif mean_val < 100:  # Dark image
        return 'high_contrast'
    elif mean_val > 200:  # Bright image
        return 'otsu'
    else:  # Default case
        return 'adaptive'

def preprocess_for_ocr(image, method='auto'):
    """
    Preprocess an image for optimal OCR results using different methods.
    
    Args:
        image: Input image (grayscale or color)
        method: Preprocessing method to use ('auto', 'default', 'high_contrast', 'sharp', 'adaptive', 'otsu')
        
    Returns:
        Preprocessed image optimized for OCR
    """
    # Ensure we're working with grayscale
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image.copy()
        
    # If method is 'auto', automatically select the best method based on image characteristics
    if method == 'auto':
        method = select_best_preprocessing_method(gray)
    
    if method == 'high_contrast':
        # Apply CLAHE with stronger parameters for better contrast
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(gray)
        
        # Apply slight Gaussian blur to reduce noise
        blurred = cv2.GaussianBlur(enhanced, (3, 3), 0)
        
        # Apply Otsu's thresholding
        _, binary = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # Apply morphological operations to clean up the image
        kernel = np.ones((2, 2), np.uint8)
        binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
        
        return binary
    
    elif method == 'sharp':
        # First enhance contrast
        clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
        enhanced = clahe.apply(gray)
        
        # Sharpen the image
        kernel = np.array([[0, -1, 0],
                           [-1, 5, -1],
                           [0, -1, 0]])
        sharpened = cv2.filter2D(enhanced, -1, kernel)
        
        # Apply Gaussian blur to reduce noise
        blurred = cv2.GaussianBlur(sharpened, (3, 3), 0)
        
        # Apply Otsu's thresholding
        _, binary = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        return binary
    
    elif method == 'adaptive':
        # First enhance contrast with CLAHE
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(gray)
        
        # Apply bilateral filter to preserve edges while reducing noise
        bilateral = cv2.bilateralFilter(enhanced, 7, 50, 50)
        
        # Apply adaptive thresholding with optimized parameters
        # Smaller block size (11) and smaller C value (5) for better local contrast
        binary = cv2.adaptiveThreshold(bilateral, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                      cv2.THRESH_BINARY, 11, 5)
        
        # Apply morphological operations to clean up the image
        # Use a slightly larger kernel for closing to connect nearby text
        kernel = np.ones((2, 2), np.uint8)
        binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
        
        # Apply opening to remove small noise
        kernel_small = np.ones((1, 1), np.uint8)
        binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel_small)
        
        return binary
    
    elif method == 'otsu':
        # Apply bilateral filter to preserve edges while reducing noise
        bilateral = cv2.bilateralFilter(gray, 9, 75, 75)
        
        # Apply Otsu's thresholding
        _, binary = cv2.threshold(bilateral, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        return binary
    
    else:  # default method
        # Apply CLAHE for better contrast
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(gray)
        
        # Apply slight Gaussian blur to reduce noise
        blurred = cv2.GaussianBlur(enhanced, (3, 3), 0)
        
        # Apply adaptive thresholding which often works better than Otsu for documents
        binary = cv2.adaptiveThreshold(blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                     cv2.THRESH_BINARY, 11, 2)
        
        # Apply morphological operations to clean up the image
        kernel = np.ones((1, 1), np.uint8)
        binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
        
        return binary

def extract_text(image, lang='eng', config='--psm 6', preprocess_method='default'):
    """
    Extract text from an image using Tesseract OCR with improved configuration.
    
    Args:
        image: Input image (color or grayscale)
        lang: Language for OCR (default: 'eng')
        config: Tesseract configuration string (default: '--psm 6')
        preprocess_method: Method to use for preprocessing ('default', 'high_contrast', 'sharp', 'adaptive', 'otsu')
    
    Returns:
        Extracted text as string
    """
    try:
        # Preprocess the image for better OCR results
        processed_img = preprocess_for_ocr(image, preprocess_method)
        
        # Save debug image if needed
        if os.environ.get('CHEXAM_DEBUG', '0') == '1':
            debug_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'debug')
            os.makedirs(debug_dir, exist_ok=True)
            cv2.imwrite(os.path.join(debug_dir, f'ocr_preprocess_{preprocess_method}.png'), processed_img)
        
        # Use more advanced Tesseract configuration
        # --psm 6: Assume a single uniform block of text
        # --oem 3: Use LSTM neural network mode
        # -l eng: Use English language
        # --dpi 300: Assume 300 DPI for better recognition
        advanced_config = f'--psm 6 --oem 3 -l {lang} --dpi 300'
        
        # Extract text using Tesseract with advanced configuration
        text = pytesseract.image_to_string(processed_img, lang=lang, config=advanced_config)
        
        return text.strip()
    except Exception as e:
        logger.error(f"OCR extraction failed: {str(e)}")
        return ""

def extract_text_with_all_methods(image, lang='eng'):
    """
    Try all preprocessing methods and return the best result based on text length.
    
    Args:
        image: Input image (color or grayscale)
        lang: Language for OCR (default: 'eng')
    
    Returns:
        Tuple of (extracted text, method used)
    """
    methods = ['default', 'high_contrast', 'sharp']
    results = []
    
    for method in methods:
        text = extract_text(image, lang=lang, preprocess_method=method)
        results.append((text, method, len(text)))
        logger.debug(f"Method {method} extracted {len(text)} characters")
    
    # Sort by text length (longer is usually better)
    results.sort(key=lambda x: x[2], reverse=True)
    
    # Return the best result
    return results[0][0], results[0][1]

def extract_text_blocks(image, lang='eng', preprocess_method='default'):
    """
    Extract text blocks with their bounding boxes from an image.
    
    Args:
        image: Input image (color or grayscale)
        lang: Language for OCR (default: 'eng')
        preprocess_method: Method to use for preprocessing
    
    Returns:
        List of dictionaries with text and bounding box information
    """
    try:
        # Preprocess the image for better OCR results
        processed_img = preprocess_for_ocr(image, preprocess_method)
        
        # Extract text blocks using Tesseract
        custom_config = r'--oem 3 --psm 11'
        data = pytesseract.image_to_data(processed_img, lang=lang, config=custom_config, output_type=pytesseract.Output.DICT)
        
        # Organize the results
        blocks = []
        n_boxes = len(data['text'])
        
        for i in range(n_boxes):
            # Skip empty text and low confidence results
            if int(data['conf'][i]) > 30:  # Only consider text with confidence > 30
                text = data['text'][i].strip()
                if text:
                    x, y, w, h = data['left'][i], data['top'][i], data['width'][i], data['height'][i]
                    blocks.append({
                        'text': text,
                        'bbox': (x, y, w, h),
                        'conf': data['conf'][i]
                    })
        
        return blocks
    except Exception as e:
        logger.error(f"OCR block extraction failed: {str(e)}")
        return []

def detect_bubbles(image, min_radius=10, max_radius=30):
    """
    Detect filled bubbles in an image with improved accuracy.
    
    Args:
        image: Input image (color or grayscale)
        min_radius: Minimum radius of bubbles to detect
        max_radius: Maximum radius of bubbles to detect
        
    Returns:
        List of dictionaries with bubble information
    """
    try:
        # Ensure we're working with grayscale
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()
        
        # Apply CLAHE for better contrast
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(gray)
        
        # Apply bilateral filter to reduce noise while preserving edges
        bilateral = cv2.bilateralFilter(enhanced, 9, 75, 75)
        
        # Apply adaptive thresholding with optimized parameters for bubbles
        thresh = cv2.adaptiveThreshold(bilateral, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                      cv2.THRESH_BINARY_INV, 11, 2)
        
        # Apply morphological operations to clean up the image
        kernel = np.ones((2, 2), np.uint8)
        thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
        
        # Find contours
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Filter contours to find bubbles
        bubbles = []
        for contour in contours:
            # Get bounding rectangle
            x, y, w, h = cv2.boundingRect(contour)
            
            # Calculate aspect ratio and area
            aspect_ratio = float(w) / h
            area = cv2.contourArea(contour)
            
            # Filter by aspect ratio (close to 1 for circles) and size
            if 0.8 <= aspect_ratio <= 1.2 and min_radius**2 * 3.14 <= area <= max_radius**2 * 3.14:
                # Get the center and radius
                center, radius = cv2.minEnclosingCircle(contour)
                center = (int(center[0]), int(center[1]))
                radius = int(radius)
                
                # Check if the bubble is filled using a more robust method
                # Create a mask for the bubble
                mask = np.zeros(gray.shape, dtype=np.uint8)
                cv2.circle(mask, center, radius, 255, -1)
                
                # Calculate the average intensity inside the bubble
                mean_val = cv2.mean(gray, mask=mask)[0]
                
                # Calculate the standard deviation inside the bubble
                # This helps distinguish between filled and unfilled bubbles
                mean, stddev = cv2.meanStdDev(gray, mask=mask)
                
                # Calculate the histogram of the bubble area
                hist = cv2.calcHist([gray], [0], mask, [256], [0, 256])
                hist = hist.flatten() / np.sum(hist)  # Normalize
                
                # Calculate the darkness ratio (percentage of dark pixels)
                # This is more robust than just using the mean value
                dark_pixels_ratio = np.sum(hist[:128]) / np.sum(hist)  # Ratio of pixels darker than middle gray
                
                # If the average intensity is below a threshold, consider it filled
                # Adjust threshold based on the overall image brightness
                overall_mean = np.mean(gray)
                intensity_threshold = overall_mean * 0.85  # Adaptive threshold based on image brightness
                darkness_threshold = 0.5  # At least 50% of pixels should be dark
                
                # Use both criteria for more robust detection
                filled = (mean_val < intensity_threshold) or (dark_pixels_ratio > darkness_threshold)
                
                # Calculate a more nuanced confidence score
                # Higher confidence for darker bubbles and lower standard deviation
                darkness_score = 1.0 - (mean_val / 255.0)
                uniformity_score = 1.0 - min(stddev[0][0] / 128.0, 1.0)  # Lower stddev means more uniform filling
                confidence = (darkness_score * 0.7) + (uniformity_score * 0.3)  # Weighted combination
                
                bubbles.append({
                    'center': center,
                    'radius': radius,
                    'filled': filled,
                    'bbox': (x, y, w, h),
                    'mean_intensity': mean_val,
                    'stddev': stddev[0][0],
                    'confidence': confidence
                })
        
        return bubbles
    except Exception as e:
        logger.error(f"Bubble detection failed: {str(e)}")
        return []

def process_document_with_ocr(image, debug_save_path=None, debug=False):
    """
    Process a document image with OCR to extract text and detect bubbles.
    
    Args:
        image: Input image (BGR format)
        debug_save_path: Path to save debug images (optional)
        debug: Whether to save debug images and log debug info
        
    Returns:
        Dictionary with OCR results and bubble detection
    """
    # Configure logging
    if debug:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.ERROR)
    
    # Try all preprocessing methods and use the best one
    logger.debug("Extracting text from document using multiple methods...")
    text, best_method = extract_text_with_all_methods(image)
    logger.debug(f"Best preprocessing method: {best_method}")
    
    # Extract text blocks using the best method
    logger.debug("Extracting text blocks from document...")
    blocks = extract_text_blocks(image, preprocess_method=best_method)
    
    # Detect bubbles
    logger.debug("Detecting bubbles in document...")
    bubbles = detect_bubbles(image)
    
    # Save debug images if requested
    if debug and debug_save_path:
        # Create visualizations
        vis_img = image.copy()
        
        # Draw text blocks
        for block in blocks:
            x, y, w, h = block['bbox']
            cv2.rectangle(vis_img, (x, y), (x + w, y + h), (0, 255, 0), 2)
            cv2.putText(vis_img, block['text'][:10], (x, y - 10), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        
        # Draw bubbles
        for bubble in bubbles:
            x, y, w, h = bubble['bbox']
            color = (0, 0, 255) if bubble['filled'] else (255, 0, 0)
            cv2.rectangle(vis_img, (x, y), (x + w, y + h), color, 2)
            cv2.circle(vis_img, bubble['center'], int(bubble['radius']), color, 2)
        
        # Save the visualization
        cv2.imwrite(debug_save_path.replace('.png', '_ocr_analysis.png'), vis_img)
        
        # Save preprocessed images for all methods
        for method in ['default', 'high_contrast', 'sharp']:
            processed = preprocess_for_ocr(image, method)
            cv2.imwrite(debug_save_path.replace('.png', f'_preprocess_{method}.png'), processed)
    
    # Return the OCR results
    return {
        'full_text': text,
        'blocks': blocks,
        'bubbles': bubbles,
        'best_preprocess_method': best_method
    }
