"""
CMS Report parser - extracts structured data from CMS report text.

This module uses regex patterns and heuristics to find and extract
key information from CMS (Commissioning/Maintenance Service) reports.
"""

import re
from typing import Optional, Dict, List
from models import CmsReportData


class CmsParseError(Exception):
    """Custom exception for CMS parsing errors."""
    pass


def parse_cms_report(text: str, debug: bool = False) -> CmsReportData:
    """
    Parse CMS report text and extract structured data.
    
    Args:
        text: Raw text extracted from CMS report PDF
        debug: If True, print debug information during parsing
        
    Returns:
        CmsReportData object with extracted information
    """
    if debug:
        print("Starting CMS report parsing...")
        print(f"Text length: {len(text)} characters")
    
    def find(pattern: str, flags: int = re.IGNORECASE, default: Optional[str] = None) -> Optional[str]:
        """Find a value using regex pattern."""
        match = re.search(pattern, text, flags)
        if match:
            value = match.group(1).strip()
            if debug:
                print(f"Found match: {pattern[:50]}... = {value}")
            return value
        return default
    
    def find_all(pattern: str, flags: int = re.IGNORECASE) -> List[str]:
        """Find all matches for a pattern."""
        matches = re.findall(pattern, text, flags)
        return [m.strip() for m in matches if m.strip()]
    
    # Wind farm and turbine information
    wind_farm = find(r"(?:Wind\s*Farm|WF|Farm\s*Name)[:\s]+([^\n]+)")
    turbine_number = find(r"(?:Turbine\s*Number|WTG|Wind\s*Turbine)[:\s#]*([A-Z0-9\-]+)")
    turbine_type = find(r"(?:Turbine\s*Type|Model|Type)[:\s]+([^\n]+)")
    
    # Location information
    location = find(r"(?:Location|Site|Address)[:\s]+([^\n]+)")
    site_address = find(r"(?:Site\s*Address|Address)[:\s]+([^\n]+)")
    
    # Service information
    service_life_year = find(r"(?:Service\s*Life\s*Year|SLY|Year)[:\s]+(\d{4})")
    
    # Personnel
    technicians_list = find_all(r"(?:Technician|Tech)[:\s]*([A-Z][a-z]+\s+[A-Z][a-z]+)")
    technicians = ", ".join(technicians_list) if technicians_list else find(r"(?:Technician|Service\s*Tech)[:\s]+([^\n]+)")
    service_manager = find(r"(?:Service\s*Manager|Manager|Supervisor)[:\s]+([^\n]+)")
    
    # Dates
    commissioning_date = find(r"(?:Commissioning\s*Date|Commission\s*Date)[:\s]+([0-9\/\-\.]+)")
    service_date = find(r"(?:Service\s*Date|Inspection\s*Date|Date)[:\s]+([0-9\/\-\.]+)")
    
    # Technical details - Network information
    ddaus_mac = find(r"(?:MAC\s*Address|DDAU\s*MAC|MAC)[:\s]+([A-F0-9:]+)", re.IGNORECASE)
    ip_address = find(r"(?:IP\s*Address|IP)[:\s]+(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})")
    gateway = find(r"(?:Default\s*Gateway|Gateway)[:\s]+(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})")
    controller_type = find(r"(?:Controller\s*Type|Controller)[:\s]+([^\n]+)")
    das_server = find(r"(?:DAS\s*Server|Server)[:\s]+([^\n]+)")
    serial_number = find(r"(?:Serial\s*Number|S/N|Serial)[:\s]+([A-Z0-9\-]+)")
    firmware_version = find(r"(?:Firmware\s*Version|FW\s*Version|Firmware)[:\s]+([0-9\.]+)")
    
    # Extract Name field which might contain turbine info
    name_field = find(r"(?:^Name|Name)[:\s]+([^\n]+)", re.MULTILINE)
    if name_field and not turbine_number:
        turbine_number = name_field
    
    # Extract Number field which might be wind farm number
    number_field = find(r"(?:^Number|Number)[:\s]+([^\n]+)", re.MULTILINE)
    if number_field and not wind_farm:
        wind_farm = number_field
    
    # Create and return structured data
    cms_data = CmsReportData(
        wind_farm=wind_farm or number_field,
        turbine_number=turbine_number or name_field,
        turbine_type=turbine_type,
        location=location or site_address,
        service_life_year=service_life_year,
        technicians=technicians,
        service_manager=service_manager,
        commissioning_date=commissioning_date,
        service_date=service_date,
        ddaus_mac=ddaus_mac,
        ip_address=ip_address,
        turbine_ip=ip_address,
        gateway=gateway,
        controller_type=controller_type,
        das_server=das_server,
        serial_number=serial_number,
        firmware_version=firmware_version,
        raw_text=text
    )
    
    if debug:
        print("\nExtraction complete. Summary:")
        for key, value in cms_data.to_dict().items():
            print(f"  {key}: {value}")
    
    return cms_data
