
import os
import pickle
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, precision_score, classification_report
from sklearn.pipeline import Pipeline

# Load data
data_path = os.environ.get('DATA_PATH')
df = pd.read_csv(data_path)

X = df.drop('target', axis=1)
y = df['target']

# Train/validation split
X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)

# Build pipeline with scaling and model
pipeline = Pipeline([
    ('scaler', StandardScaler()),
    ('model', RandomForestClassifier(random_state=42))
])

# Hyperparameter tuning
param_grid = {
    'model__n_estimators': [100, 200, 300],
    'model__max_depth': [5, 10, 15, None],
    'model__min_samples_split': [2, 5, 10],
    'model__min_samples_leaf': [1, 2, 4],
    'model__max_features': ['sqrt', 'log2']
}

grid_search = GridSearchCV(
    pipeline,
    param_grid,
    cv=5,
    scoring='accuracy',
    n_jobs=-1,
    verbose=1
)

grid_search.fit(X_train, y_train)

# Best model predictions
y_pred = grid_search.predict(X_val)

# Evaluate
accuracy = accuracy_score(y_val, y_pred)
precision = precision_score(y_val, y_pred, average='weighted', zero_division=0)

print(f"Best params: {grid_search.best_params_}")
print(f"Accuracy: {accuracy:.4f}")
print(f"Precision: {precision:.4f}")
print("Classification Report:")
print(classification_report(y_val, y_pred))

# Save best model
best_model = grid_search.best_estimator_
with open('trained_model.pkl', 'wb') as f:
    pickle.dump(best_model, f)

print(f"METRICS_JSON: {{\"accuracy\": {accuracy:.4f}, \"precision\": {precision:.4f}}}")
print(f"MODEL_PATH: trained_model.pkl")
