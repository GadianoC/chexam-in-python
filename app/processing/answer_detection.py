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
    
    # Ensure image is grayscale
    if len(warped_img.shape) == 3:
        gray = cv2.cvtColor(warped_img, cv2.COLOR_BGR2GRAY)
    else:
        gray = warped_img.copy()
    
    # Apply thresholding if not already binary
    if gray.max() > 1:
        _, binary = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY_INV)
    else:
        binary = gray
        
    if debug and debug_save_path:
        cv2.imwrite(debug_save_path + '_binary.png', binary)
    
    # Find all contours
    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    # Filter contours by size and shape to find bubbles
    bubbles = []
    for contour in contours:
        area = cv2.contourArea(contour)
        perimeter = cv2.arcLength(contour, True)
        
        # Skip very small contours
        if area < 100:  # Minimum area threshold
            continue
            
        # Circularity = 4π(area/perimeter²)
        # Perfect circle has circularity = 1
        if perimeter > 0:
            circularity = 4 * np.pi * (area / (perimeter * perimeter))
        else:
            circularity = 0
            
        # Filter by circularity to find bubble-like shapes
        if 0.5 < circularity < 1.2:  # Allow some deviation from perfect circle
            x, y, w, h = cv2.boundingRect(contour)
            aspect_ratio = float(w) / h
            
            # Bubbles should be roughly circular
            if 0.8 < aspect_ratio < 1.2:
                # Calculate fill percentage
                mask = np.zeros_like(gray)
                cv2.drawContours(mask, [contour], 0, 255, -1)
                fill_percentage = np.sum(binary[mask == 255]) / np.sum(mask == 255) if np.sum(mask == 255) > 0 else 0
                
                # Consider it filled if more than 40% is filled
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
        
    # If no bubbles found, return empty result
    if not bubbles:
        return {}
    
    # For a simple implementation, we'll organize bubbles into a grid
    # This assumes a standard bubble sheet layout
    
    # Sort bubbles by y-coordinate (row)
    bubbles.sort(key=lambda b: b['center'][1])
    
    # For a standard 60-question bubble sheet with A, B, C, D options,
    # we need a more structured approach
    
    # First, check if we have enough bubbles to work with
    if len(bubbles) < 20:  # Arbitrary threshold - should have at least some bubbles
        if debug:
            logger.warning(f"Too few bubbles detected: {len(bubbles)}")
        return {}
    
    # Get image dimensions
    h, w = warped_img.shape[:2]
    
    # Organize bubbles into a grid structure
    # For a typical bubble sheet, we expect:
    # - 60 questions (rows)
    # - 4 options per question (columns: A, B, C, D)
    # - Often organized in 3 columns of 20 questions each
    
    # Step 1: Determine the average bubble size
    avg_area = sum(b['area'] for b in bubbles) / len(bubbles)
    
    # Step 2: Group bubbles by their y-coordinate (rows)
    row_tolerance = int(math.sqrt(avg_area) * 0.7)  # Adaptive tolerance based on bubble size
    
    # Sort bubbles by y-coordinate
    bubbles_by_y = sorted(bubbles, key=lambda b: b['center'][1])
    
    # Group into rows
    rows = []
    current_row = [bubbles_by_y[0]]
    
    for bubble in bubbles_by_y[1:]:
        if abs(bubble['center'][1] - current_row[0]['center'][1]) < row_tolerance:
            current_row.append(bubble)
        else:
            # Sort bubbles in this row by x-coordinate
            current_row.sort(key=lambda b: b['center'][0])
            rows.append(current_row)
            current_row = [bubble]
    
    # Add the last row
    if current_row:
        current_row.sort(key=lambda b: b['center'][0])
        rows.append(current_row)
    
    # Sort rows by y-coordinate (top to bottom)
    rows.sort(key=lambda row: row[0]['center'][1])
    
    # Step 3: Determine the structure of the bubble sheet
    # For a standard 60-question sheet with 3 columns of 20 questions
    
    # Count the number of bubbles in each row to determine the structure
    row_lengths = [len(row) for row in rows]
    
    # Most common row length should be the number of options (typically 4: A, B, C, D)
    from collections import Counter
    option_count = Counter(row_lengths).most_common(1)[0][0]
    
    if debug:
        logger.info(f"Detected {option_count} options per question")
        logger.info(f"Found {len(rows)} rows of bubbles")
    
    # Map to answers (A, B, C, D)
    answer_options = ['A', 'B', 'C', 'D'][:option_count]
    results = {}
    
    # Process each row to determine the filled bubble
    for i, row in enumerate(rows):
        # Skip rows that don't have the expected number of options
        if len(row) != option_count:
            continue
        
        # Get the bubble with the highest fill percentage
        best_bubble = max(row, key=lambda b: b['fill'])
        bubble_index = row.index(best_bubble)
        
        # Only consider it filled if the fill percentage is above threshold
        if best_bubble['fill'] > 0.3:  # Adjust threshold as needed
            question_num = i + 1
            if bubble_index < len(answer_options):
                results[question_num] = answer_options[bubble_index]
    
    # For a 60-question sheet with 3 columns, we need to remap the question numbers
    # This depends on the specific layout of the sheet
    
    # If we have approximately 20 rows (for a 3-column layout with 60 questions)
    if 15 <= len(rows) <= 25:
        # Assume we have 3 columns of 20 questions each
        remapped_results = {}
        rows_per_column = len(rows) // 3
        
        for q_num, answer in results.items():
            # Calculate the actual question number based on position
            column = (q_num - 1) // rows_per_column
            row = (q_num - 1) % rows_per_column
            
            actual_q_num = row + 1 + (column * rows_per_column)
            if 1 <= actual_q_num <= 60:  # Ensure valid question number
                remapped_results[actual_q_num] = answer
        
        results = remapped_results
    
    if debug:
        logger.debug(f"Detected answers: {results}")
        
        # Create debug visualization
        if debug_save_path:
            # Create a color version if the input is grayscale
            if len(warped_img.shape) == 2:
                debug_img = cv2.cvtColor(warped_img, cv2.COLOR_GRAY2BGR)
            else:
                debug_img = warped_img.copy()
                
            # Draw all detected bubbles
            for bubble in bubbles:
                center = (int(bubble['center'][0]), int(bubble['center'][1]))
                radius = int(math.sqrt(bubble['area'] / math.pi))
                # Draw circle for each bubble
                cv2.circle(debug_img, center, radius, (0, 0, 255), 1)
            
            # Highlight the filled bubbles
            for q_num, answer in results.items():
                # Find the corresponding bubble
                for row in rows:
                    for i, bubble in enumerate(row):
                        if i < len(answer_options) and answer_options[i] == answer:
                            # This is a filled bubble
                            center = (int(bubble['center'][0]), int(bubble['center'][1]))
                            radius = int(math.sqrt(bubble['area'] / math.pi))
                            # Draw filled bubble
                            cv2.circle(debug_img, center, radius, (0, 255, 0), 2)
                            # Label with question number and answer
                            cv2.putText(debug_img, f"{q_num}:{answer}", 
                                       (center[0]-10, center[1]-radius-5),
                                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
            
            # Save the debug image
            cv2.imwrite(debug_save_path + '_detected.png', debug_img)
    
    return results
