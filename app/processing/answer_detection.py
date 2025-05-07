import numpy as np
import cv2
import logging
import math

def detect_bubbles(warped_img, debug=False, debug_save_path=None):
    """
    Detect filled bubbles in a processed exam sheet image.
    Specifically designed for 60-question bubble sheets with A, B, C, D options.
    
    Args:
        warped_img: Preprocessed image (grayscale or binary)
        debug: If True, save debug images and print verbose info
        debug_save_path: Path prefix for debug images
        
    Returns:
        A dictionary with question numbers as keys and detected answers as values
        Example: {1: 'A', 2: 'C', 3: 'B', ...}
    """
    logger = logging.getLogger("chexam.processing.answer_detection")
    logger.setLevel(logging.DEBUG if debug else logging.INFO)
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter('[%(levelname)s] %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    
    if len(warped_img.shape) == 3:
        gray = cv2.cvtColor(warped_img, cv2.COLOR_BGR2GRAY)
    else:
        gray = warped_img.copy()
    
    if gray.max() > 1:
        _, binary = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY_INV)
    else:
        binary = gray
        
    if debug and debug_save_path:
        cv2.imwrite(debug_save_path + '_binary.png', binary)
    
    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    bubbles = []
    for contour in contours:
        area = cv2.contourArea(contour)
        perimeter = cv2.arcLength(contour, True)
        
        if area < 100: 
            continue
            
        if perimeter > 0:
            circularity = 4 * np.pi * (area / (perimeter * perimeter))
        else:
            circularity = 0
            
        if 0.5 < circularity < 1.2:  
            x, y, w, h = cv2.boundingRect(contour)
            aspect_ratio = float(w) / h
            if 0.8 < aspect_ratio < 1.2:
                mask = np.zeros_like(gray)
                cv2.drawContours(mask, [contour], 0, 255, -1)
                fill_percentage = np.sum(binary[mask == 255]) / np.sum(mask == 255) if np.sum(mask == 255) > 0 else 0
                
                if fill_percentage > 0.4:
                    center_x = x + w/2
                    center_y = y + h/2
                    bubbles.append({
                        'center': (center_x, center_y),
                        'area': area,
                        'fill': fill_percentage
                    })
    
    if debug:
        logger.debug(f"Found {len(bubbles)} potential filled bubbles")
        
    if not bubbles:
        return {}
    

    bubbles.sort(key=lambda b: b['center'][1])
    bubbles.sort(key=lambda b: b['center'][1])
    

    if len(bubbles) < 20: 
        if debug:
            logger.warning(f"Too few bubbles detected: {len(bubbles)}")
        return {}
    
    h, w = warped_img.shape[:2]
    
    
    avg_area = sum(b['area'] for b in bubbles) / len(bubbles)
    
    
    row_tolerance = int(math.sqrt(avg_area) * 0.7) 
    
    bubbles_by_y = sorted(bubbles, key=lambda b: b['center'][1])
    

    rows = []
    current_row = [bubbles_by_y[0]]
    
    for bubble in bubbles_by_y[1:]:
        if abs(bubble['center'][1] - current_row[0]['center'][1]) < row_tolerance:
            current_row.append(bubble)
        else:
            current_row.sort(key=lambda b: b['center'][0])
            rows.append(current_row)
            current_row = [bubble]
    
    if current_row:
        current_row.sort(key=lambda b: b['center'][0])
        rows.append(current_row)
    

    rows.sort(key=lambda row: row[0]['center'][1])
    
    
    row_lengths = [len(row) for row in rows]

    from collections import Counter
    option_count = Counter(row_lengths).most_common(1)[0][0]
    
    if debug:
        logger.info(f"Detected {option_count} options per question")
        logger.info(f"Found {len(rows)} rows of bubbles")
    
    answer_options = ['A', 'B', 'C', 'D'][:option_count]
    results = {}
    

    for i, row in enumerate(rows):
    
        if len(row) != option_count:
            continue
        
 
        best_bubble = max(row, key=lambda b: b['fill'])
        bubble_index = row.index(best_bubble)
        
        if best_bubble['fill'] > 0.3:  
            question_num = i + 1
            if bubble_index < len(answer_options):
                results[question_num] = answer_options[bubble_index]
    


    if 15 <= len(rows) <= 25:
        remapped_results = {}
        rows_per_column = len(rows) // 3
        
        for q_num, answer in results.items():
            column = (q_num - 1) // rows_per_column
            row = (q_num - 1) % rows_per_column
            
            actual_q_num = row + 1 + (column * rows_per_column)
            if 1 <= actual_q_num <= 60:  
                remapped_results[actual_q_num] = answer
        
        results = remapped_results
    
    if debug:
        logger.debug(f"Detected answers: {results}")
        
        if debug_save_path:
            if len(warped_img.shape) == 2:
                debug_img = cv2.cvtColor(warped_img, cv2.COLOR_GRAY2BGR)
            else:
                debug_img = warped_img.copy()
                
            for bubble in bubbles:
                center = (int(bubble['center'][0]), int(bubble['center'][1]))
                radius = int(math.sqrt(bubble['area'] / math.pi))
                cv2.circle(debug_img, center, radius, (0, 0, 255), 1)
            
            
            for q_num, answer in results.items():
                for row in rows:
                    for i, bubble in enumerate(row):
                        if i < len(answer_options) and answer_options[i] == answer:
             
                            center = (int(bubble['center'][0]), int(bubble['center'][1]))
                            radius = int(math.sqrt(bubble['area'] / math.pi))

                            cv2.circle(debug_img, center, radius, (0, 255, 0), 2)
                 
                            cv2.putText(debug_img, f"{q_num}:{answer}", 
                                       (center[0]-10, center[1]-radius-5),
                                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
            
            cv2.imwrite(debug_save_path + '_detected.png', debug_img)
    
    return results
