"""
PDF Processing Service
======================
Extract text and images from PDF invoices/receipts.
"""

import io
import base64
from typing import Optional


def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """
    Extract text from PDF using PyMuPDF.
    """
    try:
        import fitz  # PyMuPDF
    except ImportError:
        raise ImportError("PyMuPDF not installed. Run: pip install pymupdf")
    
    text_content = []
    
    # Open PDF from bytes
    pdf_document = fitz.open(stream=pdf_bytes, filetype="pdf")
    
    for page_num in range(len(pdf_document)):
        page = pdf_document[page_num]
        text = page.get_text()
        if text.strip():
            text_content.append(f"--- Page {page_num + 1} ---\n{text}")
    
    pdf_document.close()
    
    return "\n\n".join(text_content)


def extract_images_from_pdf(pdf_bytes: bytes) -> list[dict]:
    """
    Extract images from PDF for OCR processing.
    Returns list of {image_bytes, mime_type, page}
    """
    try:
        import fitz  # PyMuPDF
    except ImportError:
        raise ImportError("PyMuPDF not installed. Run: pip install pymupdf")
    
    images = []
    pdf_document = fitz.open(stream=pdf_bytes, filetype="pdf")
    
    for page_num in range(len(pdf_document)):
        page = pdf_document[page_num]
        image_list = page.get_images()
        
        for img_index, img in enumerate(image_list):
            xref = img[0]
            base_image = pdf_document.extract_image(xref)
            image_bytes = base_image["image"]
            image_ext = base_image["ext"]
            
            mime_type = f"image/{image_ext}"
            if image_ext == "jpg":
                mime_type = "image/jpeg"
            
            images.append({
                "image_bytes": image_bytes,
                "mime_type": mime_type,
                "page": page_num + 1,
                "index": img_index
            })
    
    pdf_document.close()
    
    return images


def pdf_page_to_image(pdf_bytes: bytes, page_num: int = 0, dpi: int = 200) -> bytes:
    """
    Convert a PDF page to image for OCR.
    Returns image bytes (PNG format).
    """
    try:
        import fitz  # PyMuPDF
    except ImportError:
        raise ImportError("PyMuPDF not installed. Run: pip install pymupdf")
    
    pdf_document = fitz.open(stream=pdf_bytes, filetype="pdf")
    
    if page_num >= len(pdf_document):
        page_num = 0
    
    page = pdf_document[page_num]
    
    # Render page to image
    zoom = dpi / 72  # 72 is default DPI
    matrix = fitz.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=matrix)
    
    # Get PNG bytes
    image_bytes = pix.tobytes("png")
    
    pdf_document.close()
    
    return image_bytes


def pdf_all_pages_to_images(pdf_bytes: bytes, dpi: int = 200) -> list[bytes]:
    """
    Convert all PDF pages to images.
    Returns list of image bytes (PNG format).
    """
    try:
        import fitz  # PyMuPDF
    except ImportError:
        raise ImportError("PyMuPDF not installed. Run: pip install pymupdf")
    
    images = []
    pdf_document = fitz.open(stream=pdf_bytes, filetype="pdf")
    
    zoom = dpi / 72
    matrix = fitz.Matrix(zoom, zoom)
    
    for page_num in range(len(pdf_document)):
        page = pdf_document[page_num]
        pix = page.get_pixmap(matrix=matrix)
        image_bytes = pix.tobytes("png")
        images.append(image_bytes)
    
    pdf_document.close()
    
    return images


def get_pdf_info(pdf_bytes: bytes) -> dict:
    """
    Get PDF metadata and info.
    """
    try:
        import fitz  # PyMuPDF
    except ImportError:
        raise ImportError("PyMuPDF not installed. Run: pip install pymupdf")
    
    pdf_document = fitz.open(stream=pdf_bytes, filetype="pdf")
    
    info = {
        "page_count": len(pdf_document),
        "metadata": pdf_document.metadata,
        "has_images": False,
        "has_text": False
    }
    
    # Check for text and images
    for page_num in range(len(pdf_document)):
        page = pdf_document[page_num]
        if page.get_text().strip():
            info["has_text"] = True
        if page.get_images():
            info["has_images"] = True
        if info["has_text"] and info["has_images"]:
            break
    
    pdf_document.close()
    
    return info
