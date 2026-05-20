# NIDS Machine Learning - Model Training Guide

## Overview
This directory contains the machine learning components for NIDS.

## Files

- `train_model.py` - Main model training script
- `data/` - Training data directory

## Quick Start

### Train Model
```bash
cd ml
python train_model.py
```

This will:
1. Generate synthetic training dataset (5000 samples)
2. Create 85% normal traffic, 15% attack traffic
3. Train Random Forest classifier
4. Evaluate accuracy
5. Save model to `../backend/models/nids_model.pkl`
6. Save scaler to `../backend/models/scaler.pkl`

### Expected Output
```
[*] NIDS ML Model Training Script
[*] Real-Time Network Intrusion Detection System
[*] Training started at 2026-05-15 10:30:00.000000

[*] Generating synthetic dataset...
[+] Dataset created with 5000 samples
[+] Features: 8
[+] Normal samples: 4250
[+] Attack samples: 750

[*] Training Random Forest classifier...
[+] Model trained with 100 trees
[+] Training accuracy: 0.9524
[+] Testing accuracy: 0.9204

[*] Feature Importance:
  Packet_Rate          : 0.2845
  Byte_Rate            : 0.2134
  Duration             : 0.1567
  ...

[+] Model saved to ../backend/models/nids_model.pkl
[+] Model training completed successfully!
```

## Model Architecture

### Algorithm: Random Forest Classifier
- **Trees**: 100
- **Max Depth**: 15
- **Min Samples Split**: 10
- **Min Samples Leaf**: 4
- **Random State**: 42

### Input Features (8)
1. **Protocol** - TCP (1), UDP (2), ICMP (3)
2. **Packet Size** - Bytes (64-1500 normalized)
3. **Source Port** - Port number (1024-65535)
4. **Destination Port** - Well-known/ephemeral
5. **Packet Rate** - Packets per second (0.1-100)
6. **Byte Rate** - Bytes per second (100-1000000)
7. **Flags** - TCP flags (0-64)
8. **Duration** - Flow duration in seconds

### Output
- **Binary Classification**: Normal (0) or Attack (1)
- **Confidence Score**: 0-1 probability

### Training Data
- **Dataset Size**: 5000 samples
- **Train/Test Split**: 80/20
- **Class Distribution**: 85% Normal, 15% Attack
- **Scaling**: StandardScaler normalization

## Performance Metrics

### Expected Accuracy
- Training Accuracy: ~95%
- Testing Accuracy: ~92%
- Precision: ~94%
- Recall: ~90%

### Attack Detection
Trained to detect:
- DoS Attacks (Denial of Service)
- Port Scans
- Brute Force Attempts
- Suspicious Traffic Patterns
- Network Anomalies

## Using the Trained Model

### In Backend
```python
from utils.predictor import Predictor

# Initialize predictor
predictor = Predictor()
predictor.load_model()

# Make prediction
features = {
    'protocol': 'TCP',
    'packet_size': 512,
    'source_port': 12345,
    'dest_port': 80,
    'packet_rate': 10.5,
    'byte_rate': 5000,
}

result = predictor.predict(features)
print(result)  
# Output: {
#   'is_attack': False,
#   'confidence': 0.92,
#   'attack_probability': 0.08,
#   'normal_probability': 0.92
# }
```

## Improving Model Accuracy

### Collect Real Data
Replace synthetic data with real CICIDS2017 dataset:
```bash
# Download from:
# https://www.unb.ca/cic/datasets/ids-2017.html
```

### Feature Engineering
Add more relevant features:
- Flow duration
- Flow rate
- Network segment indicators
- Temporal features
- Entropy calculations

### Hyperparameter Tuning
```python
# Use GridSearchCV
from sklearn.model_selection import GridSearchCV

param_grid = {
    'n_estimators': [50, 100, 200],
    'max_depth': [10, 15, 20],
    'min_samples_split': [5, 10, 15],
}

grid_search = GridSearchCV(model, param_grid, cv=5)
grid_search.fit(X_train, y_train)
best_model = grid_search.best_estimator_
```

### Advanced Models
Try other algorithms:
- XGBoost
- LightGBM
- Neural Networks (TensorFlow/PyTorch)
- Isolation Forest (Anomaly Detection)
- One-Class SVM

## Dataset Format

If using custom CSV dataset:

```csv
protocol,packet_size,source_port,dest_port,packet_rate,byte_rate,flags,duration,label
1,128,1024,80,10.5,5000,2,0.5,0
2,256,2048,443,20.1,10000,18,1.2,0
3,512,3072,22,50.5,25000,4,0.2,1
```

Update `train_model.py` to load custom data:
```python
df = pd.read_csv('data/custom_dataset.csv')
X = df.drop('label', axis=1).values
y = df['label'].values
```

## Model Persistence

### Saving Model
```python
import pickle
with open('models/nids_model.pkl', 'wb') as f:
    pickle.dump(model, f)
```

### Loading Model
```python
import pickle
with open('models/nids_model.pkl', 'rb') as f:
    model = pickle.load(f)
```

## Retraining

To retrain with new data:
1. Collect more packet samples
2. Update `train_model.py` to load new data
3. Run: `python train_model.py`
4. Model will be overwritten automatically
5. Restart backend to use new model

## Monitoring Model

Track model performance over time:
```python
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    roc_auc_score,
    precision_recall_curve
)

# Print detailed metrics
print(classification_report(y_test, y_pred))
print(confusion_matrix(y_test, y_pred))
print(f"AUC-ROC: {roc_auc_score(y_test, y_pred_proba)}")
```

## Dependencies

Required Python packages:
- numpy
- pandas
- scikit-learn
- joblib

Install with:
```bash
pip install -r ../backend/requirements.txt
```

## Troubleshooting

### ImportError: No module named 'sklearn'
```bash
pip install scikit-learn
```

### Model file not found
Make sure models directory exists:
```bash
mkdir -p ../backend/models
```

### Low accuracy
1. Check data quality
2. Increase training samples
3. Tune hyperparameters
4. Try different algorithms
5. Add more features

## References

- Scikit-learn Documentation: https://scikit-learn.org/
- Random Forest Classifier: https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.RandomForestClassifier.html
- CICIDS2017 Dataset: https://www.unb.ca/cic/datasets/ids-2017.html
- IDS Review: https://www.hindawi.com/journals/scn/2016/4531947/
