"""
SIF (Service Inspection Form) PDF filler.

This module takes extracted CMS data and fills it into a SIF PDF template
by setting AcroForm field values.
"""

import io
from typing import Dict, List, Tuple, Optional
from pypdf import PdfReader, PdfWriter

from models import CmsReportData, CMS_TO_SIF_MAP


class SifFillError(Exception):
    """Custom exception for SIF filling errors."""
    pass


def get_sif_field_names(sif_template_bytes: bytes) -> List[str]:
    """
    Extract all field names from a SIF PDF template.
    
    Args:
        sif_template_bytes: Raw bytes of the SIF PDF template
        
    Returns:
        Sorted list of field names in the SIF template
        
    Raises:
        SifFillError: If the PDF cannot be read or has no fields
    """
    try:
        reader = PdfReader(io.BytesIO(sif_template_bytes))
        
        # Check if PDF has form fields
        fields = reader.get_fields()
        if fields is None:
            raise SifFillError("SIF template does not contain form fields (AcroForm)")
        
        return sorted(fields.keys())
        
    except SifFillError:
        raise
    except Exception as e:
        raise SifFillError(f"Failed to read SIF field names: {str(e)}")


def cms_to_sif_field_values(cms: CmsReportData, custom_mapping: Optional[Dict[str, str]] = None) -> Dict[str, str]:
    """
    Convert CMS report data to SIF PDF field values.
    
    Args:
        cms: Parsed CMS report data
        custom_mapping: Optional custom mapping to use instead of default CMS_TO_SIF_MAP
        
    Returns:
        Dictionary mapping SIF field names to values
    """
    mapping = custom_mapping if custom_mapping is not None else CMS_TO_SIF_MAP
    
    cms_dict = cms.to_dict()
    sif_values = {}
    
    for cms_field, sif_field in mapping.items():
        value = cms_dict.get(cms_field)
        if value:
            sif_values[sif_field] = str(value)
    
    return sif_values


def fill_sif_form(
    sif_template_bytes: bytes,
    field_values: Dict[str, str],
    flatten: bool = False
) -> bytes:
    """
    Fill a SIF PDF form with provided values.
    
    Args:
        sif_template_bytes: Raw bytes of the blank SIF PDF template
        field_values: Dictionary mapping field names to values
        flatten: If True, flatten the form (make it non-editable) after filling
        
    Returns:
        Filled PDF as bytes
        
    Raises:
        SifFillError: If the PDF cannot be filled
    """
    try:
        reader = PdfReader(io.BytesIO(sif_template_bytes))
        writer = PdfWriter()
        
        # Clone the template
        writer.clone_document_from_reader(reader)
        
        # Check if PDF has form fields
        if writer.get_fields() is None:
            raise SifFillError("SIF template does not contain form fields (AcroForm)")
        
        # Fill in the values
        for field_name, value in field_values.items():
            try:
                # Update field value for all pages
                writer.update_page_form_field_values(
                    writer.pages,
                    {field_name: value}
                )
            except KeyError:
                # Field doesn't exist in this PDF - log but continue
                print(f"Warning: Field '{field_name}' not found in SIF template")
            except Exception as e:
                print(f"Warning: Could not set field '{field_name}': {e}")
        
        # Optionally flatten the form
        if flatten:
            # Note: pypdf doesn't have direct flatten support in all versions
            # This is a placeholder - may need alternative approach
            pass
        
        # Save to bytes
        output = io.BytesIO()
        writer.write(output)
        return output.getvalue()
        
    except SifFillError:
        raise
    except Exception as e:
        raise SifFillError(f"Failed to fill SIF form: {str(e)}")


def get_unfilled_fields(sif_template_bytes: bytes, field_values: Dict[str, str]) -> List[str]:
    """
    Get list of fields in the SIF that weren't filled.
    
    Args:
        sif_template_bytes: Raw bytes of the SIF PDF template
        field_values: Dictionary of values that were filled
        
    Returns:
        List of field names that exist in SIF but weren't filled
    """
    try:
        reader = PdfReader(io.BytesIO(sif_template_bytes))
        
        if reader.get_fields() is None:
            return []
        
        sif_field_names = set(reader.get_fields().keys())
        filled_field_names = set(field_values.keys())
        
        unfilled = list(sif_field_names - filled_field_names)
        return sorted(unfilled)
        
    except Exception as e:
        print(f"Warning: Could not get unfilled fields: {e}")
        return []


def get_mapping_report(
    cms: CmsReportData,
    sif_template_bytes: bytes,
    custom_mapping: Optional[Dict[str, str]] = None
) -> Dict[str, any]:
    """
    Generate a detailed report of the mapping between CMS and SIF.
    
    Args:
        cms: Parsed CMS report data
        sif_template_bytes: Raw bytes of the SIF PDF template
        custom_mapping: Optional custom mapping to use
        
    Returns:
        Dictionary with mapping statistics and details
    """
    try:
        # Get CMS extracted fields
        cms_fields = cms.to_dict()
        
        # Get SIF form fields
        reader = PdfReader(io.BytesIO(sif_template_bytes))
        sif_fields = reader.get_fields() if reader.get_fields() else {}
        
        # Get mapped values
        sif_values = cms_to_sif_field_values(cms, custom_mapping)
        
        # Calculate statistics
        total_cms_fields = len(cms_fields)
        total_sif_fields = len(sif_fields)
        mapped_fields = len(sif_values)
        
        mapping = custom_mapping if custom_mapping is not None else CMS_TO_SIF_MAP
        
        # Find unmapped CMS fields
        unmapped_cms = [
            field for field in cms_fields.keys()
            if field not in mapping
        ]
        
        # Find unfilled SIF fields
        unfilled_sif = get_unfilled_fields(sif_template_bytes, sif_values)
        
        return {
            "cms_extraction": {
                "total_fields": total_cms_fields,
                "extracted_fields": list(cms_fields.keys())
            },
            "sif_form": {
                "total_fields": total_sif_fields,
                "field_names": list(sif_fields.keys())
            },
            "mapping": {
                "total_mappings": len(mapping),
                "successfully_mapped": mapped_fields,
                "mapping_details": sif_values
            },
            "gaps": {
                "unmapped_cms_fields": unmapped_cms,
                "unfilled_sif_fields": unfilled_sif
            },
            "coverage": {
                "cms_coverage": f"{(mapped_fields / total_cms_fields * 100):.1f}%" if total_cms_fields > 0 else "N/A",
                "sif_coverage": f"{(mapped_fields / total_sif_fields * 100):.1f}%" if total_sif_fields > 0 else "N/A"
            }
        }
        
    except Exception as e:
        return {
            "error": f"Could not generate mapping report: {str(e)}"
        }


def validate_sif_fields(sif_template_bytes: bytes, expected_fields: List[str]) -> Tuple[bool, List[str]]:
    """
    Validate that expected fields exist in the SIF template.
    
    Args:
        sif_template_bytes: Raw bytes of the SIF PDF template
        expected_fields: List of field names that should exist
        
    Returns:
        Tuple of (all_present, missing_fields)
    """
    try:
        reader = PdfReader(io.BytesIO(sif_template_bytes))
        
        if reader.get_fields() is None:
            return False, expected_fields
        
        actual_fields = set(reader.get_fields().keys())
        missing = [field for field in expected_fields if field not in actual_fields]
        
        return len(missing) == 0, missing
        
    except Exception as e:
        print(f"Error validating SIF fields: {e}")
        return False, expected_fields


def create_filled_sif(
    cms: CmsReportData,
    sif_template_bytes: bytes,
    custom_mapping: Optional[Dict[str, str]] = None,
    flatten: bool = False,
    debug: bool = False
) -> Tuple[bytes, Dict[str, any]]:
    """
    Complete workflow: convert CMS data to filled SIF PDF.
    
    Args:
        cms: Parsed CMS report data
        sif_template_bytes: Raw bytes of the blank SIF PDF template
        custom_mapping: Optional custom field mapping
        flatten: Whether to flatten the form after filling
        debug: If True, return detailed mapping report
        
    Returns:
        Tuple of (filled_pdf_bytes, report_dict)
        report_dict contains mapping statistics and any warnings
    """
    # Convert CMS to SIF field values
    sif_values = cms_to_sif_field_values(cms, custom_mapping)
    
    if debug:
        print(f"Mapped {len(sif_values)} fields from CMS to SIF")
    
    # Fill the SIF form
    filled_pdf = fill_sif_form(sif_template_bytes, sif_values, flatten)
    
    # Generate report
    report = get_mapping_report(cms, sif_template_bytes, custom_mapping)
    
    if debug:
        print("\nMapping Report:")
        print(f"  CMS fields extracted: {report['cms_extraction']['total_fields']}")
        print(f"  SIF fields available: {report['sif_form']['total_fields']}")
        print(f"  Fields successfully mapped: {report['mapping']['successfully_mapped']}")
        print(f"  CMS coverage: {report['coverage']['cms_coverage']}")
        print(f"  SIF coverage: {report['coverage']['sif_coverage']}")
    
    return filled_pdf, report
