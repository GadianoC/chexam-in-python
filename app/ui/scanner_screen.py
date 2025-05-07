from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.image import Image
from .camera_widget import CameraWidget
from ..processing.image_processing import process_document_pipeline
from ..processing.answer_detection import detect_bubbles
import cv2
import numpy as np
import logging


class ScannerScreen(Screen):
    def __init__(self, switch_to_home=None, **kwargs):
        super().__init__(**kwargs)
        self.switch_to_home = switch_to_home

        # Main layout with FloatLayout to allow background image
        self.layout = FloatLayout()

        # Background Image
        self.background_image = Image(source='chexambg (1).png', allow_stretch=True, keep_ratio=False)
        self.layout.add_widget(self.background_image)

        # Foreground layout for UI elements
        foreground_layout = BoxLayout(orientation='vertical')

        # Status Label
        self.status_label = Label(text='Ready to scan bubble sheet', size_hint_y=0.08)
        foreground_layout.add_widget(self.status_label)

        # Camera Area
        camera_area = FloatLayout(size_hint_y=0.82)
        self.camera_widget = CameraWidget(self.on_image_captured, size_hint=(1, 1))
        camera_area.add_widget(self.camera_widget)
        foreground_layout.add_widget(camera_area)

        # Button Row
        btn_row = BoxLayout(size_hint_y=0.1)
        self.capture_btn = Button(text='Capture')
        self.capture_btn.bind(on_press=self.capture_image)
        btn_row.add_widget(self.capture_btn)

        self.back_btn = Button(text='Back')
        self.back_btn.bind(on_press=self.go_back)
        btn_row.add_widget(self.back_btn)

        foreground_layout.add_widget(btn_row)

        # Add foreground layout on top of the background
        self.layout.add_widget(foreground_layout)
        self.add_widget(self.layout)

    def go_back(self, *args):
        if callable(self.switch_to_home):
            self.switch_to_home()

    def preprocess_for_bubble_detection(self, gray_img):
        """
        Specialized preprocessing method optimized for bubble detection.
        Preserves shaded and unshaded bubbles for better visualization.

        Args:
            gray_img: Grayscale input image

        Returns:
            Grayscale image optimized for bubble detection with visible shading
        """
        # Step 1: Apply CLAHE for better contrast
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        processed = clahe.apply(gray_img)

        # Step 2: Apply light Gaussian blur to reduce noise while preserving bubble shading
        processed = cv2.GaussianBlur(processed, (3, 3), 0)

        # Step 3: Enhance contrast to make bubbles more visible
        alpha = 1.3  # Contrast control (1.0 means no change)
        beta = 10    # Brightness control (0 means no change)
        processed = cv2.convertScaleAbs(processed, alpha=alpha, beta=beta)

        # Step 4: Apply sharpening to make bubble edges more defined
        kernel = np.array([[-1, -1, -1],
                           [-1,  9, -1],
                           [-1, -1, -1]])
        processed = cv2.filter2D(processed, -1, kernel)

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

        if frame is None:
            logger.error('No frame received from camera_widget!')
            self.status_label.text = 'Camera error.'
            return

        try:
            # Create a timestamp for unique filenames
            import time
            ts = int(time.time() * 1000)
            debug_path = f"edge_capture_{ts}.png"

            logger.info('Running process_document_pipeline')
            warped_color, warped_gray, sheet_pts = process_document_pipeline(frame, debug_save_path=debug_path, debug=True)

            # Generate a binary version optimized for bubble detection
            warped_thresh = self.preprocess_for_bubble_detection(warped_gray)

            # Save the processed image for reference
            cv2.imwrite(debug_path.replace('.png', '_bubble_optimized.png'), warped_thresh)

            if warped_gray is not None:
                logger.info('Document detected and processed successfully')
                from kivy.app import App
                app = App.get_running_app()
                sm = app.root
                processed_screen = sm.get_screen('processed_image')
                processed_screen.set_image(warped_thresh, warped_color)
                processed_screen.set_on_back(lambda: setattr(sm, 'current', 'scanner'))
                sm.current = 'processed_image'
                self.status_label.text = 'Processed image displayed.'
            else:
                logger.error('No processed image returned (warped_gray is None)')
                self.status_label.text = 'Sheet not detected. Try again.'
        except Exception as e:
            logger.error(f'Error during image processing: {e}')
            self.status_label.text = 'Error processing image.'

    def capture_image(self, *args):
        self.on_image_captured(self.camera_widget.current_frame)
