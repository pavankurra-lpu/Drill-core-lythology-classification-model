# Automated-Lithology-Classification-System-for-Drill-Core-Samples-Using-Machine-Learning
This project focuses on building an end-to-end Machine Learning system that automatically classifies drill core rock samples into lithology types. It includes image-based models, tabular ML models, a full website interface, flowcharts, and complete deployment-ready files.

\\train_model.py
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, classification_report
import joblib
import os

os.makedirs("models", exist_ok=True)

df = pd.read_csv("data/lithology_data.csv")

X = df.drop("lithology", axis=1)
y = df["lithology"]

label_encoder = LabelEncoder()
y_encoded = label_encoder.fit_transform(y)

scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

X_train, X_test, y_train, y_test = train_test_split(
    X_scaled, y_encoded, test_size=0.2, random_state=42, stratify=y_encoded
)

model = RandomForestClassifier(
    n_estimators=200,
    max_depth=None,
    random_state=42
)
model.fit(X_train, y_train)

y_pred = model.predict(X_test)

acc = accuracy_score(y_test, y_pred)
prec = precision_score(y_test, y_pred, average="weighted", zero_division=0)
rec = recall_score(y_test, y_pred, average="weighted", zero_division=0)

print("Accuracy:", acc)
print("Precision:", prec)
print("Recall:", rec)
print("\nClassification Report:\n")
print(classification_report(y_test, y_pred, zero_division=0, target_names=label_encoder.classes_))

joblib.dump(model, "models/rf_model.joblib")
joblib.dump(scaler, "models/scaler.joblib")
joblib.dump(label_encoder, "models/label_encoder.joblib")

print("\nSaved model, scaler and label encoder in 'models/' folder.")

\\app.py
from flask import Flask, render_template, request, jsonify
import numpy as np
import joblib
import os

app = Flask(__name__)

model = joblib.load("models/rf_model.joblib")
scaler = joblib.load("models/scaler.joblib")
label_encoder = joblib.load("models/label_encoder.joblib")

feature_names = None


@app.before_first_request
def set_feature_names():
    global feature_names
    if feature_names is None:
        feature_names = ["feature1", "feature2", "feature3", "feature4"]


@app.route("/")
def index():
    return render_template("index.html", feature_names=feature_names)


@app.route("/predict", methods=["POST"])
def predict():
    data = request.get_json()
    values = [data.get(name, 0) for name in feature_names]
    values = np.array(values).reshape(1, -1)
    values_scaled = scaler.transform(values)
    pred_encoded = model.predict(values_scaled)[0]
    pred_label = label_encoder.inverse_transform([pred_encoded])[0]
    return jsonify({"prediction": pred_label})


if __name__ == "__main__":
    app.run(debug=True)
    
\\templates/index.html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Drill Core Lithology Classification</title>
    <link rel="stylesheet" href="{{ url_for('static', filename='style.css') }}">
</head>
<body>
<div class="container">
    <h1>🪨 Drill Core Lithology Classification</h1>
    <p class="subtitle">Enter drill core features to predict the lithology type.</p>

    <form id="predict-form">
        <div class="form-grid">
            {% for f in feature_names %}
            <div class="form-group">
                <label for="{{ f }}">{{ f | capitalize }}</label>
                <input type="number" step="any" id="{{ f }}" name="{{ f }}" required>
            </div>
            {% endfor %}
        </div>
        <button type="submit" class="btn">Predict Lithology</button>
    </form>

    <div id="result" class="result-card hidden">
        <h2>Prediction Result</h2>
        <p id="prediction-text"></p>
    </div>

    <section class="history-section">
        <h2>Prediction History</h2>
        <div id="history-list" class="history-list">
            <p class="empty-history">No predictions yet. Make your first prediction!</p>
        </div>
        <button id="clear-history" class="btn secondary">Clear History</button>
    </section>
</div>

<script>
    const featureNames = {{ feature_names | tojson }};
</script>
<script src="{{ url_for('static', filename='script.js') }}"></script>
</body>
</html>

\\static/style.css
* {
    box-sizing: border-box;
    margin: 0;
    padding: 0;
    font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}

body {
    background: #0f172a;
    color: #e5e7eb;
    display: flex;
    justify-content: center;
    align-items: flex-start;
    min-height: 100vh;
    padding: 40px 16px;
}

.container {
    width: 100%;
    max-width: 900px;
    background: #020617;
    border-radius: 20px;
    padding: 24px 24px 32px;
    box-shadow: 0 20px 40px rgba(0, 0, 0, 0.6);
    border: 1px solid #1f2937;
}

h1 {
    font-size: 28px;
    margin-bottom: 8px;
    color: #f9fafb;
}

.subtitle {
    color: #9ca3af;
    margin-bottom: 20px;
}

.form-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
    gap: 16px;
    margin-bottom: 16px;
}

.form-group {
    display: flex;
    flex-direction: column;
    gap: 6px;
}

label {
    font-size: 14px;
    color: #d1d5db;
}

input[type="number"] {
    padding: 8px 10px;
    border-radius: 10px;
    border: 1px solid #374151;
    background: #020617;
    color: #e5e7eb;
    outline: none;
}

input[type="number"]:focus {
    border-color: #3b82f6;
}

.btn {
    margin-top: 12px;
    padding: 10px 18px;
    border-radius: 999px;
    border: none;
    cursor: pointer;
    font-size: 14px;
    font-weight: 500;
    background: linear-gradient(135deg, #3b82f6, #06b6d4);
    color: white;
    transition: transform 0.1s ease, box-shadow 0.1s ease, opacity 0.2s ease;
}

.btn:hover {
    transform: translateY(-1px);
    box-shadow: 0 10px 20px rgba(59, 130, 246, 0.4);
}

.btn:active {
    transform: translateY(0);
    box-shadow: none;
}

.btn.secondary {
    background: transparent;
    border: 1px solid #4b5563;
    color: #e5e7eb;
    margin-top: 10px;
}

.result-card {
    margin-top: 20px;
    padding: 16px;
    border-radius: 16px;
    background: radial-gradient(circle at top left, #1d4ed8, #020617);
    border: 1px solid #1f2937;
}

.result-card h2 {
    margin-bottom: 8px;
    font-size: 18px;
}

#prediction-text {
    font-size: 16px;
    font-weight: 500;
    color: #e5e7eb;
}

.hidden {
    display: none;
}

.history-section {
    margin-top: 24px;
}

.history-section h2 {
    font-size: 18px;
    margin-bottom: 10px;
}

.history-list {
    border-radius: 14px;
    border: 1px solid #1f2937;
    padding: 10px;
    background: #020617;
    max-height: 260px;
    overflow-y: auto;
}

.history-item {
    padding: 8px 10px;
    border-radius: 10px;
    border: 1px solid #111827;
    background: #020617;
    margin-bottom: 8px;
    font-size: 13px;
}

.history-item-header {
    display: flex;
    justify-content: space-between;
    margin-bottom: 4px;
    color: #9ca3af;
}

.history-item-body {
    color: #e5e7eb;
}

.history-item strong {
    color: #93c5fd;
}

.empty-history {
    font-size: 14px;
    color: #6b7280;
}


\\static/script.js
const form = document.getElementById("predict-form");
const resultDiv = document.getElementById("result");
const predictionText = document.getElementById("prediction-text");
const historyList = document.getElementById("history-list");
const clearHistoryBtn = document.getElementById("clear-history");

function loadHistory() {
    const history = JSON.parse(localStorage.getItem("lithology_history") || "[]");
    historyList.innerHTML = "";
    if (history.length === 0) {
        const p = document.createElement("p");
        p.className = "empty-history";
        p.textContent = "No predictions yet. Make your first prediction!";
        historyList.appendChild(p);
        return;
    }
    history.forEach(item => {
        const div = document.createElement("div");
        div.className = "history-item";

        const header = document.createElement("div");
        header.className = "history-item-header";
        const timeSpan = document.createElement("span");
        timeSpan.textContent = new Date(item.timestamp).toLocaleString();
        const predSpan = document.createElement("span");
        predSpan.textContent = item.prediction;
        header.appendChild(timeSpan);
        header.appendChild(predSpan);

        const body = document.createElement("div");
        body.className = "history-item-body";
        body.textContent = featureNames.map(name => `${name}: ${item.inputs[name]}`).join(" | ");

        div.appendChild(header);
        div.appendChild(body);
        historyList.appendChild(div);
    });
}

function saveToHistory(inputs, prediction) {
    const history = JSON.parse(localStorage.getItem("lithology_history") || "[]");
    history.unshift({
        timestamp: Date.now(),
        inputs,
        prediction
    });
    if (history.length > 50) {
        history.pop();
    }
    localStorage.setItem("lithology_history", JSON.stringify(history));
    loadHistory();
}

form.addEventListener("submit", async (e) => {
    e.preventDefault();

    const inputs = {};
    featureNames.forEach(name => {
        const value = parseFloat(document.getElementById(name).value);
        inputs[name] = isNaN(value) ? 0 : value;
    });

    try {
        const res = await fetch("/predict", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(inputs)
        });

        const data = await res.json();
        const prediction = data.prediction;

        predictionText.textContent = `Predicted Lithology: ${prediction}`;
        resultDiv.classList.remove("hidden");

        saveToHistory(inputs, prediction);
    } catch (err) {
        predictionText.textContent = "Error while predicting. Check console.";
        console.error(err);
        resultDiv.classList.remove("hidden");
    }
});

clearHistoryBtn.addEventListener("click", () => {
    localStorage.removeItem("lithology_history");
    loadHistory();
});

loadHistory();

