# Use official lightweight Python image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy and install requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Generate the model during build so the space starts successfully
RUN python ml/train.py --dummy

# Expose port 7860 (Hugging Face Spaces default port)
EXPOSE 7860

# Run the FastAPI server
CMD ["uvicorn", "backend.app:app", "--host", "0.0.0.0", "--port", "7860"]
