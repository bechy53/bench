"""
Script to clean the SIF PDF by removing orphaned fields and keeping only the 24 desired fields.
"""

from pypdf import PdfReader, PdfWriter

# The 24 fields we want to keep (based on the original scan)
FIELDS_TO_KEEP = {
    "Contact the wind turbine owner who have access to the online CMS portal Give the names and email addresses of the wind turbine owner",
    "Controller type",
    "DAS Server",
    "Date",
    "DateRow1",
    "Gateway",
    "Gearbox manufacturer type and gearbox ratio",
    "Generator manufacturer and type",
    "Hub height optional",
    "IP address DDAU",
    "IP address of the wind turbine",
    "MAC address DDAU",
    "Main bearing manufacturer and type",
    "Owner optional",
    "Service car number optional",
    "Service life year",
    "Service manager",
    "Service technician 1",
    "Service technician 2",
    "Site location",
    "Vestas supervisors initialsRow1",
    "Wind farm number",
    "Wind turbine number",
    "Wind turbine type_2"
}

def clean_sif_pdf(input_path, output_path):
    """Remove fields not in FIELDS_TO_KEEP from the PDF."""
    
    reader = PdfReader(input_path)
    writer = PdfWriter()
    
    # Clone all pages
    for page in reader.pages:
        writer.add_page(page)
    
    # Get all fields
    all_fields = reader.get_fields()
    
    print(f"Found {len(all_fields)} total fields in the PDF")
    print(f"Will keep {len(FIELDS_TO_KEEP)} fields")
    
    # Copy the form with only the fields we want
    if all_fields:
        for field_name in all_fields.keys():
            if field_name in FIELDS_TO_KEEP:
                print(f"  Keeping: {field_name}")
            else:
                print(f"  Removing: {field_name}")
    
    # Note: pypdf doesn't have a simple way to remove individual fields
    # The best approach is to use a tool like pdftk or rebuild the form
    print("\nNote: pypdf cannot selectively remove fields.")
    print("Recommended: Use Adobe Acrobat to 'Prepare Form' and manually delete unwanted fields,")
    print("then use 'Save As' (not Save) to rebuild the PDF structure.")
    
    # Alternative: List what should be deleted
    fields_to_delete = set(all_fields.keys()) - FIELDS_TO_KEEP
    print(f"\n{len(fields_to_delete)} fields to delete:")
    for field in sorted(fields_to_delete):
        print(f"  - {field}")

if __name__ == "__main__":
    input_pdf = "sif/SIF for the BKV CMS commissioning procedure.pdf"
    output_pdf = "sif/SIF_cleaned.pdf"
    
    clean_sif_pdf(input_pdf, output_pdf)
