"""
Main application logic for CMS to SIF conversion.

This module orchestrates the complete workflow:
1. Load and extract text from CMS report PDF
2. Parse CMS data using regex patterns
3. Map CMS data to SIF fields
4. Fill SIF template with extracted data
5. Return completed SIF PDF
"""

from typing import Tuple, Optional, Dict
from models import CmsReportData
from pdf_loader import extract_pdf_text, PdfLoadError, extract_text_with_ocr
from cms_parser import parse_cms_report
from sif_filler import create_filled_sif, SifFillError


class ConversionError(Exception):
    """Custom exception for conversion workflow errors."""
    pass


def process_cms_report(cms_pdf_bytes: bytes, debug: bool = False) -> CmsReportData:
    """
    Process a CMS report PDF and extract structured data.
    
    Args:
        cms_pdf_bytes: Raw bytes of the CMS report PDF
        debug: If True, print debug information
        
    Returns:
        CmsReportData object with extracted information
        
    Raises:
        ConversionError: If processing fails
    """
    try:
        # Extract text from PDF
        if debug:
            print("Extracting text from CMS report PDF...")
        
        text, needs_ocr = extract_pdf_text(cms_pdf_bytes)
        
        if needs_ocr:
            if debug:
                print("Warning: Very little text extracted. PDF may be image-based.")
                print("Attempting OCR (if available)...")
            
            # Try OCR as fallback
            ocr_text = extract_text_with_ocr(cms_pdf_bytes)
            if ocr_text and not ocr_text.startswith("[OCR not yet implemented"):
                text = ocr_text
            else:
                if debug:
                    print("Warning: OCR not available. Proceeding with limited text.")
        
        if debug:
            print(f"Extracted {len(text)} characters of text")
            print("\nFirst 500 characters:")
            print(text[:500])
            print("\n" + "="*50 + "\n")
        
        # Parse CMS data
        if debug:
            print("Parsing CMS report data...")
        
        cms_data = parse_cms_report(text, debug=debug)
        
        return cms_data
        
    except PdfLoadError as e:
        raise ConversionError(f"Failed to load CMS PDF: {str(e)}")
    except Exception as e:
        raise ConversionError(f"Failed to process CMS report: {str(e)}")


def create_sif_from_cms(
    cms_data: CmsReportData,
    sif_template_bytes: bytes,
    custom_mapping: Optional[Dict[str, str]] = None,
    flatten: bool = False,
    debug: bool = False
) -> Tuple[bytes, Dict[str, any]]:
    """
    Create a filled SIF PDF from extracted CMS data.
    
    Args:
        cms_data: Parsed CMS report data
        sif_template_bytes: Raw bytes of the blank SIF template PDF
        custom_mapping: Optional custom field mapping (CMS field -> SIF field)
        flatten: If True, flatten the form (make it non-editable)
        debug: If True, print debug information
        
    Returns:
        Tuple of (filled_sif_pdf_bytes, mapping_report)
        
    Raises:
        ConversionError: If SIF generation fails
    """
    try:
        if debug:
            print("\nGenerating filled SIF from CMS data...")
        
        # Create filled SIF
        filled_pdf, report = create_filled_sif(
            cms_data,
            sif_template_bytes,
            custom_mapping=custom_mapping,
            flatten=flatten,
            debug=debug
        )
        
        if debug:
            print("\n✓ SIF PDF generated successfully")
            print(f"  Output size: {len(filled_pdf)} bytes")
        
        return filled_pdf, report
        
    except SifFillError as e:
        raise ConversionError(f"Failed to fill SIF template: {str(e)}")
    except Exception as e:
        raise ConversionError(f"Failed to generate SIF: {str(e)}")


def convert_cms_to_sif(
    cms_pdf_bytes: bytes,
    sif_template_bytes: bytes,
    custom_mapping: Optional[Dict[str, str]] = None,
    flatten: bool = False,
    debug: bool = False
) -> Tuple[bytes, Dict[str, any]]:
    """
    Complete workflow: Convert a CMS report PDF into a filled SIF PDF.
    
    This is the main entry point for the conversion process. It combines
    all steps: extraction, parsing, mapping, and filling.
    
    Args:
        cms_pdf_bytes: Raw bytes of the CMS report PDF
        sif_template_bytes: Raw bytes of the blank SIF template PDF
        custom_mapping: Optional custom field mapping
        flatten: If True, flatten the form after filling
        debug: If True, print detailed debug information
        
    Returns:
        Tuple of (filled_sif_pdf_bytes, detailed_report)
        The report contains extraction stats and mapping information
        
    Raises:
        ConversionError: If any step of the conversion fails
        
    Example:
        >>> with open('cms_report.pdf', 'rb') as f:
        ...     cms_bytes = f.read()
        >>> with open('sif_template.pdf', 'rb') as f:
        ...     sif_bytes = f.read()
        >>> filled_sif, report = convert_cms_to_sif(cms_bytes, sif_bytes, debug=True)
        >>> with open('filled_sif.pdf', 'wb') as f:
        ...     f.write(filled_sif)
    """
    if debug:
        print("="*60)
        print("CMS to SIF Conversion Workflow")
        print("="*60)
    
    # Step 1: Process CMS report
    cms_data = process_cms_report(cms_pdf_bytes, debug=debug)
    
    # Step 2: Create filled SIF
    filled_sif, report = create_sif_from_cms(
        cms_data,
        sif_template_bytes,
        custom_mapping=custom_mapping,
        flatten=flatten,
        debug=debug
    )
    
    if debug:
        print("\n" + "="*60)
        print("Conversion Complete!")
        print("="*60)
    
    return filled_sif, report


# Convenience functions for web interface
def get_cms_preview(cms_pdf_bytes: bytes) -> Dict[str, any]:
    """
    Extract and preview CMS data without generating SIF.
    Useful for web UI to show extracted data before final conversion.
    
    Args:
        cms_pdf_bytes: Raw bytes of the CMS report PDF
        
    Returns:
        Dictionary with extracted data and summary
    """
    try:
        cms_data = process_cms_report(cms_pdf_bytes, debug=False)
        summary = get_extraction_summary(cms_data)
        
        return {
            "success": True,
            "data": cms_data.to_dict(),
            "summary": summary
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def validate_sif_template(sif_template_bytes: bytes) -> Dict[str, any]:
    """
    Validate that a SIF template is suitable for filling.
    
    Args:
        sif_template_bytes: Raw bytes of the SIF template PDF
        
    Returns:
        Dictionary with validation results and field information
    """
    try:
        from pdf_loader import get_form_fields, get_pdf_metadata
        
        metadata = get_pdf_metadata(sif_template_bytes)
        fields = get_form_fields(sif_template_bytes)
        
        is_valid = len(fields) > 0
        
        return {
            "success": True,
            "is_valid": is_valid,
            "field_count": len(fields),
            "fields": list(fields.keys()),
            "metadata": metadata,
            "message": "Valid SIF template" if is_valid else "No form fields found in PDF"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
