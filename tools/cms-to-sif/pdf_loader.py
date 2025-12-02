"""
PDF loading and text extraction utilities.

This module handles reading PDF files and extracting text content,
with support for both text-based and image-based PDFs.
"""

import io
from typing import Tuple, Optional
from pypdf import PdfReader, PdfWriter


class PdfLoadError(Exception):
    """Custom exception for PDF loading errors."""
    pass


def extract_pdf_text(pdf_bytes: bytes) -> Tuple[str, bool]:
    """
    Extract text content from a PDF file.
    
    Args:
        pdf_bytes: Raw PDF file bytes
        
    Returns:
        Tuple of (extracted_text, needs_ocr)
        - extracted_text: The text content extracted from the PDF
        - needs_ocr: Boolean indicating if OCR is likely needed (very little text found)
        
    Raises:
        PdfLoadError: If the PDF cannot be read
    """
    try:
        reader = PdfReader(io.BytesIO(pdf_bytes))
        text_chunks = []
        
        for page_num, page in enumerate(reader.pages):
            try:
                text = page.extract_text() or ""
                text_chunks.append(text)
            except Exception as e:
                print(f"Warning: Could not extract text from page {page_num + 1}: {e}")
                text_chunks.append("")
        
        full_text = "\n".join(text_chunks)
        
        # Heuristic: if we got very little text, probably need OCR
        # Consider < 100 chars or mostly whitespace as "needs OCR"
        stripped_text = full_text.strip()
        needs_ocr = len(stripped_text) < 100
        
        return full_text, needs_ocr
        
    except Exception as e:
        raise PdfLoadError(f"Failed to read PDF: {str(e)}")


def load_pdf_reader(pdf_bytes: bytes) -> PdfReader:
    """
    Load a PDF and return a PdfReader object.
    
    Args:
        pdf_bytes: Raw PDF file bytes
        
    Returns:
        PdfReader object for the PDF
        
    Raises:
        PdfLoadError: If the PDF cannot be loaded
    """
    try:
        return PdfReader(io.BytesIO(pdf_bytes))
    except Exception as e:
        raise PdfLoadError(f"Failed to load PDF: {str(e)}")


def get_pdf_metadata(pdf_bytes: bytes) -> dict:
    """
    Extract metadata from a PDF file.
    
    Args:
        pdf_bytes: Raw PDF file bytes
        
    Returns:
        Dictionary containing PDF metadata (title, author, pages, etc.)
    """
    try:
        reader = PdfReader(io.BytesIO(pdf_bytes))
        metadata = {
            "page_count": len(reader.pages),
            "is_encrypted": reader.is_encrypted,
        }
        
        # Add document info if available
        if reader.metadata:
            metadata.update({
                "title": reader.metadata.get("/Title", ""),
                "author": reader.metadata.get("/Author", ""),
                "subject": reader.metadata.get("/Subject", ""),
                "creator": reader.metadata.get("/Creator", ""),
                "producer": reader.metadata.get("/Producer", ""),
            })
        
        return metadata
        
    except Exception as e:
        return {"error": str(e)}


def get_form_fields(pdf_bytes: bytes) -> dict:
    """
    Extract form field names and types from a PDF with AcroForm.
    
    Args:
        pdf_bytes: Raw PDF file bytes
        
    Returns:
        Dictionary mapping field names to field information
    """
    try:
        reader = PdfReader(io.BytesIO(pdf_bytes))
        
        if reader.get_fields() is None:
            return {}
        
        fields = {}
        for field_name, field_data in reader.get_fields().items():
            fields[field_name] = {
                "type": field_data.get("/FT", "Unknown"),
                "value": field_data.get("/V", ""),
                "default": field_data.get("/DV", ""),
            }
        
        return fields
        
    except Exception as e:
        print(f"Warning: Could not extract form fields: {e}")
        return {}


def clone_pdf_for_writing(pdf_bytes: bytes) -> PdfWriter:
    """
    Create a PdfWriter by cloning an existing PDF.
    
    Args:
        pdf_bytes: Raw PDF file bytes to clone
        
    Returns:
        PdfWriter object ready for modification
        
    Raises:
        PdfLoadError: If the PDF cannot be cloned
    """
    try:
        reader = PdfReader(io.BytesIO(pdf_bytes))
        writer = PdfWriter()
        writer.clone_document_from_reader(reader)
        return writer
        
    except Exception as e:
        raise PdfLoadError(f"Failed to clone PDF for writing: {str(e)}")


def save_pdf_to_bytes(writer: PdfWriter) -> bytes:
    """
    Save a PdfWriter to bytes.
    
    Args:
        writer: PdfWriter object to save
        
    Returns:
        PDF file as bytes
    """
    output = io.BytesIO()
    writer.write(output)
    return output.getvalue()


# OCR support placeholder - to be implemented if needed
def extract_text_with_ocr(pdf_bytes: bytes) -> str:
    """
    Extract text from image-based PDF using OCR.
    
    This is a placeholder for OCR functionality. In a browser environment,
    this would use Tesseract.js or a similar WebAssembly-based OCR solution.
    
    Args:
        pdf_bytes: Raw PDF file bytes
        
    Returns:
        Extracted text from OCR
        
    Note:
        This requires additional dependencies and setup for browser-based OCR.
        Consider using Tesseract.js integrated with PyScript.
    """
    # TODO: Implement OCR using Tesseract.js via JavaScript interop
    # For now, return a placeholder message
    return "[OCR not yet implemented - text-based PDFs only]"
