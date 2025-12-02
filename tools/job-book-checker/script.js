let uploadedFiles = [];

const REQUIRED_STRUCTURE = {
    "Transport": [
        "*Base* *Inspection*",
        "*Base* *Transport*",
        "*M1* *Inspection*",
        "*M1* *Transport*",
        "*M2* *Inspection*",
        "*M2* *Transport*",
        "*M3* *Inspection*",
        "*M3* *Transport*",
        "*Top* *Inspection*",
        "*Top* *Transport*",
        "*DriveTrain* *Inspection*",
        "*DriveTrain* *Transport*",
        "*Nacelle* *Inspection*",
        "*Nacelle* *Transport*",
        "*Hub* *Inspection*",
        "*Hub* *Transport*",
        "*Blade* *Inspection* x3",
        "*Blade* *Transport* x3"
    ],
    "Mechanical": [
        "*10 Percent Checklists*",
        "*Bolt Certificates*",
        "*Flange Reports*",
        "*Aviation Light Manual*",
        "*Rescue Kit Inspection*",
        "*Safety Cable Checklist*",
        "*Foundation Tensioning Concrete and Grout Documents*",
        "*Quality Control of Foundation Earthing*",
        "*Quality Control of Earthing Between Turbines*",
        "*Hardware Lubrication Checklist*",
        "*Generator Alignment Test Report*",
        "*High Voltage Cable Test Report*",
        "*Recording of Main Components*",
        "*Service Inspection Form*",
        "*Mechanical Completion Checklist*",
        "*Mechanical Completion Certificate*",
        "*Punchlist*",
        "*Service Lift Installation Checklist*"
    ],
    "Commissioning": [
        "*CMS Commissioning Procedure*",
        "*Pre-Commissioning Certificate*",
        "*Commissioning Completion Certificate*",
        "*Start-Up Procedure*",
        "*SCADA Functionality Checklist*",
        "*Birth Certificate*",
        "*Final Punchlist*"
    ]
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
    const files = Array.from(e.target.files);
    uploadedFiles = files.map(file => ({
        name: file.name,
        path: file.webkitRelativePath || file.name,
        file: file
    }));
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
    
    // Helper function to convert wildcard pattern to regex
    function wildcardToRegex(pattern) {
        const regexPattern = pattern
            .replace(/[.+?^${}()|[\]\\]/g, '\\$&')
            .replace(/\*/g, '.*');
        return new RegExp(`^${regexPattern}$`, 'i');
    }
    
    // Helper function to check if a file matches a pattern
    function matchesPattern(filename, pattern) {
        const cleanPattern = pattern.replace(/ x\d+$/, '');
        const regex = wildcardToRegex(cleanPattern);
        return regex.test(filename);
    }
    
    // Group files by tower (top-level folder)
    const towerGroups = {};
    uploadedFiles.forEach(file => {
        const pathParts = file.path.split(/[\/\\]/);
        // The tower name is typically the first or second folder in the path
        // We'll use the folder that appears before Transport/Mechanical/Commissioning
        let towerName = 'Unknown';
        
        for (let i = 0; i < pathParts.length; i++) {
            const part = pathParts[i];
            // Check if this or next part contains one of our category folders
            const isCategory = ['transport', 'mechanical', 'commissioning'].some(cat => 
                part.toLowerCase().includes(cat)
            );
            
            if (isCategory && i > 0) {
                // The tower name is the parent folder
                towerName = pathParts[i - 1];
                break;
            }
        }
        
        if (!towerGroups[towerName]) {
            towerGroups[towerName] = [];
        }
        towerGroups[towerName].push(file);
    });
    
    // If only one tower group and it's "Unknown", treat all files as one tower
    const towerNames = Object.keys(towerGroups);
    let html = '';
    
    if (towerNames.length === 1 && towerNames[0] === 'Unknown') {
        // Single tower mode
        html = checkSingleTower('Job Book', uploadedFiles);
    } else {
        // Multiple towers mode
        html = '<div class="towers-summary">';
        
        let totalTowers = towerNames.filter(n => n !== 'Unknown').length;
        let completeTowers = 0;
        
        // Check each tower
        for (const [towerName, files] of Object.entries(towerGroups)) {
            if (towerName === 'Unknown' && files.length === 0) continue;
            
            const result = checkSingleTower(towerName, files);
            const isComplete = !result.includes('class="warning"');
            if (isComplete && towerName !== 'Unknown') completeTowers++;
            
            html += result;
        }
        
        html = `<div class="result-section info">
            <div class="summary">
                ${completeTowers} of ${totalTowers} towers complete
            </div>
        </div>` + html;
        
        html += '</div>';
    }
    
    resultsDiv.innerHTML = html;
}

function checkSingleTower(towerName, towerFiles) {
    let totalRequired = 0;
    let totalFound = 0;
    let missingFiles = [];
    
    // Helper function to convert wildcard pattern to regex
    function wildcardToRegex(pattern) {
        const regexPattern = pattern
            .replace(/[.+?^${}()|[\]\\]/g, '\\$&')
            .replace(/\*/g, '.*');
        return new RegExp(`^${regexPattern}$`, 'i');
    }
    
    // Helper function to check if a file matches a pattern
    function matchesPattern(filename, pattern) {
        const cleanPattern = pattern.replace(/ x\d+$/, '');
        const regex = wildcardToRegex(cleanPattern);
        return regex.test(filename);
    }
    
    // Check folders and files
    for (const [folderName, patterns] of Object.entries(REQUIRED_STRUCTURE)) {
        patterns.forEach(pattern => {
            const multiplierMatch = pattern.match(/ x(\d+)$/);
            const requiredCount = multiplierMatch ? parseInt(multiplierMatch[1]) : 1;
            const cleanPattern = pattern.replace(/ x\d+$/, '');
            
            totalRequired += requiredCount;
            
            const matchingFiles = towerFiles.filter(file => {
                const pathParts = file.path.split(/[\/\\]/);
                const inCorrectFolder = pathParts.some(part => 
                    part.toLowerCase().includes(folderName.toLowerCase())
                );
                return inCorrectFolder && matchesPattern(file.name, cleanPattern);
            });
            
            const foundCount = matchingFiles.length;
            
            if (foundCount >= requiredCount) {
                totalFound += requiredCount;
            } else {
                totalFound += foundCount;
                for (let i = foundCount; i < requiredCount; i++) {
                    missingFiles.push({
                        folder: folderName,
                        pattern: pattern
                    });
                }
            }
        });
    }
    
    const summaryClass = missingFiles.length === 0 ? 'success' : 'warning';
    
    let html = `
        <div class="result-section ${summaryClass}">
            <h3>${towerName}</h3>
            <div class="summary">
                ${totalFound} of ${totalRequired} required files found
            </div>
    `;
    
    if (missingFiles.length === 0) {
        html += `<p>✓ All required files are present!</p>`;
    } else {
        html += `<p>Missing ${missingFiles.length} file(s):</p>`;
        
        const groupedMissing = {};
        missingFiles.forEach(item => {
            if (!groupedMissing[item.folder]) {
                groupedMissing[item.folder] = [];
            }
            groupedMissing[item.folder].push(item.pattern);
        });
        
        for (const [folder, patterns] of Object.entries(groupedMissing)) {
            html += `<h4>${folder}/</h4><ul class="file-list missing">`;
            patterns.forEach(pattern => {
                html += `<li>${pattern}</li>`;
            });
            html += `</ul>`;
        }
    }
    
    html += `</div>`;
    
    return html;
}
