import cv2
import os
import sys
import argparse
from app.processing.image_processing import process_document_with_ocr

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Process a document image with OpenCV and Tesseract OCR')
    parser.add_argument('image_path', help='Path to the input image')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    parser.add_argument('--output', '-o', help='Path to save output images')
    parser.add_argument('--method', '-m', choices=['default', 'high_contrast', 'sharp'], 
                        default='default', help='OCR preprocessing method')
    args = parser.parse_args()
    
    # Check if the input image exists
    if not os.path.isfile(args.image_path):
        print(f"Error: Image file '{args.image_path}' not found")
        return 1
    
    # Set debug save path
    debug_save_path = None
    if args.debug and args.output:
        debug_save_path = args.output
    
    # Load the image
    print(f"Loading image: {args.image_path}")
    image = cv2.imread(args.image_path)
    if image is None:
        print(f"Error: Could not load image '{args.image_path}'")
        return 1
    
    # Process the document with OCR
    print("Processing document with OpenCV and Tesseract OCR...")
    results = process_document_with_ocr(image, debug_save_path, args.debug)
    
    # Display the results
    if results['sheet_pts'] is not None:
        print("\n--- Document Detection Results ---")
        print(f"Document corners detected: {results['sheet_pts'].tolist()}")
    else:
        print("\n--- Document Detection Failed ---")
    
    # Display OCR results
    if results['ocr_results'] is not None:
        print("\n--- OCR Results ---")
        print(f"Best preprocessing method: {results['ocr_results']['best_preprocess_method']}")
        
        print("\nFull Text:")
        print(results['ocr_results']['full_text'])
        
        print("\nText Blocks:")
        for i, block in enumerate(results['ocr_results']['blocks']):
            print(f"Block {i+1}: '{block['text']}' at {block['bbox']}")
        
        print("\nBubbles Detected:")
        filled_bubbles = [b for b in results['ocr_results']['bubbles'] if b['filled']]
        empty_bubbles = [b for b in results['ocr_results']['bubbles'] if not b['filled']]
        print(f"- {len(filled_bubbles)} filled bubbles")
        print(f"- {len(empty_bubbles)} empty bubbles")
    else:
        print("\n--- OCR Processing Failed ---")
    
    # Save the processed images if output path is provided
    if args.output:
        output_dir = os.path.dirname(args.output)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # Save the warped color image
        warped_color_path = args.output.replace('.png', '_warped_color.png')
        cv2.imwrite(warped_color_path, results['warped_color'])
        print(f"\nSaved warped color image to: {warped_color_path}")
        
        # Save the warped grayscale image
        warped_gray_path = args.output.replace('.png', '_warped_gray.png')
        cv2.imwrite(warped_gray_path, results['warped_gray'])
        print(f"Saved warped grayscale image to: {warped_gray_path}")
    
    # Display the images if debug mode is enabled
    if args.debug:
        # Resize images for display
        max_height = 800
        warped_color = results['warped_color']
        h, w = warped_color.shape[:2]
        if h > max_height:
            scale = max_height / h
            warped_color = cv2.resize(warped_color, (int(w * scale), max_height))
        
        # Show the warped color image
        cv2.imshow('Warped Document', warped_color)
        print("\nPress any key to exit...")
        cv2.waitKey(0)
        cv2.destroyAllWindows()
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
