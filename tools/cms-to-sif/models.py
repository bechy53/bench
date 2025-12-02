"""
Data models for CMS Report to SIF conversion.

This module defines the data structures used to extract information from 
CMS reports and map them to SIF (Service Inspection Form) PDF fields.
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, List


@dataclass
class CmsReportData:
    """
    Structured data extracted from a CMS (Commissioning/Maintenance Service) report.
    
    This class represents all the key information that can be extracted from
    a typical CMS report PDF document.
    """
    # Basic Information
    wind_farm: Optional[str] = None
    turbine_number: Optional[str] = None
    turbine_type: Optional[str] = None
    location: Optional[str] = None
    service_life_year: Optional[str] = None
    
    # Personnel
    technicians: Optional[str] = None
    service_manager: Optional[str] = None
    
    # Dates
    commissioning_date: Optional[str] = None
    service_date: Optional[str] = None
    
    # Technical details - Network/DDAU
    ddaus_mac: Optional[str] = None
    ip_address: Optional[str] = None
    turbine_ip: Optional[str] = None
    gateway: Optional[str] = None
    controller_type: Optional[str] = None
    das_server: Optional[str] = None
    serial_number: Optional[str] = None
    firmware_version: Optional[str] = None
    
    # Raw extracted text for debugging/reference
    raw_text: Optional[str] = None
    
    def to_dict(self) -> Dict[str, str]:
        """Convert to dictionary, excluding None values and raw_text."""
        return {
            k: v for k, v in self.__dict__.items() 
            if v is not None and k != 'raw_text'
        }


# Mapping configuration from CMS report fields to SIF PDF form field names
# This dictionary maps the CmsReportData attribute names to the actual
# AcroForm field names in the SIF PDF template.
# 
# Update these field names based on the actual field names in your SIF PDF.
# You can inspect the field names using pdf-lib or pypdf.

CMS_TO_SIF_MAP: Dict[str, str] = {
    # Basic mappings
    "wind_farm": "Wind farm number",
    "turbine_number": "Wind turbine number",
    "turbine_type": "Wind turbine type_2",
    "location": "Site location",
    "service_life_year": "Service life year",
    
    # Personnel mappings
    "technicians": "Service technician 1",
    "service_manager": "Service manager",
    
    # Date mappings
    "commissioning_date": "DateRow1",
    "service_date": "Date",
    
    # Technical mappings - DDAU/Network
    "ddaus_mac": "MAC address DDAU",
    "ip_address": "IP address DDAU",
    "turbine_ip": "IP address of the wind turbine",
    "gateway": "Gateway",
    "controller_type": "Controller type",
    "das_server": "DAS Server",
    
    # Serial numbers and versions
    "serial_number": "Serial number",
    "firmware_version": "Firmware version",
    
    # Equipment details
    "gearbox_info": "Gearbox manufacturer type and gearbox ratio",
    "generator_info": "Generator manufacturer and type",
    "main_bearing_info": "Main bearing manufacturer and type",
    "hub_height": "Hub height optional",
    "owner": "Owner optional",
    "service_car": "Service car number optional",
}


# Reverse mapping for looking up CMS fields from SIF field names
SIF_TO_CMS_MAP: Dict[str, str] = {v: k for k, v in CMS_TO_SIF_MAP.items()}


def get_field_mapping_info() -> Dict[str, Dict[str, str]]:
    """
    Get comprehensive mapping information for debugging and documentation.
    
    Returns:
        Dictionary with mapping details and statistics
    """
    return {
        "cms_to_sif": CMS_TO_SIF_MAP,
        "sif_to_cms": SIF_TO_CMS_MAP,
        "stats": {
            "total_mappings": len(CMS_TO_SIF_MAP),
            "cms_fields": list(CMS_TO_SIF_MAP.keys()),
            "sif_fields": list(CMS_TO_SIF_MAP.values())
        }
    }
