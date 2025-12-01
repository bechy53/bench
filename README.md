# bench
A website repo that stores all the in browser tools I've developed so far

## Python File Processor

A browser-based tool that lets you upload and process text files using Python running directly in your browser!

### Features

- **File Upload**: Drag & drop or click to upload text files (.txt, .csv, .json, .py, etc.)
- **Python Processing**: Files are processed using Python via [PyScript](https://pyscript.net/) (Pyodide - Python compiled to WebAssembly)
- **File Analysis**: Provides statistics like line count, word count, character count
- **Format-specific Analysis**: Special handling for JSON, CSV, and Python files
- **Word Frequency**: Shows the top 10 most common words
- **Download Results**: Export the processed output as a text file

### How It Works

This website uses **PyScript/Pyodide** to run Python code directly in the browser. No server-side processing is needed - everything runs client-side using WebAssembly.

### Deployment

This site is designed for deployment on GitHub Pages:

1. Enable GitHub Pages in your repository settings
2. Set the source to the main branch
3. Your site will be available at `https://<username>.github.io/bench/`

### Local Development

To run locally:

```bash
python3 -m http.server 8080
```

Then open `http://localhost:8080` in your browser.

### Technology

- **PyScript/Pyodide**: Python compiled to WebAssembly for browser execution
- **HTML/CSS/JavaScript**: Frontend interface
- **GitHub Pages**: Static site hosting
