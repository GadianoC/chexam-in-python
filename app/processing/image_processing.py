import cv2
import numpy as np
import logging

logger = logging.getLogger("chexam.image_processing")
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('[%(levelname)s] %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.ERROR)

def process_document_pipeline(image, debug_save_path=None, debug=False):
    """
    Process document image with the following pipeline:
    original > gray > threshold > contour > biggest contour > warp perspective > warp gray
    
    Args:
        image: Input image (BGR format)
        debug_save_path: Path to save debug images (optional)
        debug: Whether to save debug images and log debug info
        
    Returns:
        warped_color: Color version of the warped document
        warped_gray: Grayscale version of the warped document
        sheet_pts: Four corner points of the detected document (ordered)
    """
    original = image.copy()
    
    if debug:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.ERROR)

    # 1. Convert to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    if debug and debug_save_path:
        cv2.imwrite(debug_save_path.replace('.png', '_1_gray.png'), gray)
    
    # 2. Apply Gaussian blur to reduce noise
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    
    if debug and debug_save_path:
        cv2.imwrite(debug_save_path.replace('.png', '_2_blurred.png'), blurred)
    
    # 3. Apply Canny edge detection
    edges = cv2.Canny(blurred, 75, 200)
    
    # 4. Apply dilation and erosion to strengthen the edges
    kernel = np.ones((5, 5), np.uint8)
    dilated = cv2.dilate(edges, kernel, iterations=2)
    edges = cv2.erode(dilated, kernel, iterations=1)
    
    if debug and debug_save_path:
        cv2.imwrite(debug_save_path.replace('.png', '_3_thresh.png'), edges)
    
    # 5. Find contours
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    

    contour_vis = image.copy()
    
    if debug:
        cv2.drawContours(contour_vis, contours, -1, (0, 255, 0), 2)
    
    # 6. Find the largest quadrilateral contour (the document)
    max_area = 0
    biggest_contour = None
    
    for contour in contours:
        area = cv2.contourArea(contour)
        

        if area < 1000:
            continue
    
        peri = cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, 0.02 * peri, True)
        
      
        if len(approx) == 4 and area > max_area:
            biggest_contour = approx
            max_area = area
   
    if biggest_contour is None:
        logger.warning("No suitable document contour found, using full image")
        h, w = image.shape[:2]
        sheet_pts = np.array([[0, 0], [w, 0], [w, h], [0, h]], dtype=np.float32)
        
        if debug and debug_save_path:
            cv2.imwrite(debug_save_path.replace('.png', '_4_no_contour.png'), image)
        
        warped_color = image.copy()
        warped_gray = gray.copy()
        warped_thresh = cv2.adaptiveThreshold(warped_gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                             cv2.THRESH_BINARY, 11, 2)
        
        return warped_color, warped_gray, None
    
    # Reorder the points / perspective transformation
    sheet_pts = order_points(biggest_contour.reshape(4, 2))
    
    if debug and debug_save_path:
        cv2.drawContours(contour_vis, [biggest_contour], -1, (0, 255, 0), 3)
        cv2.imwrite(debug_save_path.replace('.png', '_4_contour.png'), contour_vis)

    # 7. Apply perspective transform to get a top-down view
    warped_color = four_point_transform(original, sheet_pts)
    
    # 8. Convert warped image to grayscale
    warped_gray = cv2.cvtColor(warped_color, cv2.COLOR_BGR2GRAY)
    
    if debug and debug_save_path:
        cv2.imwrite(debug_save_path.replace('.png', '_5_warped_color.png'), warped_color)
        cv2.imwrite(debug_save_path.replace('.png', '_6_warped_gray.png'), warped_gray)
    
    # 9. Enhance the warped grayscale image for better visualization
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    warped_gray_enhanced = clahe.apply(warped_gray)
    
    if debug and debug_save_path:
        cv2.imwrite(debug_save_path.replace('.png', '_6_5_enhanced.png'), warped_gray_enhanced)
    
    if debug and debug_save_path:
        cv2.imwrite(debug_save_path.replace('.png', '_5_warped_color.png'), warped_color)
        cv2.imwrite(debug_save_path.replace('.png', '_6_warped_gray.png'), warped_gray)
    
    warped_color, warped_gray = correct_orientation(warped_color, warped_gray, debug_save_path, debug)
    
    return warped_color, warped_gray, sheet_pts


def correct_orientation(color_image, gray_image, debug_save_path=None, debug=False):
    """
    Detect and correct the orientation of the image to ensure it's upright.
    
    Args:
        color_image: Color version of the image to correct
        gray_image: Grayscale version of the image to correct
        debug_save_path: Path to save debug images (optional)
        debug: Whether to save debug images and log debug info
        
    Returns:
        corrected_color: Color version of the corrected image
        corrected_gray: Grayscale version of the corrected image
    """
    height, width = gray_image.shape
    
    is_portrait = height > width
    
    if not is_portrait:
        logger.info("Image is in landscape orientation, rotating to portrait")
        corrected_color = cv2.rotate(color_image, cv2.ROTATE_90_CLOCKWISE)
        corrected_gray = cv2.rotate(gray_image, cv2.ROTATE_90_CLOCKWISE)
        
        if debug and debug_save_path:
            cv2.imwrite(debug_save_path.replace('.png', '_7_rotated_color.png'), corrected_color)
            cv2.imwrite(debug_save_path.replace('.png', '_8_rotated_gray.png'), corrected_gray)
    else:
        corrected_color = color_image
        corrected_gray = gray_image
    
    
    if debug and debug_save_path:
        cv2.imwrite(debug_save_path.replace('.png', '_9_final_color.png'), corrected_color)
        cv2.imwrite(debug_save_path.replace('.png', '_10_final_gray.png'), corrected_gray)
    
    return corrected_color, corrected_gray



def detect_sheet_edges(image, debug_save_path=None, debug=False):
    """
    Detect the edges of a bubble sheet in an image.
    Returns the four points of the sheet or None if not found.
    """
    _, _, sheet_pts = process_document_pipeline(image, debug_save_path, debug)
    return sheet_pts

def find_document_corners(edge_img):
    """
    Find the four corners of a document in an edge image.
    Returns the four corners or None if not found.
    """
    logger.warning("find_document_corners is deprecated, use process_document_pipeline instead")
    return None


def validate_corners(corners, img_shape):
    """
    Validate that corners are within image bounds and form a reasonable quadrilateral.
    """
    logger.warning("validate_corners is deprecated, use process_document_pipeline instead")
    return False


# This function was removed as Tesseract OCR has been replaced by Gemini Vision API

def four_point_transform(image, pts):
    rect = order_points(pts)
    (tl, tr, br, bl) = rect
    widthA = np.linalg.norm(br - bl)
    widthB = np.linalg.norm(tr - tl)
    maxWidth = max(int(widthA), int(widthB))
    heightA = np.linalg.norm(tr - br)
    heightB = np.linalg.norm(tl - bl)
    maxHeight = max(int(heightA), int(heightB))
    dst = np.array([
        [0, 0],
        [maxWidth - 1, 0],
        [maxWidth - 1, maxHeight - 1],
        [0, maxHeight - 1]], dtype = 'float32')
    M = cv2.getPerspectiveTransform(rect, dst)
    warped = cv2.warpPerspective(image, M, (maxWidth, maxHeight))
    return warped

def order_points(pts):
    pts = np.array(pts)
    sorted_by_y = pts[np.argsort(pts[:, 1])]
    top = sorted_by_y[:2]
    bottom = sorted_by_y[2:]
    top = top[np.argsort(top[:, 0])]
    bottom = bottom[np.argsort(bottom[:, 0])]
    # Order: top-left, top-right, bottom-right, bottom-left
    return np.array([top[0], top[1], bottom[1], bottom[0]], dtype='float32')

