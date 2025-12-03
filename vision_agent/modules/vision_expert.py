import logging
import ollama
import cv2
import base64
import os
from datetime import datetime

class VisionExpert:
    def __init__(self):
        self.model = "llava" # Vision model
        self.analysis_model = "llama3.1" # For deeper reasoning about the image
        self.webcam_path = "webcam_input.jpg"
        self.screenshot_path = "vision_input.png"

    def capture_webcam(self) -> str:
        """Captures an image from the webcam."""
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            return None
        
        ret, frame = cap.read()
        cap.release()
        
        if ret:
            cv2.imwrite(self.webcam_path, frame)
            return self.webcam_path
        return None

    def analyze_image(self, image_path: str, prompt: str = "Describe this image in detail.") -> str:
        """
        Analyzes an image using LLaVA.
        """
        if not os.path.exists(image_path):
            return "Error: Image file not found."
            
        logging.info(f"👁️ Vision Expert: Analyzing {image_path} with prompt: '{prompt}'")
        
        try:
            with open(image_path, "rb") as f:
                image_bytes = f.read()
                
            response = ollama.generate(model=self.model, prompt=prompt, images=[image_bytes])
            description = response['response']
            
            return description
        except Exception as e:
            return f"Error analyzing image: {str(e)}"

    def deep_analysis(self, image_path: str, question: str) -> str:
        """
        Performs a two-step analysis: LLaVA describes -> Llama reasons.
        """
        # Step 1: See
        description = self.analyze_image(image_path, "Describe everything you see in this image in extreme detail.")
        
        # Step 2: Think
        prompt = f"""
        You are The Vision Expert.
        
        IMAGE DESCRIPTION:
        {description}
        
        USER QUESTION:
        "{question}"
        
        Based on the description, answer the user's question.
        """
        
        response = ollama.chat(model=self.analysis_model, messages=[{'role': 'user', 'content': prompt}])
        return response['message']['content']
