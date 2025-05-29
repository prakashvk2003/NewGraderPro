from typing import List
from PIL import Image
import requests
import base64
from io import BytesIO

from stopOllamaModel import stop_ollama_model

def image_to_text(images: List[Image.Image]) -> str:
    ollama_api_url = "http://localhost:11434/api/generate"
    all_text = ""
    session = requests.Session()
    
    try:
        for image in images:
            buffer = BytesIO()
            image.save(buffer, format="PNG")
            base64_image = base64.b64encode(buffer.getvalue()).decode("utf-8")
            buffer.close()
            
            payload = {
                "model": "granite3.2-vision:2b",
                "prompt": "Extract all text from this image. Return only the extracted text with no additional commentary.",
                "images": [base64_image],
                "stream": False
            }
            
            response = session.post(ollama_api_url, json=payload)
            
            if response.status_code == 200:
                result = response.json()
                extracted_text = result.get("response", "")
                all_text += extracted_text + "\n\n"
            else:
                print(f"Error: OCR request failed with status code {response.status_code}")
                print(f"Response: {response.text}")
            
            del base64_image
        
        return all_text.strip()
    finally:
        try:
            stop_ollama_model("granite3.2-vision:2b")
        except Exception as e:
            print(f"Warning: Failed to release Ollama model resources: {e}")
        finally:
            session.close()