let uploadedFiles = [];

const REQUIRED_STRUCTURE = {
    "JOB BOOK": {
        "photos": [
            "Before Photo.jpg",
            "After Photo.jpg"
        ],
        "documents": [
            "CMS 1500.pdf",
            "Risk Assessment.pdf",
            "Scope of Works.pdf",
            "Floor Plan.pdf",
            "EOB.pdf",
            "Invoice.pdf",
            "SIF.pdf"
        ]
    }
};

const uploadArea = document.getElementById('uploadArea');
const folderInput = document.getElementById('folderInput');
const checkBtn = document.getElementById('checkBtn');
const resultsDiv = document.getElementById('results');

// Click to upload
uploadArea.addEventListener('click', () => {
    folderInput.click();
});

// Drag and drop
uploadArea.addEventListener('dragover', (e) => {
    e.preventDefault();
    uploadArea.classList.add('dragover');
});

uploadArea.addEventListener('dragleave', () => {
    uploadArea.classList.remove('dragover');
});

uploadArea.addEventListener('drop', (e) => {
    e.preventDefault();
    uploadArea.classList.remove('dragover');
    
    const items = e.dataTransfer.items;
    if (items) {
        handleDroppedItems(items);
    }
});

// File input change
folderInput.addEventListener('change', (e) => {
    uploadedFiles = Array.from(e.target.files);
    if (uploadedFiles.length > 0) {
        uploadArea.innerHTML = `<p>✓ Folder selected: ${uploadedFiles.length} files</p>`;
        checkBtn.disabled = false;
    }
});

async function handleDroppedItems(items) {
    uploadedFiles = [];
    
    for (let i = 0; i < items.length; i++) {
        const item = items[i].webkitGetAsEntry();
        if (item) {
            await traverseFileTree(item);
        }
    }
    
    if (uploadedFiles.length > 0) {
        uploadArea.innerHTML = `<p>✓ Folder selected: ${uploadedFiles.length} files</p>`;
        checkBtn.disabled = false;
    }
}

function traverseFileTree(item, path = '') {
    return new Promise((resolve) => {
        if (item.isFile) {
            item.file((file) => {
                uploadedFiles.push({
                    name: file.name,
                    path: path + file.name,
                    file: file
                });
                resolve();
            });
        } else if (item.isDirectory) {
            const dirReader = item.createReader();
            dirReader.readEntries(async (entries) => {
                for (const entry of entries) {
                    await traverseFileTree(entry, path + item.name + '/');
                }
                resolve();
            });
        }
    });
}

checkBtn.addEventListener('click', () => {
    checkFiles();
});

function checkFiles() {
    resultsDiv.innerHTML = '';
    
    const fileMap = new Map();
    uploadedFiles.forEach(file => {
        fileMap.set(file.path.toLowerCase(), file);
    });
    
    let totalRequired = 0;
    let totalFound = 0;
    let missingFiles = [];
    
    // Check folders and files
    for (const [folderName, contents] of Object.entries(REQUIRED_STRUCTURE)) {
        for (const [subFolder, files] of Object.entries(contents)) {
            totalRequired += files.length;
            
            files.forEach(fileName => {
                const expectedPath = `${folderName}/${subFolder}/${fileName}`.toLowerCase();
                
                // Check for exact match or any file in uploaded files
                const found = Array.from(fileMap.keys()).some(path => 
                    path.endsWith(`/${subFolder}/${fileName}`.toLowerCase()) ||
                    path.endsWith(`\\${subFolder}\\${fileName}`.toLowerCase())
                );
                
                if (found) {
                    totalFound++;
                } else {
                    missingFiles.push({
                        folder: subFolder,
                        file: fileName
                    });
                }
            });
        }
    }
    
    // Display results
    const summaryClass = missingFiles.length === 0 ? 'success' : 'warning';
    
    let html = `
        <div class="result-section ${summaryClass}">
            <div class="summary">
                ${totalFound} of ${totalRequired} required files found
            </div>
    `;
    
    if (missingFiles.length === 0) {
        html += `<p>✓ All required files are present!</p>`;
    } else {
        html += `<p>Missing ${missingFiles.length} file(s):</p>`;
        
        // Group by folder
        const groupedMissing = {};
        missingFiles.forEach(item => {
            if (!groupedMissing[item.folder]) {
                groupedMissing[item.folder] = [];
            }
            groupedMissing[item.folder].push(item.file);
        });
        
        for (const [folder, files] of Object.entries(groupedMissing)) {
            html += `<h4>${folder}/</h4><ul class="file-list missing">`;
            files.forEach(file => {
                html += `<li>${file}</li>`;
            });
            html += `</ul>`;
        }
    }
    
    html += `</div>`;
    
    // Show found files
    if (totalFound > 0) {
        html += `<div class="result-section success">
            <h3>Found Files (${totalFound})</h3>`;
        
        const groupedFound = {};
        uploadedFiles.forEach(file => {
            const pathParts = file.path.split(/[\/\\]/);
            if (pathParts.length >= 2) {
                const folder = pathParts[pathParts.length - 2];
                if (!groupedFound[folder]) {
                    groupedFound[folder] = [];
                }
                groupedFound[folder].push(file.name);
            }
        });
        
        for (const [folder, files] of Object.entries(groupedFound)) {
            html += `<h4>${folder}/</h4><ul class="file-list">`;
            files.forEach(file => {
                html += `<li>${file}</li>`;
            });
            html += `</ul>`;
        }
        
        html += `</div>`;
    }
    
    resultsDiv.innerHTML = html;
}
