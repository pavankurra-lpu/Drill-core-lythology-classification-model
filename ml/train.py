import os
import argparse
import numpy as np
import tensorflow as tf
from tensorflow.keras import layers, models
from PIL import Image

# List of rock classes
CLASSES = [
    "Granite", "Sandstone", "Limestone", "Basalt", "Shale",
    "Quartzite", "Marble", "Dolomite", "Coal", "Gneiss"
]

def generate_synthetic_data(data_dir, num_samples_per_class=15):
    """
    Generates a synthetic dataset of color images for testing the training pipeline.
    """
    print(f"Generating synthetic dataset in '{data_dir}'...")
    os.makedirs(data_dir, exist_ok=True)
    
    # Define distinct colors for synthetic classes to make them somewhat learnable
    class_colors = {
        "Granite": (150, 150, 150),   # Grey
        "Sandstone": (210, 180, 140), # Tan
        "Limestone": (230, 230, 250), # Off-white
        "Basalt": (30, 30, 30),       # Dark Grey/Black
        "Shale": (90, 80, 80),        # Dark Brown/Grey
        "Quartzite": (240, 248, 255), # White/Alice Blue
        "Marble": (255, 250, 240),    # Floral White
        "Dolomite": (200, 200, 190),  # Light Tan/Grey
        "Coal": (10, 10, 10),         # Charcoal Black
        "Gneiss": (120, 110, 100)     # Banded Grey/Brown
    }
    
    for cls in CLASSES:
        cls_dir = os.path.join(data_dir, cls)
        os.makedirs(cls_dir, exist_ok=True)
        
        base_color = class_colors.get(cls, (128, 128, 128))
        
        for i in range(num_samples_per_class):
            # Create an image with base color and add random patterns/noise
            img_arr = np.zeros((224, 224, 3), dtype=np.uint8)
            img_arr[:, :] = base_color
            
            # Add random noise
            noise = np.random.randint(-20, 20, (224, 224, 3))
            img_arr = np.clip(img_arr.astype(np.int16) + noise, 0, 255).astype(np.uint8)
            
            # Add some stripes or spots to simulate texture
            for _ in range(5):
                x1, y1 = np.random.randint(0, 224, 2)
                x2, y2 = np.random.randint(0, 224, 2)
                draw_color = tuple(np.clip(np.array(base_color) + np.random.randint(-40, 40, 3), 0, 255).tolist())
                # simple drawing
                img = Image.fromarray(img_arr)
                from PIL import ImageDraw
                draw = ImageDraw.Draw(img)
                draw.line([(x1, y1), (x2, y2)], fill=draw_color, width=np.random.randint(2, 10))
                img_arr = np.array(img)
            
            # Save the image
            img = Image.fromarray(img_arr)
            img.save(os.path.join(cls_dir, f"{cls.lower()}_{i}.jpg"))
            
    print("Synthetic dataset generation complete.")

def build_resnet50_model(num_classes=10):
    """
    Builds a Transfer Learning model using ResNet50 as the backbone.
    Embeds preprocessing layers directly in the model.
    """
    # Define inputs (RGB images)
    inputs = layers.Input(shape=(224, 224, 3), name="input_image")
    
    # Preprocessing layer: zero-centers channels using ImageNet mean
    x = layers.Lambda(tf.keras.applications.resnet50.preprocess_input, name="resnet_preprocess")(inputs)
    
    # Data Augmentation Layers (active during training only)
    x = layers.RandomFlip("horizontal_and_vertical", name="random_flip")(x)
    x = layers.RandomRotation(0.2, name="random_rotation")(x)
    x = layers.RandomContrast(0.15, name="random_contrast")(x)
    
    # Load Pretrained ResNet50
    base_model = tf.keras.applications.ResNet50(
        include_top=False, 
        weights='imagenet', 
        input_tensor=x
    )
    
    # Freeze the backbone
    base_model.trainable = False
    
    # Classification Head
    x = base_model.output
    x = layers.GlobalAveragePooling2D(name="avg_pool")(x)
    x = layers.BatchNormalization()(x)
    x = layers.Dense(512, activation='relu', name="dense_fc1")(x)
    x = layers.Dropout(0.3, name="dropout1")(x)
    x = layers.Dense(256, activation='relu', name="dense_fc2")(x)
    x = layers.Dropout(0.2, name="dropout2")(x)
    outputs = layers.Dense(num_classes, activation='softmax', name="predictions")(x)
    
    model = models.Model(inputs=inputs, outputs=outputs, name="Lithology_ResNet50")
    return model

def create_dummy_model(output_path="model.h5"):
    """
    Creates and saves a dummy model instantly for rapid application development and deployment validation.
    Uses the same input/output interfaces.
    """
    print("Building a dummy model structure...")
    inputs = layers.Input(shape=(224, 224, 3), name="input_image")
    x = layers.Lambda(tf.keras.applications.resnet50.preprocess_input, name="resnet_preprocess")(inputs)
    
    # Create a small CNN instead of full ResNet50 to compile instantly and keep model size small
    x = layers.Conv2D(16, (3, 3), activation='relu')(x)
    x = layers.GlobalAveragePooling2D()(x)
    x = layers.Dense(32, activation='relu')(x)
    outputs = layers.Dense(len(CLASSES), activation='softmax', name="predictions")(x)
    
    model = models.Model(inputs=inputs, outputs=outputs)
    model.compile(optimizer='adam', loss='categorical_crossentropy', metrics=['accuracy'])
    
    # Save the model
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    model.save(output_path)
    print(f"Dummy model successfully saved to '{output_path}'. Ready for API loading!")

def train_model(data_dir, epochs=10, batch_size=32, model_save_path="model.h5"):
    """
    Trains the ResNet50 model using the dataset directory.
    """
    if not os.path.exists(data_dir):
        raise ValueError(f"Dataset directory '{data_dir}' not found.")
        
    print(f"Loading dataset from '{data_dir}'...")
    
    # Load training and validation datasets
    train_ds = tf.keras.utils.image_dataset_from_directory(
        data_dir,
        validation_split=0.2,
        subset="training",
        seed=123,
        image_size=(224, 224),
        batch_size=batch_size,
        label_mode="categorical",
        class_names=CLASSES
    )
    
    val_ds = tf.keras.utils.image_dataset_from_directory(
        data_dir,
        validation_split=0.2,
        subset="validation",
        seed=123,
        image_size=(224, 224),
        batch_size=batch_size,
        label_mode="categorical",
        class_names=CLASSES
    )
    
    # Configure dataset for performance
    AUTOTUNE = tf.data.AUTOTUNE
    train_ds = train_ds.prefetch(buffer_size=AUTOTUNE)
    val_ds = val_ds.prefetch(buffer_size=AUTOTUNE)
    
    # Build Model
    model = build_resnet50_model(num_classes=len(CLASSES))
    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=1e-4),
        loss="categorical_crossentropy",
        metrics=["accuracy"]
    )
    
    model.summary()
    
    # Callbacks
    callbacks = [
        tf.keras.callbacks.EarlyStopping(patience=3, restore_best_weights=True),
        tf.keras.callbacks.ModelCheckpoint(model_save_path, save_best_only=True)
    ]
    
    # Train
    print("Starting training...")
    history = model.fit(
        train_ds,
        validation_data=val_ds,
        epochs=epochs,
        callbacks=callbacks
    )
    
    print("Training finished.")
    
    # Evaluate model
    print("Evaluating model...")
    evaluate_metrics(model, val_ds)

def evaluate_metrics(model, val_ds):
    """
    Computes precision, recall, F1-score, and confusion matrix.
    """
    from sklearn.metrics import classification_report, confusion_matrix
    import matplotlib.pyplot as plt
    import seaborn as sns
    
    y_true = []
    y_pred = []
    
    for images, labels in val_ds:
        preds = model.predict(images, verbose=0)
        y_true.extend(np.argmax(labels.numpy(), axis=1))
        y_pred.extend(np.argmax(preds, axis=1))
        
    y_true = np.array(y_true)
    y_pred = np.array(y_pred)
    
    # Classification Report
    report = classification_report(y_true, y_pred, target_names=CLASSES, zero_division=0)
    print("\n--- Classification Report ---")
    print(report)
    
    # Save text report
    with open("classification_report.txt", "w") as f:
        f.write(report)
    print("Saved classification report to 'classification_report.txt'.")
    
    # Confusion Matrix
    cm = confusion_matrix(y_true, y_pred)
    plt.figure(figsize=(10, 8))
    sns.heatmap(cm, annot=True, fmt='d', xticklabels=CLASSES, yticklabels=CLASSES, cmap='Blues')
    plt.title("Confusion Matrix - Lithology Classification")
    plt.ylabel("True Class")
    plt.xlabel("Predicted Class")
    plt.tight_layout()
    plt.savefig("confusion_matrix.png")
    print("Saved confusion matrix plot to 'confusion_matrix.png'.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Drill Core Lithology Model Trainer")
    parser.add_argument("--data_dir", type=str, default="dataset", help="Path to image dataset")
    parser.add_argument("--epochs", type=int, default=10, help="Number of epochs to train")
    parser.add_argument("--batch_size", type=int, default=32, help="Batch size")
    parser.add_argument("--model_path", type=str, default="model.h5", help="Path to save the model.h5 file")
    parser.add_argument("--dummy", action="store_true", help="Generate a dummy model instantly for rapid local launch")
    parser.add_argument("--generate_synthetic", action="store_true", help="Generate synthetic dataset for testing the pipeline")
    
    args = parser.parse_args()
    
    if args.dummy:
        create_dummy_model(args.model_path)
    elif args.generate_synthetic:
        synthetic_dir = "synthetic_dataset"
        generate_synthetic_data(synthetic_dir)
        train_model(synthetic_dir, epochs=args.epochs, batch_size=args.batch_size, model_save_path=args.model_path)
    else:
        if not os.path.exists(args.data_dir):
            print(f"Warning: Dataset directory '{args.data_dir}' not found.")
            print("To generate a dummy model instantly, run: python ml/train.py --dummy")
            print("To generate a synthetic dataset and train a model, run: python ml/train.py --generate_synthetic")
        else:
            train_model(args.data_dir, epochs=args.epochs, batch_size=args.batch_size, model_save_path=args.model_path)
