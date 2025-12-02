# CMS to SIF Converter

A web-based tool for automatically extracting data from CMS (Commissioning/Maintenance Service) reports and filling Service Inspection Form (SIF) PDFs. Built with Python running entirely in the browser using PyScript.

## 🎯 Overview

This tool streamlines the process of transferring information from CMS reports into SIF forms by:

1. **Extracting** structured data from CMS report PDFs using text extraction and pattern matching
2. **Mapping** extracted data to corresponding SIF form fields
3. **Generating** a completed SIF PDF ready for submission or archival

All processing happens client-side in the browser - no server uploads required, ensuring data privacy.

## 🏗️ Architecture

### Component Overview

```
cms-to-sif/
├── models.py          # Data models and field mappings
├── pdf_loader.py      # PDF reading and text extraction
├── cms_parser.py      # CMS report parsing logic
├── sif_filler.py      # SIF form filling logic
├── main.py            # Main workflow orchestration
├── cms-to-sif.html    # Web interface with PyScript
└── README.md          # This file
```

### Data Flow

```
┌─────────────────┐
│  CMS Report PDF │
└────────┬────────┘
         │
         ▼
  ┌──────────────┐
  │ pdf_loader   │ ─── Extract text
  └──────┬───────┘
         │
         ▼
  ┌──────────────┐
  │ cms_parser   │ ─── Parse structured data
  └──────┬───────┘
         │
         ▼
  ┌──────────────┐
  │ models       │ ─── CmsReportData object
  └──────┬───────┘
         │
         ▼
  ┌──────────────┐
  │ sif_filler   │ ─── Map to SIF fields
  └──────┬───────┘
         │
         ▼
┌─────────────────┐
│ Filled SIF PDF  │
└─────────────────┘
```

## 📦 Core Modules

### models.py

Defines the data structures:

- **CmsReportData**: Structured representation of CMS report content
- **SifData**: Structure matching SIF PDF form fields
- **CMS_TO_SIF_MAP**: Configuration mapping CMS fields to SIF field names

### pdf_loader.py

Handles PDF operations:

- `extract_pdf_text()`: Extract text content from PDFs
- `get_form_fields()`: Inspect PDF AcroForm fields
- `clone_pdf_for_writing()`: Prepare PDF for modification
- OCR support (placeholder for future implementation)

### cms_parser.py

Extracts structured data from CMS text:

- `parse_cms_report()`: Main parsing function using regex patterns
- `validate_cms_data()`: Check for required fields
- `get_extraction_summary()`: Statistics on extraction success
- Pattern matching for common CMS report formats

### sif_filler.py

Fills SIF PDF forms:

- `cms_to_sif_field_values()`: Convert CMS data to SIF field values
- `fill_sif_form()`: Apply values to PDF AcroForm fields
- `get_mapping_report()`: Detailed mapping statistics
- `create_filled_sif()`: Complete filling workflow

### main.py

Orchestrates the workflow:

- `convert_cms_to_sif()`: Complete end-to-end conversion
- `process_cms_report()`: Extract and parse CMS data
- `create_sif_from_cms()`: Generate filled SIF
- Convenience functions for web interface

## 🚀 Usage

### Web Interface

1. Open `cms-to-sif.html` in a modern web browser
2. Upload your CMS report PDF
3. Upload your SIF template PDF
4. Click "Extract CMS Data" to parse the report
5. Review extracted data
6. Click "Generate Filled SIF" to create the completed form
7. Download the filled SIF PDF

### Python API (for desktop use)

```python
from main import convert_cms_to_sif

# Load PDFs
with open('cms_report.pdf', 'rb') as f:
    cms_bytes = f.read()

with open('sif_template.pdf', 'rb') as f:
    sif_bytes = f.read()

# Convert
filled_sif, report = convert_cms_to_sif(
    cms_bytes, 
    sif_bytes, 
    debug=True
)

# Save result
with open('filled_sif.pdf', 'wb') as f:
    f.write(filled_sif)

# Check mapping report
print(f"Mapped {report['mapping']['successfully_mapped']} fields")
print(f"Coverage: {report['coverage']['sif_coverage']}")
```

## 🔧 Configuration

### Customizing Field Mappings

Edit `models.py` to customize how CMS fields map to SIF fields:

```python
CMS_TO_SIF_MAP = {
    "cms_field_name": "SIF Form Field Name",
    "wind_farm": "Wind farm number",
    "turbine_number": "Wind turbine number",
    # Add more mappings as needed
}
```

### Refining CMS Parsing

Update regex patterns in `cms_parser.py` to match your CMS report format:

```python
# Example: Extract turbine number
turbine_number = find(r"(?:Turbine\s*Number|WTG)[:\s#]*([A-Z0-9\-]+)")
```

Use `refine_patterns_for_format()` to analyze sample reports and identify patterns.

## 📋 Requirements

### Browser Environment
- Modern web browser with JavaScript enabled
- PyScript (loaded via CDN in HTML)
- Internet connection for initial load (PyScript and pypdf)

### Desktop Python Environment (optional)
```bash
pip install pypdf
```

## 🔍 How It Works

### 1. Text Extraction

The `pdf_loader` module uses `pypdf` to extract text from the CMS report. It detects if OCR is needed (when very little text is extracted).

### 2. Pattern Matching

The `cms_parser` module uses regex patterns to find and extract specific information:
- Wind farm details
- Turbine information
- Personnel names
- Dates
- Technical specifications

### 3. Data Validation

After extraction, the system validates that critical fields were found and provides warnings for missing data.

### 4. Field Mapping

The `sif_filler` module maps extracted CMS data to SIF form fields using the configuration in `models.py`.

### 5. Form Filling

PDF AcroForm fields in the SIF template are populated with the mapped values using `pypdf`'s form field update capabilities.

### 6. Report Generation

A detailed mapping report shows:
- How many fields were extracted
- How many SIF fields were filled
- Coverage percentages
- Any unmapped or missing fields

## 🎨 Customization

### Adding New Fields

1. Add field to `CmsReportData` in `models.py`
2. Add extraction pattern in `cms_parser.py`
3. Add mapping entry in `CMS_TO_SIF_MAP`
4. Verify SIF PDF field name matches mapping

### Changing UI

Modify `cms-to-sif.html`:
- Styling is in `<style>` section
- UI logic is in `<py-script>` section
- Add custom validation or workflow steps as needed

### Adding OCR Support

To enable OCR for image-based PDFs:

1. Integrate Tesseract.js in `cms-to-sif.html`
2. Implement `extract_text_with_ocr()` in `pdf_loader.py`
3. Add JavaScript interop for PDF page rendering
4. Process each page image through Tesseract

## 📊 Debugging

Enable debug mode to see detailed processing information:

```python
# In Python
filled_sif, report = convert_cms_to_sif(cms_bytes, sif_bytes, debug=True)

# In browser console
# PyScript will print debug output to browser console
```

Debug output includes:
- Extracted text preview
- Parsing results for each field
- Mapping statistics
- Field coverage percentages

## ⚠️ Limitations

- **Text-based PDFs only**: OCR for image-based PDFs requires additional setup
- **Pattern matching**: Parsing depends on consistent CMS report formatting
- **Browser compatibility**: Requires modern browser with WASM support
- **Field names**: SIF template must have AcroForm fields with expected names

## 🛠️ Development

### Testing Parsing Patterns

Use the pattern refinement helper:

```python
from cms_parser import refine_patterns_for_format

with open('sample_cms.pdf', 'rb') as f:
    from pdf_loader import extract_pdf_text
    text, _ = extract_pdf_text(f.read())

suggestions = refine_patterns_for_format(text)
print(suggestions)
```

### Inspecting SIF Fields

Check what fields are in your SIF template:

```python
from pdf_loader import get_form_fields

with open('sif_template.pdf', 'rb') as f:
    fields = get_form_fields(f.read())

for name, info in fields.items():
    print(f"{name}: {info}")
```

## 📝 Future Enhancements

- [ ] OCR support for image-based PDFs
- [ ] Template management (save/load field mappings)
- [ ] Batch processing multiple CMS reports
- [ ] Export mapping reports as CSV/JSON
- [ ] Machine learning for adaptive pattern matching
- [ ] Support for additional report formats
- [ ] Field validation rules
- [ ] Undo/redo for manual edits

## 📄 License

[Add your license information here]

## 🤝 Contributing

To contribute:

1. Test with your specific CMS report format
2. Refine regex patterns in `cms_parser.py`
3. Update field mappings in `models.py`
4. Submit improvements or bug reports

## 📞 Support

For issues or questions:
- Check browser console for PyScript errors
- Enable debug mode to see detailed processing logs
- Verify SIF template has AcroForm fields
- Ensure CMS report is text-based (not scanned image)
