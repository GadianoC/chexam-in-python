from .camera_widget import CameraWidget
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.metrics import dp
from ..processing.image_processing import process_document_pipeline
from ..processing.answer_detection import detect_bubbles
from .base_screen import BaseScreen
import cv2
import numpy as np
import logging

class ScannerScreen(BaseScreen):
    def __init__(self, **kwargs):
        super().__init__(title="Scanner", **kwargs)
        self.set_back_destination('home')
        
        scanner_layout = BoxLayout(orientation='vertical', spacing=dp(10))
        
        self.status_label = Label(
            text='Ready to scan bubble sheet', 
            size_hint_y=None, 
            height=dp(40),
            font_size=dp(18),
            color=(0.2, 0.6, 1, 1)
        )
        scanner_layout.add_widget(self.status_label)
        
        camera_area = FloatLayout(size_hint_y=None, height=dp(500))
        self.camera_widget = CameraWidget(self.on_image_captured, size_hint=(1, 1))
        camera_area.add_widget(self.camera_widget)
        scanner_layout.add_widget(camera_area)
        
        btn_row = BoxLayout(size_hint_y=None, height=dp(80), padding=[dp(20), dp(10), dp(20), dp(10)])
        self.capture_btn = Button(
            text='Capture Photo',
            font_size=dp(22),
            background_normal='',
            background_color=(0.2, 0.6, 1, 1),
            color=(1, 1, 1, 1)
        )
        self.capture_btn.bind(on_press=self.capture_image)
        btn_row.add_widget(self.capture_btn)
        scanner_layout.add_widget(btn_row)
        
        self.content_area.add_widget(scanner_layout)
        
    def preprocess_for_bubble_detection(self, gray_img):
        """
        Specialized preprocessing method optimized for bubble detection.
        Preserves shaded and unshaded bubbles for better visualization.
        
        Args:
            gray_img: Grayscale input image
            
        Returns:
            Grayscale image optimized for bubble detection with visible shading
        """
        import cv2
        import numpy as np
        
        processed = gray_img.copy()
        
        # Step 1: Apply CLAHE for better contrast
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        processed = clahe.apply(processed)
        
        # Step 2: Apply light Gaussian blur to reduce noise while preserving bubble shading
        processed = cv2.GaussianBlur(processed, (3, 3), 0)
        
        # Step 3: Enhance contrast to make bubbles more visible
        alpha = 1.3  
        beta = 10    
        processed = cv2.convertScaleAbs(processed, alpha=alpha, beta=beta)
        
        # Step 4: Apply sharpening to make bubble edges more defined
        kernel = np.array([[-1, -1, -1],
                           [-1,  9, -1],
                           [-1, -1, -1]])
        processed = cv2.filter2D(processed, -1, kernel)
        
        # Return the processed grayscale image (not binary)
        # preserves the shading information in the bubbles
        return processed

    def on_enter(self, *args):
        self.camera_widget.start_camera()

    def on_leave(self, *args):
        self.camera_widget.stop_camera()

    def on_image_captured(self, frame):
        logger = logging.getLogger("chexam.ui.scanner_screen")
        logger.setLevel(logging.INFO)
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('[%(levelname)s] %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            
        self.status_label.text = 'Processing...'
        logger.info('on_image_captured called')
        from kivy.app import App
        import time
        import os
        
        # Debug path (set to None to disable debug image saving)
        debug_path = None
        
        if frame is None:
            print('[ERROR] No frame received from camera_widget!')
            logger.error('No frame received from camera_widget!')
            self.status_label.text = 'Camera error.'
            return
            
        logger.info('Running process_document_pipeline')
        warped_color, warped_gray, sheet_pts = process_document_pipeline(frame, debug_save_path=debug_path, debug=False)
        
        # Generate a binary version optimized for bubble detection
        from ..processing.ocr_processing import preprocess_for_ocr
        
        warped_thresh = self.preprocess_for_bubble_detection(warped_gray)
        
        # Disable saving processed image for reference
        if debug_path is not None:
            cv2.imwrite(debug_path.replace('.png', '_bubble_optimized.png'), warped_thresh)
        
        if warped_gray is not None:
            logger.info('Document detected and processed successfully')
            # Show processed image screen
            app = App.get_running_app()
            sm = app.root
            logger.info(f'Got ScreenManager: {sm}')
            try:
                processed_screen = sm.get_screen('processed_image')
                logger.info('Got ProcessedImageScreen')
                processed_screen.set_image(warped_thresh, warped_color)
                logger.info('Set image on ProcessedImageScreen')
                processed_screen.set_back_destination('scanner')
                sm.current = 'processed_image'
                logger.info('Switched to processed_image screen')
                self.status_label.text = 'Processed image displayed.'
            except Exception as e:
                logger.error(f'Failed to switch to processed_image screen: {e}')
                self.status_label.text = 'Error displaying processed image.'
        else:
            logger.error('No processed image returned (warped_adapt is None)')
            self.status_label.text = 'Sheet not detected. Try again.'

    def capture_image(self, *args):
        self.on_image_captured(self.camera_widget.current_frame)
