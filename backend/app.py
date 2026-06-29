import os
import io
import numpy as np
import tensorflow as tf
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from PIL import Image

app = FastAPI(
    title="Drill Core Lithology Classification System",
    description="FastAPI Backend for predicting drill core rock types",
    version="1.0.0"
)

# Enable CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

CLASSES = [
    "Granite", "Sandstone", "Limestone", "Basalt", "Shale",
    "Quartzite", "Marble", "Dolomite", "Coal", "Gneiss"
]

DESCRIPTIONS = {
    "Granite": "An intrusive igneous rock with a coarse-grained texture, primarily composed of quartz, feldspar, and mica. It forms from the slow crystallization of magma below Earth's surface.",
    "Sandstone": "A clastic sedimentary rock composed mainly of sand-sized mineral particles or rock fragments (mostly quartz). It often displays prominent bedding layers and is highly porous.",
    "Limestone": "A sedimentary rock composed primarily of calcium carbonate (calcite or aragonite). It frequently forms in shallow, warm marine waters and often contains marine fossils.",
    "Basalt": "An extrusive igneous rock formed from the rapid cooling of low-viscosity lava rich in magnesium and iron. It is dark-colored, fine-grained, and forms most of the oceanic crust.",
    "Shale": "A fine-grained, clastic sedimentary rock composed of mud that is a mix of clay minerals and tiny fragments of quartz and calcite. It is characterized by thin laminae or parallel layering.",
    "Quartzite": "A non-foliated metamorphic rock composed almost entirely of quartz. It forms when a quartz-rich sandstone is subjected to high heat and pressure.",
    "Marble": "A metamorphic rock composed of recrystallized carbonate minerals, most commonly calcite or dolomite. It forms when limestone is subjected to metamorphism, resulting in a crystalline texture.",
    "Dolomite": "A sedimentary carbonate rock that contains a high percentage of the mineral dolomite, calcium magnesium carbonate. Similar to limestone but harder and less reactive to acid.",
    "Coal": "A combustible black or brownish-black sedimentary rock formed as rock strata called coal seams. It is composed mostly of carbon, along with variable quantities of other elements like hydrogen, sulfur, oxygen, and nitrogen.",
    "Gneiss": "A high-grade metamorphic rock characterized by distinct banding, which is caused by the segregation of light (quartz, feldspar) and dark (biotite, amphibole) minerals under intense heat and pressure."
}

# Global variable for the model
model = None

@app.on_event("startup")
def load_model():
    global model
    # Model is stored in the workspace root directory
    model_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "model.h5")
    if os.path.exists(model_path):
        print(f"Loading TensorFlow model from '{model_path}'...")
        try:
            # Register preprocess_input as a custom object for Keras deserialization
            model = tf.keras.models.load_model(
                model_path,
                custom_objects={'preprocess_input': tf.keras.applications.resnet50.preprocess_input}
            )
            print("Model loaded successfully!")
        except Exception as e:
            print(f"Failed to load model: {e}")
    else:
        print(f"Warning: Model file not found at '{model_path}'. Inference will not work until a model is trained or generated.")

@app.get("/api/health")
def health_check():
    """Health check endpoint to verify backend status."""
    return {
        "status": "healthy",
        "model_loaded": model is not None,
        "classes_supported": len(CLASSES)
    }

@app.post("/api/predict")
async def predict(file: UploadFile = File(...)):
    """
    Accepts an uploaded image, processes it, and returns the top predicted rock types.
    """
    global model
    if model is None:
        # Re-check if model.h5 became available
        model_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "model.h5")
        if os.path.exists(model_path):
            try:
                model = tf.keras.models.load_model(
                    model_path,
                    custom_objects={'preprocess_input': tf.keras.applications.resnet50.preprocess_input}
                )
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Model exists but could not be loaded: {e}")
        else:
            raise HTTPException(status_code=503, detail="Model not loaded. Please generate/train the model first.")

    # Validate file extension
    allowed_extensions = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in allowed_extensions:
        raise HTTPException(status_code=400, detail=f"Unsupported file format. Allowed formats: {', '.join(allowed_extensions)}")

    try:
        # Read file content
        contents = await file.read()
        image = Image.open(io.BytesIO(contents)).convert("RGB")
        
        # Resize image to match model input shape (224, 224)
        resized_image = image.resize((224, 224))
        
        # Convert to numpy array and add batch dimension
        img_array = np.array(resized_image, dtype=np.float32)
        img_array = np.expand_dims(img_array, axis=0) # Shape: (1, 224, 224, 3)
        
        # Run inference
        # Model has built-in ResNet50 preprocess_input layer, so raw pixel values [0, 255] are expected
        predictions = model.predict(img_array, verbose=0)[0]
        
        # Extract top 3 indices and probabilities
        top_indices = np.argsort(predictions)[::-1][:3]
        
        top_3 = []
        for idx in top_indices:
            top_3.append({
                "class": CLASSES[idx],
                "probability": round(float(predictions[idx]), 4)
            })
            
        predicted_class = CLASSES[top_indices[0]]
        confidence = round(float(predictions[top_indices[0]]), 4)
        
        return {
            "predicted_class": predicted_class,
            "confidence": confidence,
            "top_3": top_3,
            "description": DESCRIPTIONS.get(predicted_class, "No description available for this lithology.")
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing image: {str(e)}")

# Mount the static frontend files
# Make sure the frontend directory exists
frontend_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend")
if os.path.exists(frontend_dir):
    app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="static")
else:
    print(f"Warning: Frontend directory not found at '{frontend_dir}'. Running in API-only mode.")
