// PDF.js setup
pdfjsLib.GlobalWorkerOptions.workerSrc = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js';

let controlPdf = null;
let reviewPdfs = [];
let comparisonResults = null;

// Control PDF upload handling
const controlUpload = document.getElementById('control-upload');
const controlInput = document.getElementById('control-input');
const controlInfo = document.getElementById('control-info');
const controlName = document.getElementById('control-name');

controlUpload.addEventListener('click', () => controlInput.click());

controlUpload.addEventListener('dragover', (e) => {
    e.preventDefault();
    controlUpload.classList.add('dragover');
});

controlUpload.addEventListener('dragleave', () => {
    controlUpload.classList.remove('dragover');
});

controlUpload.addEventListener('drop', (e) => {
    e.preventDefault();
    controlUpload.classList.remove('dragover');
    const files = e.dataTransfer.files;
    if (files.length > 0 && files[0].type === 'application/pdf') {
        handleControlFile(files[0]);
    }
});

controlInput.addEventListener('change', (e) => {
    if (e.target.files.length > 0) {
        handleControlFile(e.target.files[0]);
    }
});

function handleControlFile(file) {
    controlPdf = file;
    controlName.textContent = file.name;
    controlInfo.classList.add('visible');
    checkReadyToCompare();
}

// Review PDFs upload handling
const reviewUpload = document.getElementById('review-upload');
const reviewInput = document.getElementById('review-input');
const reviewInfo = document.getElementById('review-info');
const reviewCount = document.getElementById('review-count');
const reviewList = document.getElementById('review-list');

reviewUpload.addEventListener('click', () => reviewInput.click());

reviewUpload.addEventListener('dragover', (e) => {
    e.preventDefault();
    reviewUpload.classList.add('dragover');
});

reviewUpload.addEventListener('dragleave', () => {
    reviewUpload.classList.remove('dragover');
});

reviewUpload.addEventListener('drop', (e) => {
    e.preventDefault();
    reviewUpload.classList.remove('dragover');
    const files = Array.from(e.dataTransfer.files).filter(f => f.type === 'application/pdf');
    if (files.length > 0) {
        handleReviewFiles(files);
    }
});

reviewInput.addEventListener('change', (e) => {
    const files = Array.from(e.target.files);
    if (files.length > 0) {
        handleReviewFiles(files);
    }
});

function handleReviewFiles(files) {
    reviewPdfs = files;
    reviewCount.textContent = files.length;
    reviewInfo.classList.add('visible');
    
    reviewList.innerHTML = '<ul style="margin: 5px 0; padding-left: 20px;">' +
        files.map(f => `<li>${f.name}</li>`).join('') +
        '</ul>';
    
    checkReadyToCompare();
}

function checkReadyToCompare() {
    const compareBtn = document.getElementById('compare-btn');
    compareBtn.disabled = !(controlPdf && reviewPdfs.length > 0);
}

// Extract form fields from PDF using PDF.js
async function extractFormFields(file) {
    const arrayBuffer = await file.arrayBuffer();
    const pdf = await pdfjsLib.getDocument({ data: arrayBuffer }).promise;
    const fields = [];
    
    for (let pageNum = 1; pageNum <= pdf.numPages; pageNum++) {
        const page = await pdf.getPage(pageNum);
        const annotations = await page.getAnnotations();
        
        for (const annot of annotations) {
            if (annot.fieldType) {
                fields.push({
                    page: pageNum,
                    name: annot.fieldName || '',
                    value: annot.fieldValue || '',
                    type: annot.fieldType
                });
            }
        }
    }
    
    return fields;
}

function getStatus(value) {
    if (!value || !value.toString().trim()) {
        return 'BLANK';
    }
    return value.toString().trim().toUpperCase() === 'N/A' ? 'N/A' : 'FILLED';
}

function compareFields(controlFields, reviewFields) {
    const controlDict = {};
    controlFields.forEach(f => {
        controlDict[f.name] = f;
    });
    
    const reviewDict = {};
    reviewFields.forEach(f => {
        reviewDict[f.name] = f;
    });
    
    const allFieldNames = [...new Set([...Object.keys(controlDict), ...Object.keys(reviewDict)])].sort();
    const matches = [];
    const mismatches = [];
    
    for (const name of allFieldNames) {
        const cField = controlDict[name] || { value: '', page: '' };
        const rField = reviewDict[name] || { value: '', page: '' };
        const cStatus = getStatus(cField.value);
        const rStatus = getStatus(rField.value);
        
        const fieldData = {
            name: name,
            cValue: cField.value,
            rValue: rField.value,
            cPage: cField.page,
            rPage: rField.page,
            cStatus: cStatus,
            rStatus: rStatus,
            match: cStatus === rStatus
        };
        
        if (fieldData.match) {
            matches.push(fieldData);
        } else {
            mismatches.push(fieldData);
        }
    }
    
    return { matches, mismatches };
}

function displayResults(results) {
    const resultsDiv = document.getElementById('results');
    resultsDiv.innerHTML = '';
    
    // Master summary
    let html = '<div class="summary-card"><h2>📊 Master Summary</h2>';
    html += '<table><thead><tr><th>Review PDF</th><th>Total Fields</th><th>Matches</th><th>Mismatches</th><th>Match %</th></tr></thead><tbody>';
    
    results.forEach(result => {
        const total = result.matches.length + result.mismatches.length;
        const matchPct = total > 0 ? (result.matches.length / total * 100).toFixed(1) : 0;
        html += `<tr>
            <td>${result.pdfName}</td>
            <td style="text-align: center;">${total}</td>
            <td style="text-align: center;" class="match">${result.matches.length}</td>
            <td style="text-align: center;" class="mismatch">${result.mismatches.length}</td>
            <td style="text-align: center;">${matchPct}%</td>
        </tr>`;
    });
    
    html += '</tbody></table></div>';
    
    // Individual PDF results
    results.forEach(result => {
        const isPerfect = result.mismatches.length === 0;
        html += `<div class="summary-card ${isPerfect ? 'success' : 'error'}">`;
        html += `<h3>${result.pdfName}</h3>`;
        
        if (isPerfect) {
            html += '<p style="font-size: 1.3em; margin: 20px 0;"><strong>✓ 100% MATCH</strong></p>';
        } else {
            html += `<p><strong>❌ ${result.mismatches.length} Mismatch(es) Found</strong></p>`;
            html += '<table><thead><tr><th>Ctrl Pg</th><th>Rev Pg</th><th>Field Name</th><th>Control (Status)</th><th>Review (Status)</th></tr></thead><tbody>';
            
            result.mismatches.forEach(field => {
                html += `<tr>
                    <td style="text-align: center;">${field.cPage}</td>
                    <td style="text-align: center;">${field.rPage}</td>
                    <td>${field.name}</td>
                    <td><span class="status-badge status-${field.cStatus.toLowerCase()}">${field.cStatus}</span><br><small>${field.cValue || '(empty)'}</small></td>
                    <td><span class="status-badge status-${field.rStatus.toLowerCase()}">${field.rStatus}</span><br><small>${field.rValue || '(empty)'}</small></td>
                </tr>`;
            });
            
            html += '</tbody></table>';
        }
        
        html += '</div>';
    });
    
    resultsDiv.innerHTML = html;
    resultsDiv.classList.add('visible');
    document.getElementById('download-btn').disabled = false;
}

// Compare button handler
document.getElementById('compare-btn').addEventListener('click', async () => {
    const loading = document.getElementById('loading');
    const compareBtn = document.getElementById('compare-btn');
    
    loading.classList.add('visible');
    compareBtn.disabled = true;
    
    try {
        // Extract control PDF fields
        const controlFields = await extractFormFields(controlPdf);
        
        // Process each review PDF
        const results = [];
        for (const reviewPdf of reviewPdfs) {
            const reviewFields = await extractFormFields(reviewPdf);
            const comparison = compareFields(controlFields, reviewFields);
            
            results.push({
                pdfName: reviewPdf.name,
                matches: comparison.matches,
                mismatches: comparison.mismatches
            });
        }
        
        comparisonResults = {
            controlName: controlPdf.name,
            results: results
        };
        
        displayResults(results);
        
    } catch (error) {
        alert('Error processing PDFs: ' + error.message);
        console.error(error);
    } finally {
        loading.classList.remove('visible');
        compareBtn.disabled = false;
    }
});

// Download button - trigger Python export
document.getElementById('download-btn').addEventListener('click', async () => {
    if (comparisonResults && window.generateExcelReport) {
        try {
            await window.generateExcelReport(comparisonResults);
        } catch (error) {
            alert('Error generating Excel report: ' + error.message);
            console.error(error);
        }
    }
});
