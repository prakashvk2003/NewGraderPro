from typing import List
import pypdfium2 as pdfium
from PIL import Image

from TrOcr import image_to_text

def pdf_to_image(pdf_path: str) -> List[Image.Image]:
    pdf = pdfium.PdfDocument(pdf_path)
    page_count = len(pdf)
    images = []
    
    try:
        for page_number in range(page_count):
            page = pdf[page_number]
            bitmap = page.render(scale=1.5)
            pil_image = bitmap.to_pil()
            images.append(pil_image)
            bitmap.close()
            page.close()
        
        return images
    finally:
        pdf.close()


def extract_text_from_pdf(pdf_path: str) -> str:
    try:
        images = pdf_to_image(pdf_path)
        text = image_to_text(images)
        return text
    finally:
        for img in images:
            img.close()


if __name__ == "__main__":
    pdf_path = r"Sample\20.pdf"
    extracted_text = extract_text_from_pdf(pdf_path)
    print(extracted_text)