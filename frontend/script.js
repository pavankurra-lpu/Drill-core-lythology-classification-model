// Global variables
let selectedFile = null;
let probChart = null;

// Geology Properties Mapping
const ROCK_METADATA = {
    "Granite": { hardness: "6.0 - 7.0", grain: "Coarse", era: "Precambrian", minerals: "Quartz, Feldspar, Mica", use: "Countertops, Construction" },
    "Sandstone": { hardness: "6.0 - 7.0", grain: "Medium", era: "Paleozoic", minerals: "Quartz, Clay minerals", use: "Building Stone, Aquifers" },
    "Limestone": { hardness: "3.0 - 4.0", grain: "Fine to Coarse", era: "Mesozoic", minerals: "Calcite, Aragonite", use: "Cement, Steel smelting" },
    "Basalt": { hardness: "5.0 - 6.0", grain: "Very Fine", era: "Cenozoic", minerals: "Plagioclase, Pyroxene", use: "Road Base, Concrete aggregate" },
    "Shale": { hardness: "2.5 - 3.0", grain: "Ultra Fine", era: "Paleozoic", minerals: "Clay minerals, Quartz", use: "Brick manufacture, Oil source" },
    "Quartzite": { hardness: "7.0", grain: "Medium", era: "Precambrian", minerals: "Quartz", use: "Railway ballast, Refractories" },
    "Marble": { hardness: "3.0 - 4.0", grain: "Medium to Coarse", era: "Paleozoic", minerals: "Calcite", use: "Sculptures, Building facades" },
    "Dolomite": { hardness: "3.5 - 4.0", grain: "Fine to Medium", era: "Triassic", minerals: "Dolomite", use: "Acid neutralizer, Road stone" },
    "Coal": { hardness: "1.0 - 2.5", grain: "Amorphous", era: "Carboniferous", minerals: "Organic Carbon", use: "Electricity generation, Steel" },
    "Gneiss": { hardness: "6.0 - 7.0", grain: "Coarse / Banded", era: "Precambrian", minerals: "Quartz, Feldspar, Biotite", use: "Crushed stone, Curbing" }
};

// Seed initial database logs
let coreDatabase = [
    {
        id: "CR-8201",
        timestamp: "2026-06-29 11:24",
        class: "Granite",
        confidence: 0.9840,
        geologist: "Kurra Pavan",
        preview: "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='100' height='76' viewBox='0 0 100 76'><rect width='100' height='76' fill='%239e9e9e'/><circle cx='30' cy='30' r='10' fill='%23616161'/><circle cx='70' cy='50' r='15' fill='%23757575'/><circle cx='50' cy='20' r='8' fill='%23424242'/></svg>"
    },
    {
        id: "CR-8202",
        timestamp: "2026-06-29 12:10",
        class: "Sandstone",
        confidence: 0.9425,
        geologist: "Kurra Pavan",
        preview: "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='100' height='76' viewBox='0 0 100 76'><rect width='100' height='76' fill='%23d7ccc8'/><line x1='0' y1='20' x2='100' y2='25' stroke='%238d6e63' stroke-width='4'/><line x1='0' y1='45' x2='100' y2='40' stroke='%23a1887f' stroke-width='6'/><line x1='0' y1='65' x2='100' y2='68' stroke='%238d6e63' stroke-width='3'/></svg>"
    },
    {
        id: "CR-8203",
        timestamp: "2026-06-29 14:05",
        class: "Basalt",
        confidence: 0.8872,
        geologist: "Kurra Pavan",
        preview: "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='100' height='76' viewBox='0 0 100 76'><rect width='100' height='76' fill='%23212121'/><circle cx='20' cy='40' r='4' fill='%23424242'/><circle cx='60' cy='20' r='6' fill='%23303030'/><circle cx='80' cy='55' r='5' fill='%23424242'/></svg>"
    },
    {
        id: "CR-8204",
        timestamp: "2026-06-29 15:30",
        class: "Coal",
        confidence: 0.9912,
        geologist: "Kurra Pavan",
        preview: "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='100' height='76' viewBox='0 0 100 76'><rect width='100' height='76' fill='%23111111'/><path d='M10,20 L30,40 L60,10' stroke='%23222' stroke-width='3' fill='none'/><circle cx='70' cy='60' r='10' fill='%23000'/></svg>"
    },
    {
        id: "CR-8205",
        timestamp: "2026-06-29 17:15",
        class: "Gneiss",
        confidence: 0.8540,
        geologist: "Kurra Pavan",
        preview: "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='100' height='76' viewBox='0 0 100 76'><rect width='100' height='76' fill='%23757575'/><path d='M0,15 Q30,30 60,10 T100,20' stroke='%23eeeeee' stroke-width='6' fill='none'/><path d='M0,45 Q40,25 70,55 T100,35' stroke='%23333333' stroke-width='8' fill='none'/><path d='M0,65 Q20,68 50,55 T100,68' stroke='%23eeeeee' stroke-width='4' fill='none'/></svg>"
    }
];

// Document Ready
document.addEventListener("DOMContentLoaded", () => {
    // Initialize icons
    lucide.createIcons();

    // Set active tab buttons
    const navItems = document.querySelectorAll(".nav-item");
    navItems.forEach(item => {
        item.addEventListener("click", () => {
            const tabId = item.getAttribute("data-tab");
            switchTab(tabId);
        });
    });

    // File Drag and Drop listeners
    const dropZone = document.getElementById("drop-zone");
    const fileInput = document.getElementById("file-input");
    const predictBtn = document.getElementById("predict-btn");
    const clearImgBtn = document.getElementById("clear-img-btn");

    dropZone.addEventListener("click", () => {
        if (!selectedFile) {
            fileInput.click();
        }
    });

    fileInput.addEventListener("change", (e) => {
        if (e.target.files.length > 0) {
            handleFileSelect(e.target.files[0]);
        }
    });

    ["dragenter", "dragover"].forEach(eventName => {
        dropZone.addEventListener(eventName, (e) => {
            e.preventDefault();
            e.stopPropagation();
            dropZone.classList.add("drag-over");
        }, false);
    });

    ["dragleave", "drop"].forEach(eventName => {
        dropZone.addEventListener(eventName, (e) => {
            e.preventDefault();
            e.stopPropagation();
            dropZone.classList.remove("drag-over");
        }, false);
    });

    dropZone.addEventListener("drop", (e) => {
        const dt = e.dataTransfer;
        const files = dt.files;
        if (files.length > 0) {
            handleFileSelect(files[0]);
        }
    });

    clearImgBtn.addEventListener("click", (e) => {
        e.stopPropagation(); // Avoid click event bubbling to dropzone open files
        resetPredictInterface();
    });

    predictBtn.addEventListener("click", () => {
        if (selectedFile) {
            runClassifierInference();
        }
    });

    // Database search and filter input events
    document.getElementById("db-search").addEventListener("input", filterCoreDatabaseTable);
    document.getElementById("db-filter-class").addEventListener("change", filterCoreDatabaseTable);

    // Initial renders
    updateDashboardStats();
    renderRecentActivities();
    renderCoreDatabaseTable(coreDatabase);
});

// Switching view states
function switchTab(tabId) {
    // Toggle active classes on sidebar links and content panes
    document.querySelectorAll(".nav-item").forEach(item => item.classList.remove("active"));
    document.querySelectorAll(".tab-pane").forEach(pane => pane.classList.remove("active"));

    const activeItem = document.querySelector(`.nav-item[data-tab="${tabId}"]`);
    const activePane = document.getElementById(`${tabId}-tab`);

    if (activeItem && activePane) {
        activeItem.classList.add("active");
        activePane.classList.add("active");
    }

    // Set page title and subtitle
    const pageTitle = document.getElementById("page-title");
    const pageSubtitle = document.getElementById("page-subtitle");

    switch(tabId) {
        case "dashboard":
            pageTitle.textContent = "Dashboard";
            pageSubtitle.textContent = "Stratigraphic logs and platform overview.";
            break;
        case "classifier":
            pageTitle.textContent = "Lithology Classifier";
            pageSubtitle.textContent = "Inference workspace to identify core samples.";
            break;
        case "database":
            pageTitle.textContent = "Core Database";
            pageSubtitle.textContent = "Central archive of all classified drill cores.";
            break;
        case "about":
            pageTitle.textContent = "About Platform";
            pageSubtitle.textContent = "Detailed system architecture and model pipeline.";
            break;
    }
}

// Handling uploaded core images
function handleFileSelect(file) {
    const allowedTypes = ["image/jpeg", "image/png", "image/webp", "image/bmp"];
    if (!allowedTypes.includes(file.type)) {
        alert("Please upload a valid image (JPG, PNG, WEBP, or BMP).");
        return;
    }

    if (file.size > 10 * 1024 * 1024) {
        alert("Image exceeds 10MB size limit.");
        return;
    }

    selectedFile = file;

    const reader = new FileReader();
    reader.onload = (e) => {
        document.getElementById("image-preview").src = e.target.result;
        document.querySelector(".drop-prompt").style.display = "none";
        document.getElementById("preview-container").style.display = "flex";
        document.getElementById("predict-btn").removeAttribute("disabled");
    };
    reader.readAsDataURL(file);
}

// Clearing image selection
function resetPredictInterface() {
    selectedFile = null;
    document.getElementById("file-input").value = "";
    document.querySelector(".drop-prompt").style.display = "flex";
    document.getElementById("preview-container").style.display = "none";
    document.getElementById("image-preview").src = "";
    document.getElementById("predict-btn").setAttribute("disabled", "true");

    // Hide output contents
    document.getElementById("results-content").style.display = "none";
    document.getElementById("results-loading").style.display = "none";
    document.getElementById("results-empty").style.display = "block";
}

// Execute predicted classification through FastAPI backend
async function runClassifierInference() {
    if (!selectedFile) return;

    const resultsEmpty = document.getElementById("results-empty");
    const resultsLoading = document.getElementById("results-loading");
    const resultsContent = document.getElementById("results-content");
    const predictBtn = document.getElementById("predict-btn");

    // Show loading
    resultsEmpty.style.display = "none";
    resultsContent.style.display = "none";
    resultsLoading.style.display = "block";
    predictBtn.setAttribute("disabled", "true");

    const formData = new FormData();
    formData.append("file", selectedFile);

    try {
        const response = await fetch("/api/predict", {
            method: "POST",
            body: formData
        });

        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.detail || "Server inference error.");
        }

        const data = await response.json();

        // Convert the current uploaded file to a base64 string to keep a local history preview
        const reader = new FileReader();
        reader.onloadend = () => {
            const previewUrl = reader.result;
            // Append prediction log into the database
            const newRecord = {
                id: `CR-${Math.floor(1000 + Math.random() * 9000)}`,
                timestamp: getCurrentDateTime(),
                class: data.predicted_class,
                confidence: data.confidence,
                geologist: "Kurra Pavan",
                preview: previewUrl
            };

            coreDatabase.unshift(newRecord); // Add to beginning

            // Re-render components
            updateDashboardStats();
            renderRecentActivities();
            renderCoreDatabaseTable(coreDatabase);
        };
        reader.readAsDataURL(selectedFile);

        // Display results
        displayPredictionResults(data);

    } catch (e) {
        console.error(e);
        alert(`Core classification failed: ${e.message}`);
        resultsLoading.style.display = "none";
        resultsEmpty.style.display = "block";
    } finally {
        predictBtn.removeAttribute("disabled");
    }
}

// Render inference results on results pane
function displayPredictionResults(data) {
    const resultsLoading = document.getElementById("results-loading");
    const resultsContent = document.getElementById("results-content");
    const rockName = document.getElementById("predicted-rock-name");
    const confidenceText = document.getElementById("confidence-text");
    const confidenceBar = document.getElementById("confidence-bar");
    const rockDesc = document.getElementById("predicted-rock-desc");

    resultsLoading.style.display = "none";
    resultsContent.style.display = "flex";

    // Inject general parameters
    rockName.textContent = data.predicted_class;
    rockDesc.textContent = data.description;
    
    const confidencePercent = (data.confidence * 100).toFixed(1);
    confidenceText.textContent = `${confidencePercent}% Confidence`;
    
    // Animate progress bar fill
    setTimeout(() => {
        confidenceBar.style.width = `${confidencePercent}%`;
    }, 100);

    // Inject structured geology properties
    const props = ROCK_METADATA[data.predicted_class] || { hardness: "-", grain: "-", era: "-", minerals: "-", use: "-" };
    document.getElementById("rock-prop-hardness").textContent = props.hardness;
    document.getElementById("rock-prop-grain").textContent = props.grain;
    document.getElementById("rock-prop-era").textContent = props.era;
    document.getElementById("rock-prop-minerals").textContent = props.minerals;
    document.getElementById("rock-prop-use").textContent = props.use;

    // Render probability chart
    const labels = data.top_3.map(item => item.class);
    const probabilities = data.top_3.map(item => item.probability * 100);

    if (probChart) {
        probChart.destroy();
    }

    const ctx = document.getElementById("probabilities-chart").getContext("2d");
    probChart = new Chart(ctx, {
        type: "bar",
        data: {
            labels: labels,
            datasets: [{
                data: probabilities,
                backgroundColor: [
                    "rgba(16, 185, 129, 0.8)", // Green for winner
                    "rgba(255, 255, 255, 0.12)",
                    "rgba(255, 255, 255, 0.08)"
                ],
                borderColor: [
                    "#10b981",
                    "rgba(255, 255, 255, 0.2)",
                    "rgba(255, 255, 255, 0.1)"
                ],
                borderWidth: 1,
                borderRadius: 4,
                barThickness: 16
            }]
        },
        options: {
            indexAxis: "y",
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    backgroundColor: "#0c0f12",
                    titleFont: { family: "Outfit", size: 11 },
                    bodyFont: { family: "Plus Jakarta Sans", size: 11 },
                    borderColor: "rgba(255, 255, 255, 0.08)",
                    borderWidth: 1,
                    callbacks: {
                        label: (context) => ` ${context.parsed.x.toFixed(1)}%`
                    }
                }
            },
            scales: {
                x: {
                    min: 0,
                    max: 100,
                    grid: { color: "rgba(255, 255, 255, 0.03)" },
                    ticks: {
                        color: "#6b7280",
                        font: { family: "Plus Jakarta Sans", size: 10 },
                        callback: (v) => v + "%"
                    }
                },
                y: {
                    grid: { display: false },
                    ticks: {
                        color: "#f3f4f6",
                        font: { family: "Outfit", size: 12, weight: "600" }
                    }
                }
            }
        }
    });
}

// Update stats card counts
function updateDashboardStats() {
    document.getElementById("stat-total-cores").textContent = coreDatabase.length;
}

// Render recent predictions on Dashboard Overview timeline
function renderRecentActivities() {
    const timeline = document.getElementById("recent-activity-timeline");
    timeline.innerHTML = "";

    // Render top 4 recent records
    const recentLogs = coreDatabase.slice(0, 4);

    if (recentLogs.length === 0) {
        timeline.innerHTML = "<p class='text-muted text-sm'>No records logged yet.</p>";
        return;
    }

    recentLogs.forEach(log => {
        const isHighConf = log.confidence >= 0.90;
        const formattedConf = (log.confidence * 100).toFixed(1);
        
        const activityHtml = `
            <div class="activity-item ${isHighConf ? 'high-conf' : ''}">
                <div class="activity-bullet"></div>
                <div class="activity-details">
                    <div class="activity-top">
                        <span class="activity-title">${log.class} Classification</span>
                        <span class="activity-time">${formatTimeAgo(log.timestamp)}</span>
                    </div>
                    <div class="activity-meta">
                        <span>Record: <span class="font-mono">${log.id}</span></span>
                        <span class="${isHighConf ? 'text-green' : 'text-amber'} font-weight-bold">${formattedConf}% confidence</span>
                    </div>
                </div>
            </div>
        `;
        timeline.insertAdjacentHTML("beforeend", activityHtml);
    });
}

// Render database page table rows
function renderCoreDatabaseTable(dataList) {
    const tbody = document.getElementById("db-table-body");
    tbody.innerHTML = "";

    if (dataList.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="7" style="text-align: center; color: var(--text-dim); padding: 40px 0;">
                    <i data-lucide="database-backup" style="width: 32px; height: 32px; margin-bottom: 8px; stroke: var(--text-dim);"></i>
                    <p>No matching core records found.</p>
                </td>
            </tr>
        `;
        lucide.createIcons();
        return;
    }

    dataList.forEach(record => {
        const confPercent = (record.confidence * 100).toFixed(1);
        const rowHtml = `
            <tr id="row-${record.id}">
                <td class="font-mono" style="font-weight: 700; color: var(--text-main);">${record.id}</td>
                <td style="color: var(--text-muted);">${record.timestamp}</td>
                <td>
                    <div class="td-preview-box">
                        <img src="${record.preview}" alt="${record.class} microview" class="td-preview-img">
                    </div>
                </td>
                <td style="font-weight: 700;">${record.class}</td>
                <td>
                    <span class="badge ${record.confidence >= 0.90 ? 'badge-green' : 'badge-amber'}">
                        ${confPercent}%
                    </span>
                </td>
                <td style="color: var(--text-muted);">${record.geologist}</td>
                <td>
                    <button class="btn-icon" onclick="deleteCoreRecord('${record.id}')" title="Delete record">
                        <i data-lucide="trash-2"></i>
                    </button>
                </td>
            </tr>
        `;
        tbody.insertAdjacentHTML("beforeend", rowHtml);
    });

    lucide.createIcons();
}

// Search and filter database table
function filterCoreDatabaseTable() {
    const searchQuery = document.getElementById("db-search").value.toLowerCase();
    const filterClass = document.getElementById("db-filter-class").value;

    const filteredList = coreDatabase.filter(record => {
        const matchesSearch = record.id.toLowerCase().includes(searchQuery) ||
                              record.class.toLowerCase().includes(searchQuery) ||
                              record.geologist.toLowerCase().includes(searchQuery);

        const matchesClass = filterClass === "all" || record.class === filterClass;

        return matchesSearch && matchesClass;
    });

    renderCoreDatabaseTable(filteredList);
}

// Delete core record
function deleteCoreRecord(recordId) {
    if (confirm(`Are you sure you want to delete core record ${recordId}?`)) {
        coreDatabase = coreDatabase.filter(record => record.id !== recordId);
        
        // Re-render
        updateDashboardStats();
        renderRecentActivities();
        filterCoreDatabaseTable(); // Maintains current filter states
    }
}

// Utility functions
function getCurrentDateTime() {
    const now = new Date();
    const yyyy = now.getFullYear();
    const mm = String(now.getMonth() + 1).padStart(2, '0');
    const dd = String(now.getDate()).padStart(2, '0');
    const hh = String(now.getHours()).padStart(2, '0');
    const min = String(now.getMinutes()).padStart(2, '0');
    return `${yyyy}-${mm}-${dd} ${hh}:${min}`;
}

function formatTimeAgo(dateStr) {
    // Simple helper to format time since it's simulated
    const now = new Date();
    const past = new Date(dateStr.replace(' ', 'T'));
    const diffMs = now - past;
    const diffMins = Math.floor(diffMs / 60000);

    if (diffMins < 1) return "Just now";
    if (diffMins < 60) return `${diffMins}m ago`;
    
    const diffHours = Math.floor(diffMins / 60);
    if (diffHours < 24) return `${diffHours}h ago`;

    return dateStr.split(' ')[1]; // Returns HH:MM
}
