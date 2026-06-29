// Global variables
let selectedFile = null;
let probChart = null;

// Initialize when DOM is loaded
document.addEventListener("DOMContentLoaded", () => {
    // Initialize Lucide Icons
    lucide.createIcons();

    // Tab Navigation setup
    const navButtons = document.querySelectorAll(".nav-btn");
    navButtons.forEach(btn => {
        btn.addEventListener("click", () => {
            const tabId = btn.getAttribute("data-tab");
            switchTab(tabId);
        });
    });

    // Drag and Drop Area setup
    const dropZone = document.getElementById("drop-zone");
    const fileInput = document.getElementById("file-input");
    const browseBtn = document.getElementById("browse-btn");
    const clearImgBtn = document.getElementById("clear-img-btn");
    const predictBtn = document.getElementById("predict-btn");

    // Click on browse button triggers file input
    browseBtn.addEventListener("click", (e) => {
        e.stopPropagation(); // Avoid triggering drop-zone click
        fileInput.click();
    });

    // Click on drop zone itself triggers file input if empty
    dropZone.addEventListener("click", () => {
        if (!selectedFile) {
            fileInput.click();
        }
    });

    // File input selection change
    fileInput.addEventListener("change", (e) => {
        if (e.target.files.length > 0) {
            handleFileSelection(e.target.files[0]);
        }
    });

    // Drag-and-drop event listeners
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
            handleFileSelection(files[0]);
        }
    });

    // Clear image selection
    clearImgBtn.addEventListener("click", (e) => {
        e.stopPropagation(); // Prevent opening browse file dialog
        resetImageUpload();
    });

    // Run prediction on button click
    predictBtn.addEventListener("click", () => {
        if (selectedFile) {
            runLithologyClassification();
        }
    });
});

// Function to switch tabs
function switchTab(tabId) {
    // Deactivate all tabs and contents
    document.querySelectorAll(".nav-btn").forEach(btn => btn.classList.remove("active"));
    document.querySelectorAll(".tab-content").forEach(content => content.classList.remove("active"));

    // Activate target tab button and content
    const activeBtn = document.querySelector(`.nav-btn[data-tab="${tabId}"]`);
    const activeContent = document.getElementById(`${tabId}-tab`);
    
    if (activeBtn && activeContent) {
        activeBtn.classList.add("active");
        activeContent.classList.add("active");
    }
}

// Function to handle the selected file
function handleFileSelection(file) {
    // Validate file type
    const allowedTypes = ["image/jpeg", "image/png", "image/webp", "image/bmp"];
    if (!allowedTypes.includes(file.type)) {
        alert("Please upload a valid image file (JPG, PNG, WEBP, or BMP).");
        return;
    }

    // Validate size (max 10MB)
    if (file.size > 10 * 1024 * 1024) {
        alert("File size exceeds 10MB limit. Please upload a smaller image.");
        return;
    }

    selectedFile = file;

    // Show image preview
    const reader = new FileReader();
    reader.onload = (e) => {
        const previewImg = document.getElementById("image-preview");
        previewImg.src = e.target.result;
        
        // Toggle view from prompt to preview
        document.querySelector(".drop-zone-prompt").style.display = "none";
        document.getElementById("preview-container").style.display = "flex";
        
        // Enable predict button
        document.getElementById("predict-btn").removeAttribute("disabled");
    };
    reader.readAsDataURL(file);
}

// Reset image upload state
function resetImageUpload() {
    selectedFile = null;
    document.getElementById("file-input").value = "";
    
    // Toggle view back to prompt
    document.querySelector(".drop-zone-prompt").style.display = "flex";
    document.getElementById("preview-container").style.display = "none";
    document.getElementById("image-preview").src = "";
    
    // Disable predict button
    document.getElementById("predict-btn").setAttribute("disabled", "true");

    // Clear prediction panels
    document.getElementById("results-content").style.display = "none";
    document.getElementById("results-loading").style.display = "none";
    document.getElementById("results-empty").style.display = "block";
}

// Run prediction calling the backend
async function runLithologyClassification() {
    if (!selectedFile) return;

    const resultsEmpty = document.getElementById("results-empty");
    const resultsLoading = document.getElementById("results-loading");
    const resultsContent = document.getElementById("results-content");
    const predictBtn = document.getElementById("predict-btn");

    // Set UI to loading state
    resultsEmpty.style.display = "none";
    resultsContent.style.display = "none";
    resultsLoading.style.display = "block";
    predictBtn.setAttribute("disabled", "true");

    // Prepare Multipart Form Data
    const formData = new FormData();
    formData.append("file", selectedFile);

    try {
        // Send request to FastAPI /predict
        // Use relative URL so it functions both locally and hosted (e.g. on Hugging Face)
        const response = await fetch("/api/predict", {
            method: "POST",
            body: formData
        });

        if (!response.ok) {
            const errData = await response.json();
            throw new Error(errData.detail || "Server error occurred during classification.");
        }

        const data = await response.json();

        // Process output data
        displayResults(data);

    } catch (error) {
        console.error("Inference Error:", error);
        alert(`Classification Failed: ${error.message}`);
        
        // Reset results panel
        resultsLoading.style.display = "none";
        resultsEmpty.style.display = "block";
    } finally {
        // Re-enable predict button
        predictBtn.removeAttribute("disabled");
    }
}

// Render inference results on the UI
function displayResults(data) {
    const resultsLoading = document.getElementById("results-loading");
    const resultsContent = document.getElementById("results-content");
    const rockNameEl = document.getElementById("predicted-rock-name");
    const confidenceTextEl = document.getElementById("confidence-text");
    const confidenceBarEl = document.getElementById("confidence-bar");
    const rockDescEl = document.getElementById("predicted-rock-desc");

    // Hide loader, show result content
    resultsLoading.style.display = "none";
    resultsContent.style.display = "block";

    // Set rock name and description
    rockNameEl.textContent = data.predicted_class;
    rockDescEl.textContent = data.description;

    // Set confidence
    const confPercent = (data.confidence * 100).toFixed(1);
    confidenceTextEl.textContent = `${confPercent}% Confidence`;
    
    // Trigger transition delay for progress bar fill animation
    setTimeout(() => {
        confidenceBarEl.style.width = `${confPercent}%`;
    }, 100);

    // Prepare data for Chart.js
    const labels = data.top_3.map(item => item.class);
    const probabilities = data.top_3.map(item => item.probability * 100);

    // Destroy existing chart if it exists to prevent overlap
    if (probChart) {
        probChart.destroy();
    }

    // Render new horizontal bar chart
    const ctx = document.getElementById("probabilities-chart").getContext("2d");
    
    // Retrieve colors matching CSS styling variables
    const amberAccent = "#f59e0b";
    
    probChart = new Chart(ctx, {
        type: "bar",
        data: {
            labels: labels,
            datasets: [{
                data: probabilities,
                backgroundColor: [
                    "rgba(16, 185, 129, 0.75)", // Emerald for predicted class
                    "rgba(255, 255, 255, 0.12)", // Dim white for others
                    "rgba(255, 255, 255, 0.08)"
                ],
                borderColor: [
                    "#10b981",
                    "rgba(255, 255, 255, 0.2)",
                    "rgba(255, 255, 255, 0.1)"
                ],
                borderWidth: 1,
                borderRadius: 4,
                barThickness: 22
            }]
        },
        options: {
            indexAxis: "y", // Makes the bar chart horizontal
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false // Hide legend
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return ` ${context.parsed.x.toFixed(1)}%`;
                        }
                    },
                    backgroundColor: "#161c22",
                    titleFont: { family: "Outfit", size: 12 },
                    bodyFont: { family: "Plus Jakarta Sans", size: 12 },
                    borderColor: "rgba(255, 255, 255, 0.08)",
                    borderWidth: 1
                }
            },
            scales: {
                x: {
                    min: 0,
                    max: 100,
                    grid: {
                        color: "rgba(255, 255, 255, 0.04)"
                    },
                    ticks: {
                        color: "#6b7280",
                        font: { family: "Plus Jakarta Sans", size: 11 },
                        callback: function(value) {
                            return value + "%";
                        }
                    }
                },
                y: {
                    grid: {
                        display: false
                    },
                    ticks: {
                        color: "#f3f4f6",
                        font: { family: "Outfit", size: 13, weight: "600" }
                    }
                }
            }
        }
    });
}
