import pandas as pd
import numpy as np
import pickle
import json
import os
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, precision_score, classification_report
import warnings
warnings.filterwarnings('ignore')

DATA_PATH = os.environ.get('DATA_PATH')
if DATA_PATH is None:
    raise ValueError("Environment variable DATA_PATH is not set.")

df = pd.read_csv(DATA_PATH)

feature_cols = ['feature_0', 'feature_1', 'feature_2', 'feature_3', 'feature_4', 'feature_5', 'feature_6']
X = df[feature_cols]
y = df['target']

# Handle missing values
X = X.fillna(X.mean())

# Encode target if needed
if y.dtype == 'object':
    from sklearn.preprocessing import LabelEncoder
    le = LabelEncoder()
    y = le.fit_transform(y)

# Scale features
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# Split
X_train, X_test, y_train, y_test = train_test_split(
    X_scaled, y, test_size=0.2, random_state=42, stratify=y
)

# Train
model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

# Predict
y_pred = model.predict(X_test)

# Evaluate
accuracy = accuracy_score(y_test, y_pred)
precision = precision_score(y_test, y_pred, average='weighted', zero_division=0)

metrics_json = {"accuracy": round(accuracy, 2), "precision": round(precision, 2)}

# Save model
with open('trained_model.pkl', 'wb') as f:
    pickle.dump({'model': model, 'scaler': scaler}, f)

# Print required output
print(f"METRICS_JSON: {json.dumps(metrics_json)}")
print("MODEL_PATH: trained_model.pkl")