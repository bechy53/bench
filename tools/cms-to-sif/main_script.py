print("=" * 50)
print("PyScript initializing...")
print("=" * 50)

from pyodide.ffi import create_proxy
from js import document, window, Blob, URL
import main

print("Imports successful")

# Global state
cms_bytes = None
sif_bytes = None
extracted_cms_data = None
user_sif_bytes = None  # For user-uploaded SIF template

print("Global state initialized")

# Load SIF template on startup
async def load_sif_template():
    global sif_bytes
    try:
        # Add timestamp to bypass browser cache
        import time
        timestamp = int(time.time())
        response = await window.fetch(f'sif/SIF for the BKV CMS commissioning procedure.pdf?t={timestamp}')
        if response.ok:
            array_buffer = await response.arrayBuffer()
            sif_bytes = array_buffer.to_py().tobytes()
            print('SIF template loaded successfully')
            # Display SIF fields after loading
            await display_sif_fields()
        else:
            print('Error loading SIF template')
    except Exception as e:
        print(f'Error loading SIF template: {e}')

# Display all SIF fields
async def display_sif_fields():
    """Display all available SIF fields on the page"""
    try:
        current_sif = user_sif_bytes if user_sif_bytes is not None else sif_bytes
        if current_sif is None:
            return
        
        from pypdf import PdfReader
        from models import CMS_TO_SIF_MAP
        import io
        
        # Extract field names directly
        reader = PdfReader(io.BytesIO(current_sif))
        fields = reader.get_fields()
        
        if not fields:
            print('No fields found in SIF template')
            return
        
        # Debug: print first few field names
        field_list = list(fields.keys())
        print(f'Total fields found: {len(field_list)}')
        print(f'First 5 fields: {field_list[:5]}')
        print('\nAll field names:')
        for i, fname in enumerate(sorted(field_list), 1):
            print(f'{i}. {fname}')
        
        # Use unique field names only
        field_names = sorted(set(fields.keys()))
        mapped_fields = set(CMS_TO_SIF_MAP.values())
        
        grid = document.getElementById('sif-fields-grid')
        grid.innerHTML = ''
        
        for field_name in field_names:
            field_div = document.createElement('div')
            field_div.className = 'sif-field-item'
            
            # Create field name label
            name_span = document.createElement('span')
            name_span.className = 'sif-field-name'
            
            # Mark if this field is mapped from CMS
            if field_name in mapped_fields:
                field_div.className += ' mapped'
                name_span.innerText = f'✓ {field_name}'
            else:
                name_span.innerText = field_name
            
            # Create input field
            input_field = document.createElement('input')
            input_field.type = 'text'
            input_field.className = 'sif-field-input'
            input_field.placeholder = 'Empty'
            input_field.id = f'sif-field-{field_name.replace(" ", "_").replace("/", "_")}'
            
            field_div.appendChild(name_span)
            field_div.appendChild(input_field)
            grid.appendChild(field_div)
        
        print(f'Displayed {len(field_names)} unique SIF fields')
        
    except Exception as e:
        print(f'Error displaying SIF fields: {e}')
        import traceback
        traceback.print_exc()

# File upload handlers
def handle_cms_upload(event):
    global cms_bytes
    print("File upload event triggered")
    files = event.target.files
    if files.length > 0:
        file = files.item(0)
        print(f"File selected: {file}")
        print(f"File name: {file.name}")
        document.getElementById('cms-file-name').innerText = file.name
        document.getElementById('cms-upload').classList.add('active')
        
        # Read file bytes
        reader = window.FileReader.new()
        
        def on_load(e):
            global cms_bytes
            print("File reader onload triggered")
            array_buffer = e.target.result
            cms_bytes = array_buffer.to_py().tobytes()
            print(f"CMS bytes loaded: {len(cms_bytes)} bytes")
            check_ready_to_extract()
        
        reader.onload = create_proxy(on_load)
        reader.readAsArrayBuffer(file)
        print("Started reading file as ArrayBuffer")

def handle_sif_upload(event):
    global user_sif_bytes
    print("SIF file upload event triggered")
    files = event.target.files
    if files.length > 0:
        file = files.item(0)
        print(f"SIF File selected: {file}")
        print(f"SIF File name: {file.name}")
        document.getElementById('sif-file-name').innerText = file.name
        document.getElementById('sif-upload').classList.add('active')
        
        # Read file bytes
        reader = window.FileReader.new()
        
        def on_load(e):
            global user_sif_bytes
            print("SIF file reader onload triggered")
            array_buffer = e.target.result
            user_sif_bytes = array_buffer.to_py().tobytes()
            print(f"User SIF bytes loaded: {len(user_sif_bytes)} bytes")
            # Update SIF fields display
            import asyncio
            asyncio.ensure_future(display_sif_fields())
            check_ready_to_generate()
        
        reader.onload = create_proxy(on_load)
        reader.readAsArrayBuffer(file)
        print("Started reading SIF file as ArrayBuffer")

def check_ready_to_extract():
    print(f"check_ready_to_extract called. cms_bytes is None: {cms_bytes is None}")
    if cms_bytes is not None:
        document.getElementById('extract-btn').disabled = False
        print("Extract button enabled")

def check_ready_to_generate():
    print(f"check_ready_to_generate called. extracted_cms_data is None: {extracted_cms_data is None}, sif_bytes is None: {sif_bytes is None}, user_sif_bytes is None: {user_sif_bytes is None}")
    # Enable generate button if we have CMS data and either default or user SIF
    if extracted_cms_data is not None and (sif_bytes is not None or user_sif_bytes is not None):
        document.getElementById('generate-btn').disabled = False
        print("Generate button enabled")

def populate_sif_fields(cms_data):
    """Populate SIF field input boxes with CMS data based on the mapping"""
    from models import CMS_TO_SIF_MAP
    
    cms_dict = cms_data.to_dict()
    
    # Map CMS data to SIF fields
    for cms_field, sif_field in CMS_TO_SIF_MAP.items():
        value = cms_dict.get(cms_field)
        if value:
            # Find the input field by creating the same ID we used when creating it
            field_id = f'sif-field-{sif_field.replace(" ", "_").replace("/", "_")}'
            input_element = document.getElementById(field_id)
            if input_element:
                input_element.value = str(value)
                print(f"Populated {sif_field} = {value}")
            else:
                print(f"Warning: Could not find input field for {sif_field}")

# Extract CMS data
async def extract_cms(event):
    global extracted_cms_data
    
    print("Extract CMS button clicked")
    print(f"cms_bytes length: {len(cms_bytes) if cms_bytes else 'None'}")
    
    show_loading(True)
    show_status("Performing OCR on CMS report... This may take a minute.", "info")
    
    try:
        print("Starting OCR on CMS report...")
        # Use JavaScript OCR function
        from js import performOCR
        ocr_text = await performOCR(cms_bytes)
        print(f"OCR complete. Extracted {len(ocr_text)} characters")
        
        print("Parsing OCR text...")
        # Parse the OCR'd text
        from cms_parser import parse_cms_report
        extracted_cms_data = parse_cms_report(ocr_text, debug=True)
        
        # Add current date if not present
        if not extracted_cms_data.service_date:
            from datetime import datetime
            extracted_cms_data.service_date = datetime.now().strftime('%m/%d/%Y')
            print(f"Added current date: {extracted_cms_data.service_date}")
        
        print(f"Extraction complete. Data: {extracted_cms_data}")
        
        # Populate SIF field inputs with mapped CMS data
        populate_sif_fields(extracted_cms_data)
        
        # Display extracted data
        display_extracted_data(extracted_cms_data)
        
        show_status(f"Successfully extracted {len(extracted_cms_data.to_dict())} fields from CMS report", "success")
        check_ready_to_generate()
        
    except Exception as e:
        show_status(f"Error extracting CMS data: {str(e)}", "error")
        print(f"Error during extraction: {e}")
        import traceback
        traceback.print_exc()
    finally:
        show_loading(False)

# Generate filled SIF
def generate_sif(event):
    print("Generate SIF button clicked")
    
    # Use user-uploaded SIF if available, otherwise use default
    current_sif = user_sif_bytes if user_sif_bytes is not None else sif_bytes
    print(f"current_sif length: {len(current_sif) if current_sif else 'None'}")
    
    show_loading(True)
    hide_status()
    
    try:
        print("Starting SIF generation...")
        
        # Collect values from all SIF field inputs
        from pypdf import PdfReader
        import io
        
        reader = PdfReader(io.BytesIO(current_sif))
        fields = reader.get_fields()
        
        if not fields:
            raise Exception("No fields found in SIF template")
        
        # Build field values dictionary from input fields
        field_values = {}
        for field_name in fields.keys():
            field_id = f'sif-field-{field_name.replace(" ", "_").replace("/", "_")}'
            input_element = document.getElementById(field_id)
            if input_element and input_element.value:
                field_values[field_name] = input_element.value
                print(f"Using field value: {field_name} = {input_element.value}")
        
        print(f"Filling {len(field_values)} fields")
        
        # Fill the SIF using the collected values
        from sif_filler import fill_sif_form
        filled_pdf = fill_sif_form(current_sif, field_values, flatten=False)
        print(f"SIF generation complete. PDF size: {len(filled_pdf)} bytes")
        
        # Download filled PDF
        download_pdf(filled_pdf, "filled_SIF.pdf")
        
        show_status(f"Successfully generated SIF! Filled {len(field_values)} fields.", "success")
        
    except Exception as e:
        show_status(f"Error generating SIF: {str(e)}", "error")
        print(f"Error during SIF generation: {e}")
        import traceback
        traceback.print_exc()
    finally:
        show_loading(False)

# Clear all
def clear_all(event):
    global cms_bytes, extracted_cms_data, user_sif_bytes
    
    cms_bytes = None
    extracted_cms_data = None
    user_sif_bytes = None
    
    document.getElementById('cms-file').value = ""
    document.getElementById('cms-file-name').innerText = ""
    document.getElementById('cms-upload').classList.remove('active')
    document.getElementById('sif-file').value = ""
    document.getElementById('sif-file-name').innerText = ""
    document.getElementById('sif-upload').classList.remove('active')
    document.getElementById('extract-btn').disabled = True
    document.getElementById('generate-btn').disabled = True
    document.getElementById('extracted-data').style.display = 'none'
    document.getElementById('report').style.display = 'none'
    hide_status()
    # Reload SIF template and refresh field display
    import asyncio
    asyncio.ensure_future(load_sif_template())

# UI helpers
def show_loading(show):
    if show:
        document.getElementById('loading').classList.add('visible')
    else:
        document.getElementById('loading').classList.remove('visible')

def show_status(message, status_type):
    status_el = document.getElementById('status')
    status_el.innerText = message
    status_el.className = f'status-section status-{status_type} visible'

def hide_status():
    document.getElementById('status').className = 'status-section'

def display_extracted_data(cms_data):
    print(f"display_extracted_data called with data: {type(cms_data)}")
    
    grid = document.getElementById('data-grid')
    grid.innerHTML = ''
    
    # Display basic fields (excluding raw_text)
    basic_fields = {k: v for k, v in cms_data.to_dict().items() 
                    if k != 'raw_text'}
    
    for field, value in basic_fields.items():
        field_div = document.createElement('div')
        field_div.className = 'data-field'
        
        label = document.createElement('label')
        label.innerText = field.replace('_', ' ')
        
        value_div = document.createElement('div')
        value_div.className = 'value' if value else 'value empty'
        value_div.innerText = value if value else '(not found)'
        
        field_div.appendChild(label)
        field_div.appendChild(value_div)
        grid.appendChild(field_div)
    
    document.getElementById('extracted-data').style.display = 'block'

def display_report(report):
    report_el = document.getElementById('report')
    
    html = f"""
    <h4>Mapping Report</h4>
    <ul>
        <li>CMS fields extracted: {report['cms_extraction']['total_fields']}</li>
        <li>SIF fields available: {report['sif_form']['total_fields']}</li>
        <li>Successfully mapped: {report['mapping']['successfully_mapped']}</li>
        <li>CMS coverage: {report['coverage']['cms_coverage']}</li>
        <li>SIF coverage: {report['coverage']['sif_coverage']}</li>
    </ul>
    """
    
    report_el.innerHTML = html
    report_el.style.display = 'block'

def download_pdf(pdf_bytes, filename):
    # Create blob and download
    blob = Blob.new([pdf_bytes], {'type': 'application/pdf'})
    url = URL.createObjectURL(blob)
    
    a = document.createElement('a')
    a.href = url
    a.download = filename
    a.click()
    
    URL.revokeObjectURL(url)

# Attach event listeners
document.getElementById('cms-file').addEventListener('change', create_proxy(handle_cms_upload))
document.getElementById('sif-file').addEventListener('change', create_proxy(handle_sif_upload))
document.getElementById('extract-btn').addEventListener('click', create_proxy(extract_cms))
document.getElementById('generate-btn').addEventListener('click', create_proxy(generate_sif))
document.getElementById('clear-btn').addEventListener('click', create_proxy(clear_all))

print("Event listeners attached")
print("Starting SIF template load...")

# Load SIF template on startup
import asyncio
asyncio.ensure_future(load_sif_template())

print("=" * 50)
print("CMS to SIF Converter loaded successfully!")
print("=" * 50)
