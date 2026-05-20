"""
Professional ML Training Pipeline for CICIDS2017
Trains RandomForest classifier with proper validation and metrics
"""

import os
import sys
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    confusion_matrix, classification_report, roc_auc_score
)
import warnings
warnings.filterwarnings('ignore')

# Import preprocessing
from preprocess import DatasetPreprocessor


class MLModelTrainer:
    """Professional ML Model Trainer"""
    
    def __init__(self, model_dir='../backend/models'):
        self.model_dir = model_dir
        self.model = None
        self.X_train = None
        self.X_test = None
        self.y_train = None
        self.y_test = None
        self.preprocessor = None
        self.feature_columns = None
        
        os.makedirs(model_dir, exist_ok=True)
    
    def train(self, X, y, preprocessor, feature_columns):
        """Train RandomForest model"""
        print("\n" + "="*60)
        print("TRAINING RANDOM FOREST CLASSIFIER")
        print("="*60 + "\n")
        
        self.preprocessor = preprocessor
        self.feature_columns = feature_columns
        
        # Split data
        print("[*] Splitting data (80/20)...")
        self.X_train, self.X_test, self.y_train, self.y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        print(f"[+] Training set: {len(self.X_train)} samples")
        print(f"[+] Test set: {len(self.X_test)} samples")
        
        # Train model
        print("\n[*] Training RandomForest Classifier...")
        print("    - Trees: 200")
        print("    - Max depth: 20")
        print("    - Min samples split: 5")
        print("    - Min samples leaf: 2")
        print("    - Max features: sqrt")
        
        self.model = RandomForestClassifier(
            n_estimators=200,
            max_depth=20,
            min_samples_split=5,
            min_samples_leaf=2,
            max_features='sqrt',
            random_state=42,
            n_jobs=1,
            verbose=0
        )
        
        self.model.fit(self.X_train, self.y_train)
        print("[+] Training complete!")
    
    def evaluate(self):
        """Evaluate model performance"""
        print("\n" + "="*60)
        print("MODEL EVALUATION")
        print("="*60 + "\n")
        
        # Predictions
        y_train_pred = self.model.predict(self.X_train)
        y_test_pred = self.model.predict(self.X_test)
        y_test_proba = self.model.predict_proba(self.X_test)
        
        # Accuracy
        train_acc = accuracy_score(self.y_train, y_train_pred)
        test_acc = accuracy_score(self.y_test, y_test_pred)
        
        print("[*] ACCURACY METRICS")
        print(f"    Training Accuracy:  {train_acc:.4f} ({train_acc*100:.2f}%)")
        print(f"    Testing Accuracy:   {test_acc:.4f} ({test_acc*100:.2f}%)")
        
        # Precision, Recall, F1
        print("\n[*] DETAILED METRICS")
        precision = precision_score(self.y_test, y_test_pred, average='weighted', zero_division=0)
        recall = recall_score(self.y_test, y_test_pred, average='weighted', zero_division=0)
        f1 = f1_score(self.y_test, y_test_pred, average='weighted', zero_division=0)
        
        print(f"    Precision (weighted): {precision:.4f}")
        print(f"    Recall (weighted):    {recall:.4f}")
        print(f"    F1-Score (weighted):  {f1:.4f}")
        
        # Confusion Matrix
        print("\n[*] CONFUSION MATRIX")
        cm = confusion_matrix(self.y_test, y_test_pred)
        print(cm)
        
        # Classification Report
        print("\n[*] CLASSIFICATION REPORT")
        class_names = self.preprocessor.label_encoder.classes_
        print(classification_report(
            self.y_test, y_test_pred,
            target_names=class_names,
            zero_division=0
        ))
        
        # Feature Importance
        print("\n[*] TOP 10 IMPORTANT FEATURES")
        feature_importance = pd.DataFrame({
            'feature': self.feature_columns,
            'importance': self.model.feature_importances_
        }).sort_values('importance', ascending=False)
        
        for idx, (i, row) in enumerate(feature_importance.head(10).iterrows(), 1):
            print(f"    [{idx}] {row['feature']}: {row['importance']:.4f}")
        
        return {
            'train_accuracy': train_acc,
            'test_accuracy': test_acc,
            'precision': precision,
            'recall': recall,
            'f1': f1,
            'confusion_matrix': cm,
            'feature_importance': feature_importance
        }
    
    def save_model(self):
        """Save model and artifacts"""
        print("\n" + "="*60)
        print("SAVING MODEL")
        print("="*60 + "\n")
        
        # Save model
        model_path = os.path.join(self.model_dir, 'model.pkl')
        joblib.dump(self.model, model_path)
        print(f"[+] Model saved: {model_path}")
        
        # Save scaler
        scaler_path = os.path.join(self.model_dir, 'scaler.pkl')
        joblib.dump(self.preprocessor.scaler, scaler_path)
        print(f"[+] Scaler saved: {scaler_path}")
        
        # Save label encoder
        encoder_path = os.path.join(self.model_dir, 'label_encoder.pkl')
        joblib.dump(self.preprocessor.label_encoder, encoder_path)
        print(f"[+] Label encoder saved: {encoder_path}")
        
        # Save feature columns
        features_path = os.path.join(self.model_dir, 'feature_columns.pkl')
        joblib.dump(self.feature_columns, features_path)
        print(f"[+] Feature columns saved: {features_path}")
        
        print(f"\n[+] All artifacts saved to: {self.model_dir}/")


def main():
    """Main training pipeline"""
    print("\n" + "="*60)
    print("PROFESSIONAL NIDS ML TRAINING PIPELINE")
    print("Using CICIDS2017 Dataset")
    print("="*60 + "\n")
    
    # Step 1: Preprocess data
    print("[*] Step 1: Preprocessing data...")
    preprocessor = DatasetPreprocessor(data_dir='data')
    
    if not preprocessor.load_all_csv_files():
        print("[-] Preprocessing failed!")
        return False
    
    preprocessor.clean_column_names()
    label_col = preprocessor.identify_label_column()
    
    if not label_col:
        print("[-] Could not identify label column!")
        return False
    
    preprocessor.clean_data()
    preprocessor.identify_feature_types(label_col)
    preprocessor.encode_label(label_col)
    preprocessor.normalize_features()
    
    if preprocessor.categorical_features:
        preprocessor.encode_categorical()
    
    X, y, feature_columns = preprocessor.prepare_dataset(target_rows=50000)
    
    # Step 2: Train model
    print("\n[*] Step 2: Training model...")
    trainer = MLModelTrainer()
    trainer.train(X, y, preprocessor, feature_columns)
    
    # Step 3: Evaluate model
    print("\n[*] Step 3: Evaluating model...")
    metrics = trainer.evaluate()
    
    # Step 4: Save model
    print("\n[*] Step 4: Saving artifacts...")
    trainer.save_model()
    
    print("\n" + "="*60)
    print("TRAINING PIPELINE COMPLETE!")
    print("="*60)
    print(f"Model Accuracy: {metrics['test_accuracy']:.2%}")
    print("Ready for production deployment!")
    print("="*60 + "\n")
    
    return True


if __name__ == '__main__':
    try:
        success = main()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n[-] ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    print(f"[+] Scaler saved to {scaler_path}")

    # Create summary
    print("\n" + "="*60)
    print("MODEL TRAINING SUMMARY")
    print("="*60)
    print(f"Model Type: Random Forest Classifier")
    print(f"Number of Trees: {model.n_estimators}")
    print(f"Max Depth: {model.max_depth}")
    print(f"Training Accuracy: {train_score:.2%}")
    print(f"Testing Accuracy: {test_score:.2%}")
    print(f"Training Samples: {X_train.shape[0]}")
    print(f"Testing Samples: {X_test.shape[0]}")
    print(f"Features: {X.shape[1]}")
    print(f"Dataset Balance: 85% Normal, 15% Attack")
    print(f"Completed at: {datetime.now()}")
    print("="*60)

    print("\n[+] Model training completed successfully!")
    print("[*] Ready for deployment in NIDS backend")
