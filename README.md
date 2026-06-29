# Drill Core Lithology Classification System

An end-to-end Machine Learning web application designed to automate the logging and classification of stratigraphic drill core rock samples. 

The system leverages a **ResNet50 Deep Convolutional Neural Network (Transfer Learning)** trained using TensorFlow/Keras to classify core slices into 10 distinct lithological classes. It serves predictions via a **FastAPI backend** and presents findings in a modern, **geology-inspired dark UI website**.

---

## Folder Structure

```text
├── ml/
│   └── train.py           # ML Model training, evaluation, and synthetic dataset generator
├── backend/
│   └── app.py             # FastAPI backend with /predict endpoint and static files serving
├── frontend/
│   ├── index.html         # Three-page SPA (Home, Predict, About) with dark geology theme
│   ├── style.css          # Premium custom CSS styling
│   └── script.js          # Chart.js visualization, drag-and-drop, API connection
├── Dockerfile             # Container configuration for Hugging Face Spaces
├── requirements.txt       # Dependencies (fastapi, tensorflow, pillow, scikit-learn, etc.)
└── README.md              # Project documentation and deployment instructions
```

---

## Supported Classes (10 Lithologies)

- **Igneous**: Granite, Basalt
- **Sedimentary**: Sandstone, Limestone, Shale, Dolomite, Coal
- **Metamorphic**: Quartzite, Marble, Gneiss

---

## Local Setup & Run Instructions

### 1. Prerequisites
Ensure you have **Python 3.10+** installed on your system.

### 2. Create and Activate a Virtual Environment
Navigate to the project root directory and run:

```bash
# Create Virtual Environment
python -m venv venv

# Activate Virtual Environment
# On Windows (PowerShell):
venv\Scripts\Activate.ps1
# On Windows (CMD):
venv\Scripts\activate.bat
# On macOS / Linux:
source venv/bin/activate
```

### 3. Install Dependencies
Install all required libraries inside the virtual environment:

```bash
pip install -r requirements.txt
```

### 4. Generate/Train the Model (`model.h5`)
You need a trained `model.h5` in the root of the workspace for the FastAPI server to start. You can generate it using the following options:

*   **Option A: Generate a Dummy Model (Rapid Testing)**
    Instantly compiles a small CNN matching the input/output signatures and saves it. Recommended to quickly see the web application in action:
    ```bash
    python ml/train.py --dummy
    ```

*   **Option B: Generate Synthetic Data and Train (Test Full Pipeline)**
    Automatically generates synthetic colored rock patterns across the 10 classes and trains a ResNet50 model for 5 epochs, producing evaluation metrics and saving the model:
    ```bash
    python ml/train.py --generate_synthetic --epochs 5
    ```

*   **Option C: Train on Custom Core Dataset**
    If you have your own dataset organized in directories (e.g. `dataset/Granite/`, `dataset/Sandstone/` etc.), run:
    ```bash
    python ml/train.py --data_dir dataset --epochs 10
    ```

### 5. Start the FastAPI Server
Run the FastAPI development server:

```bash
uvicorn backend.app:app --reload
```

Open your browser and visit: **`http://127.0.0.1:8000/`**

---

## Deploying to Hugging Face Spaces (Step-by-Step)

Hugging Face Spaces is an easy way to host ML applications for free. Because this application contains both a Python API and static assets, we deploy it using the **Docker SDK**.

### Step 1: Create a Hugging Face Account
Go to [huggingface.co](https://huggingface.co/) and sign up or log in.

### Step 2: Create a New Space
1. Click on your profile picture in the top-right and select **"New Space"**.
2. Set a **Space Name** (e.g., `drill-core-lithology-classifier`).
3. Select **Docker** as the SDK.
4. Under Docker templates, select **Blank** (our custom `Dockerfile` handles everything).
5. Choose **Public** or **Private** visibility.
6. Click **"Create Space"**.

### Step 3: Clone the Space Repository
Locally, clone the Hugging Face repository created for your Space (replace `username` and `space-name`):

```bash
git clone https://huggingface.co/spaces/username/space-name
```

### Step 4: Copy Code and Push
1. Copy all folders and files from this project (`ml/`, `backend/`, `frontend/`, `requirements.txt`, `Dockerfile`, `README.md`) into your cloned repository folder.
2. Commit and push the changes:

```bash
git add .
git commit -m "Initial commit of lithology classification system"
git push
```

### Step 5: Wait for Build to Complete
Hugging Face will automatically detect the `Dockerfile`, install the dependencies from `requirements.txt`, trigger the `python ml/train.py --dummy` script to generate a model container, and boot the FastAPI application.

After 2–3 minutes, your live web app will be accessible directly in the browser!
