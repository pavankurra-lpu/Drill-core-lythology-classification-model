# 🪨 Automated Lithology Classification System for Drill Core Samples

An enterprise-grade AI system for automated petrographic core scanning, lithology classification, mineral prediction, and geological reporting. Powered by Deep Learning (EfficientNet-B3 / ResNet50) and LLM-driven Retrieval-Augmented Generation (RAG).

---

## ✨ Features

- **Drill-Core Image Classification**: Immediate diagnostic prediction of rock classes and mineral percentages using EfficientNet-B3/ResNet50 models.
- **RAG Geological Assistant**: Interact with an LLM chatbot trained on stratigraphic manuals, or upload PDF reports to consult custom borehole datasets.
- **Automated PDF Compiling**: Instantly compile professional petrographic diagnostic reports using ReportLab.
- **Dataset Retraining**: Ingest custom zip datasets with folders structured as label indices, and trigger Celery training nodes.
- **Analytics Overview**: Interactive distribution timelines and confidence charts powered by Recharts.
- **JWT Node Authentication**: Complete security mapping using JWT access/refresh tokens.

---

## 🏗️ Architecture

```
                       ┌───────────────────────┐
                       │      Nginx Proxy      │
                       └───────────┬───────────┘
                                   │
                 ┌─────────────────┴─────────────────┐
                 ▼                                   ▼
        ┌─────────────────┐                 ┌─────────────────┐
        │ React Frontend  │                 │  FastAPI Server │
        │   (Vite + TS)   │                 │     (Port 8000) │
        └─────────────────┘                 └────────┬────────┘
                                                     │
                                           ┌─────────┴─────────┐
                                           ▼                   ▼
                                  ┌────────────────┐   ┌───────────────┐
                                  │ Celery Workers │   │ PostgreSQL DB │
                                  │ (Redis broker) │   └───────────────┘
                                  └────────────────┘
```

---

## 🛠️ Tech Stack

| Component | Technology |
|---|---|
| **Backend** | Python 3.12, FastAPI, SQLAlchemy 2.0 async, Pydantic V2, Celery |
| **Frontend** | React 19, Vite, TypeScript, Tailwind CSS, Zustand, Recharts |
| **Machine Learning** | PyTorch, torchvision, Albumentations, OpenCV |
| **LLM & RAG** | SentenceTransformers, FAISS, LangChain |
| **DevOps** | Docker, Docker Compose, Nginx, Redis, PostgreSQL |

---

## 🚀 Local Quick Start (No Docker Required)

This project has been engineered to run locally with zero infrastructure setup. Database tables are automatically initialized and seeded with mock entries on backend startup.

### 1. Start the Backend API
```bash
cd backend

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\activate

# Install requirements
pip install -r requirements.txt

# Start FastAPI server
uvicorn app.main:app --reload --port 8000
```
- **FastAPI Documentation**: http://localhost:8000/docs
- Database will be initialized in `backend/lithology.db` with seeded data.

### 2. Start the React Frontend
Open a new terminal:
```bash
cd frontend

# Install UI packages
npm install

# Start Vite server
npm run dev
```
- **Frontend UI**: http://localhost:3000

### 3. Default Credentials
Log in with the seeded credentials:
- **Email**: `admin@lithology.ai`
- **Password**: `Admin@123456`

---

## 🧪 Testing

To trigger the automated pytest execution matrix:
```bash
cd backend
python -m pytest ../tests/ -v
```

---

## 📄 License
This project is licensed under the MIT License - see the LICENSE file for details.
