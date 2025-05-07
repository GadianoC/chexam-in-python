from kivy.uix.floatlayout import FloatLayout
from kivy.uix.image import Image
from kivy.graphics.texture import Texture
from kivy.clock import Clock
import cv2
import numpy as np
import logging
from ..processing.image_processing import process_document_pipeline

class CameraWidget(FloatLayout):
    def __init__(self, capture_callback, **kwargs):
        super().__init__(**kwargs)
        # Set up logging
        self.logger = logging.getLogger("chexam.ui.camera_widget")
        self.logger.setLevel(logging.INFO)
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('[%(levelname)s] %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            
        # Main camera image with contour overlay
        self.image = Image(size_hint=(1, 1), allow_stretch=True, keep_ratio=True)
        self.add_widget(self.image)
        
        # Camera state variables
        self.capture_callback = capture_callback
        self.capture = None
        self.current_frame = None
        self._update_ev = None


    def update(self, dt):
        if self.capture is None:
            return
            
        ret, frame = self.capture.read()
        if ret:
            self.current_frame = frame.copy()
            
                # Create a visualization image for display
            try:
                display_frame = frame.copy()
                
  
                _, _, pts = process_document_pipeline(frame, debug=False)
                
                if pts is not None and hasattr(pts, 'shape') and pts.shape == (4, 2):
                    pts_int = pts.astype(np.int32).reshape((-1, 1, 2))
                    
                    # Draw the document contour
                    cv2.polylines(display_frame, [pts_int], isClosed=True, color=(0, 255, 0), thickness=3)
                    
                    # Add corner points
                    for pt in pts_int:
                        cv2.circle(display_frame, (pt[0][0], pt[0][1]), 10, (0, 0, 255), -1)
                    
                    # Add text to indicate document is detected
                    cv2.putText(display_frame, "Document Detected", (20, 40), 
                                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                else:
                    # Add text to indicate no document is detected
                    cv2.putText(display_frame, "No Document Detected", (20, 40), 
                                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                
                # Convert the frame to a texture for display
                buf = cv2.flip(display_frame, 0).tobytes()
                image_texture = Texture.create(
                    size=(display_frame.shape[1], display_frame.shape[0]), colorfmt='bgr')
                image_texture.blit_buffer(buf, colorfmt='bgr', bufferfmt='ubyte')
                self.image.texture = image_texture
                
            except Exception as e:
                self.logger.error(f"Failed to process frame: {e}")
                # If processing fails, just display the original frame
                buf = cv2.flip(frame, 0).tobytes()
                image_texture = Texture.create(
                    size=(frame.shape[1], frame.shape[0]), colorfmt='bgr')
                image_texture.blit_buffer(buf, colorfmt='bgr', bufferfmt='ubyte')
                self.image.texture = image_texture


    def capture_image(self, *args):
        if self.current_frame is not None:
            # Save the captured frame for debugging
            import cv2, time
            ts = int(time.time() * 1000)
            cv2.imwrite(f"captured_frame_{ts}.png", self.current_frame)
            self.capture_callback(self.current_frame)
            self.stop_camera()

    def start_camera(self):
        if self.capture is None:
            self.capture = cv2.VideoCapture(0)
            self._update_ev = Clock.schedule_interval(self.update, 1.0 / 30)

    def stop_camera(self):
        if self.capture is not None:
            self.capture.release()
            self.capture = None
        if self._update_ev is not None:
            self._update_ev.cancel()
            self._update_ev = None

    def on_stop(self):
        self.stop_camera()
        
