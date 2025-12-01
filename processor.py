"""
Python File Processor
This module runs in the browser using PyScript/Pyodide.
It processes uploaded text files and returns the result.
"""

from pyscript import window
import json


def process_file(content: str, filename: str) -> str:
    """
    Process the uploaded file content.
    
    Args:
        content: The text content of the uploaded file
        filename: The name of the uploaded file
        
    Returns:
        Processed content as a string
    """
    # Get file extension
    ext = filename.lower().split('.')[-1] if '.' in filename else ''
    
    # Statistics
    lines = content.split('\n')
    line_count = len(lines)
    word_count = len(content.split())
    char_count = len(content)
    
    result = []
    result.append("=" * 50)
    result.append("📊 FILE ANALYSIS REPORT")
    result.append("=" * 50)
    result.append(f"\n📁 Filename: {filename}")
    result.append(f"📏 Lines: {line_count}")
    result.append(f"📝 Words: {word_count}")
    result.append(f"🔤 Characters: {char_count}")
    
    # File-type specific processing
    if ext == 'json':
        result.append("\n" + "-" * 50)
        result.append("🔍 JSON ANALYSIS")
        result.append("-" * 50)
        try:
            data = json.loads(content)
            if isinstance(data, dict):
                result.append(f"Type: Object with {len(data)} keys")
                result.append(f"Keys: {', '.join(list(data.keys())[:10])}")
                if len(data.keys()) > 10:
                    result.append(f"... and {len(data.keys()) - 10} more keys")
            elif isinstance(data, list):
                result.append(f"Type: Array with {len(data)} items")
            result.append("✅ Valid JSON structure")
        except json.JSONDecodeError as e:
            result.append(f"❌ Invalid JSON: {str(e)}")
    
    elif ext == 'csv':
        result.append("\n" + "-" * 50)
        result.append("📊 CSV ANALYSIS")
        result.append("-" * 50)
        if lines:
            # Try to detect delimiter
            first_line = lines[0]
            if ',' in first_line:
                delimiter = ','
            elif '\t' in first_line:
                delimiter = '\t'
            elif ';' in first_line:
                delimiter = ';'
            else:
                delimiter = ','
            
            columns = first_line.split(delimiter)
            result.append(f"Columns: {len(columns)}")
            result.append(f"Data rows: {line_count - 1}")
            result.append(f"Column headers: {', '.join(columns[:5])}")
            if len(columns) > 5:
                result.append(f"... and {len(columns) - 5} more columns")
    
    elif ext == 'py':
        result.append("\n" + "-" * 50)
        result.append("🐍 PYTHON CODE ANALYSIS")
        result.append("-" * 50)
        
        import_count = sum(1 for line in lines if line.strip().startswith('import ') or line.strip().startswith('from '))
        def_count = sum(1 for line in lines if line.strip().startswith('def '))
        class_count = sum(1 for line in lines if line.strip().startswith('class '))
        comment_count = sum(1 for line in lines if line.strip().startswith('#'))
        
        result.append(f"Imports: {import_count}")
        result.append(f"Functions: {def_count}")
        result.append(f"Classes: {class_count}")
        result.append(f"Comments: {comment_count}")
    
    # Word frequency analysis
    result.append("\n" + "-" * 50)
    result.append("📈 TOP 10 MOST COMMON WORDS")
    result.append("-" * 50)
    
    # Simple word frequency
    words = content.lower().split()
    # Remove punctuation from words
    cleaned_words = []
    for word in words:
        cleaned = ''.join(c for c in word if c.isalnum())
        if cleaned and len(cleaned) > 2:
            cleaned_words.append(cleaned)
    
    word_freq = {}
    for word in cleaned_words:
        word_freq[word] = word_freq.get(word, 0) + 1
    
    # Sort by frequency
    sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:10]
    for i, (word, freq) in enumerate(sorted_words, 1):
        result.append(f"{i}. '{word}': {freq} times")
    
    # Add transformed content preview
    result.append("\n" + "-" * 50)
    result.append("📄 CONTENT PREVIEW (first 500 chars)")
    result.append("-" * 50)
    result.append(content[:500])
    if len(content) > 500:
        result.append("\n... [truncated]")
    
    result.append("\n" + "=" * 50)
    result.append("✅ Processing complete!")
    result.append("=" * 50)
    
    return '\n'.join(result)


# Expose the function to JavaScript
window.processFile = process_file
