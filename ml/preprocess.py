"""
CICIDS2017 Dataset Preprocessing Pipeline
Loads, cleans, and prepares network traffic data for ML training
"""

import os
import pandas as pd
import numpy as np
from sklearn.preprocessing import LabelEncoder, StandardScaler
import warnings
warnings.filterwarnings('ignore')


class DatasetPreprocessor:
    """Professional dataset preprocessing for CICIDS2017"""

    def __init__(self, data_dir='data'):
        self.data_dir = data_dir
        self.df = None
        self.scaler = StandardScaler()
        self.label_encoder = LabelEncoder()
        self.numeric_features = []
        self.categorical_features = []
        
    def load_all_csv_files(self):
        """Load and merge all CSV files from data directory"""
        print("[*] Loading CICIDS2017 dataset...")
        
        csv_files = [f for f in os.listdir(self.data_dir) if f.endswith('.csv')]
        
        if not csv_files:
            print("[-] No CSV files found in data directory!")
            return False
        
        print(f"[+] Found {len(csv_files)} CSV files")
        
        dataframes = []
        for i, file in enumerate(csv_files, 1):
            filepath = os.path.join(self.data_dir, file)
            try:
                print(f"[*] Loading ({i}/{len(csv_files)}): {file}...", end=' ')
                
                # Read with error handling for large files
                df = pd.read_csv(filepath, low_memory=False)
                dataframes.append(df)
                print(f"✓ ({len(df)} rows)")
                
            except Exception as e:
                print(f"✗ Error: {str(e)}")
                continue
        
        if not dataframes:
            print("[-] Failed to load any CSV files!")
            return False
        
        # Merge all dataframes
        print("[*] Merging datasets...")
        self.df = pd.concat(dataframes, ignore_index=True, sort=False)
        print(f"[+] Total dataset size: {len(self.df)} rows × {len(self.df.columns)} columns")
        
        return True
    
    def identify_label_column(self):
        """Identify the label column (attack type)"""
        possible_labels = ['Label', 'label', 'Class', 'class', 'Attack', 'attack']
        
        for col in possible_labels:
            if col in self.df.columns:
                print(f"[+] Found label column: '{col}'")
                return col
        
        # If not found, look for columns with few unique values
        for col in self.df.columns:
            if self.df[col].nunique() < 20:
                print(f"[*] Assuming label column: '{col}' ({self.df[col].nunique()} unique values)")
                return col
        
        print("[-] Could not identify label column!")
        return None
    
    def clean_data(self):
        """Remove NaN, Infinity, and duplicate values"""
        print("[*] Cleaning data...")
        
        initial_rows = len(self.df)
        
        # Remove rows with NaN values
        self.df = self.df.dropna()
        print(f"    [-] Removed NaN rows: {initial_rows - len(self.df)}")
        
        # Replace infinite values
        print(f"    [-] Replacing Infinity values...")
        for col in self.df.select_dtypes(include=[np.number]).columns:
            self.df[col] = self.df[col].replace([np.inf, -np.inf], np.nan)
        
        self.df = self.df.dropna()
        
        # Remove duplicates
        initial_rows = len(self.df)
        self.df = self.df.drop_duplicates()
        print(f"    [-] Removed duplicate rows: {initial_rows - len(self.df)}")
        
        print(f"[+] Cleaned dataset: {len(self.df)} rows remaining")
    
    def clean_column_names(self):
        """Standardize column names"""
        print("[*] Cleaning column names...")
        
        # Remove spaces and special characters
        self.df.columns = self.df.columns.str.strip()
        self.df.columns = self.df.columns.str.replace(' ', '_')
        self.df.columns = self.df.columns.str.lower()
        
        print(f"[+] Column names cleaned")
    
    def identify_feature_types(self, label_col):
        """Identify numeric and categorical features"""
        print("[*] Identifying feature types...")
        
        for col in self.df.columns:
            if col == label_col:
                continue
            
            if self.df[col].dtype in ['float64', 'int64']:
                self.numeric_features.append(col)
            else:
                # Try to convert to numeric
                try:
                    pd.to_numeric(self.df[col], errors='coerce')
                    self.numeric_features.append(col)
                except:
                    self.categorical_features.append(col)
        
        print(f"[+] Numeric features: {len(self.numeric_features)}")
        print(f"[+] Categorical features: {len(self.categorical_features)}")
        
        return self.numeric_features, self.categorical_features
    
    def encode_label(self, label_col):
        """Encode attack labels"""
        print(f"[*] Encoding labels from column: '{label_col}'")
        
        # Show attack categories
        unique_labels = self.df[label_col].unique()
        print(f"[+] Attack categories found: {len(unique_labels)}")
        for i, label in enumerate(sorted(unique_labels)):
            print(f"    [{i}] {label}")
        
        # Encode labels
        self.df['label_encoded'] = self.label_encoder.fit_transform(self.df[label_col])
        
        # Store mapping
        label_mapping = dict(zip(
            self.label_encoder.classes_,
            self.label_encoder.transform(self.label_encoder.classes_)
        ))
        print(f"[+] Labels encoded: {label_mapping}")
        
        return self.df['label_encoded']
    
    def normalize_features(self, selected_features=None):
        """
        Normalize ONLY selected realtime-compatible features
        using StandardScaler.
        """

        print("[*] Normalizing numeric features...")

        # Use selected features only
        if selected_features:
            features_to_scale = selected_features
        else:
            features_to_scale = self.numeric_features

        X = self.df.loc[:,features_to_scale].copy()

        # Handle NaN / Inf
        X = X.fillna(X.mean())
        X = X.replace([np.inf, -np.inf], 0)

        # Fit scaler ONLY on selected features
        X_scaled = self.scaler.fit_transform(X)

        # Update dataframe
        self.df[features_to_scale] = X_scaled

        print(f"[+] {len(features_to_scale)} features normalized")
        print(f"    Feature mean: {X_scaled.mean():.6f}")
        print(f"    Feature std:  {X_scaled.std():.6f}")
    
    def encode_categorical(self):
        """Encode categorical features"""
        print("[*] Encoding categorical features...")
        
        for col in self.categorical_features:
            unique_vals = self.df[col].nunique()
            
            if unique_vals > 2:
                # One-hot encode
                dummies = pd.get_dummies(self.df[col], prefix=col)
                self.df = pd.concat([self.df, dummies], axis=1)
                self.df.drop(col, axis=1, inplace=True)
                print(f"    [+] One-hot encoded '{col}' ({unique_vals} values)")
            else:
                # Label encode binary
                le = LabelEncoder()
                self.df[col] = le.fit_transform(self.df[col])
                print(f"    [+] Label encoded '{col}'")
    
    def prepare_dataset(self, target_rows=None, test_size=0.2):
        """
        Prepare final dataset for training
        
        Args:
            target_rows: If set, intelligently sample rows (for faster training on huge datasets)
            test_size: Fraction of data to use for testing
        """
        print("[*] Preparing final dataset...")
        
        # Intelligent sampling for large datasets
        if target_rows and len(self.df) > target_rows:
            print(f"[*] Dataset too large ({len(self.df)} rows), sampling {target_rows} rows...")
            
            # Sample balanced classes
            sampled_dfs = []
            for label in self.df['label_encoded'].unique():
                class_df = self.df[self.df['label_encoded'] == label]
                class_size = int(target_rows / self.df['label_encoded'].nunique())
                
                if len(class_df) > class_size:
                    class_df = class_df.sample(n=class_size, random_state=42)
                
                sampled_dfs.append(class_df)
            
            self.df = pd.concat(sampled_dfs, ignore_index=True)
            print(f"[+] Sampled dataset: {len(self.df)} rows")
        
 # ============================================================
# FLOW-BASED CICIDS FEATURE SELECTION
# Must EXACTLY match realtime feature_extractor.py
# ============================================================

        selected_features = [
            'destination_port',
            'flow_duration',
            'total_fwd_packets',
            'total_backward_packets',
            'total_length_of_fwd_packets',
            'total_length_of_bwd_packets',
            'fwd_packet_length_max',
            'fwd_packet_length_min',
            'fwd_packet_length_mean',
            'bwd_packet_length_max',
            'bwd_packet_length_min',
            'bwd_packet_length_mean',
            'flow_bytes/s',
            'flow_packets/s',
            'flow_iat_mean',
            'flow_iat_std',
            'fwd_iat_mean',
            'bwd_iat_mean',
            'fin_flag_count',
            'syn_flag_count',
            'rst_flag_count',
            'psh_flag_count',
            'ack_flag_count',
            'urg_flag_count',
            'average_packet_size',
            'packet_length_variance',
            'idle_mean',
            'active_mean'
        ]

        # Normalize ONLY selected realtime features
        self.normalize_features(selected_features)

        # Keep only existing columns
        available_features = [
            col for col in selected_features
            if col in self.df.columns
        ]

        missing_features = [
            col for col in selected_features
            if col not in self.df.columns
        ]

        if missing_features:
            print("[!] Missing realtime-compatible features:")
            for feature in missing_features:
                print(f"    - {feature}")

        print(f"[+] Using {len(available_features)} realtime-compatible features")

        # Feature matrix
        X = self.df[available_features].copy()

        # Labels
        y = self.df['label_encoded'].copy()

        # Save exact feature order
        feature_columns = available_features
        
        print(f"[+] Features: {len(X.columns)}")
        print(f"[+] Samples: {len(X)}")
        
        # Print class distribution
        print("[+] Class distribution:")
        class_counts = y.value_counts().sort_index()
        for label_idx, count in class_counts.items():
            label_name = self.label_encoder.inverse_transform([label_idx])[0]
            percentage = (count / len(y)) * 100
            print(f"    [{label_idx}] {label_name}: {count} ({percentage:.2f}%)")
        
        return X, y, feature_columns
    
    def save_artifacts(self, scaler=None, label_encoder=None, feature_columns=None):
        """Save preprocessing artifacts"""
        import joblib
        
        artifacts_dir = 'artifacts'
        os.makedirs(artifacts_dir, exist_ok=True)
        
        if scaler:
            joblib.dump(scaler, os.path.join(artifacts_dir, 'scaler.pkl'))
            print(f"[+] Saved scaler to {artifacts_dir}/scaler.pkl")
        
        if label_encoder:
            joblib.dump(label_encoder, os.path.join(artifacts_dir, 'label_encoder.pkl'))
            print(f"[+] Saved label encoder to {artifacts_dir}/label_encoder.pkl")
        
        if feature_columns:
            joblib.dump(feature_columns, os.path.join(artifacts_dir, 'feature_columns.pkl'))
            print(f"[+] Saved feature columns to {artifacts_dir}/feature_columns.pkl")


def main():
    """Main preprocessing pipeline"""
    print("\n" + "="*60)
    print("CICIDS2017 DATASET PREPROCESSING")
    print("="*60 + "\n")
    
    # Initialize preprocessor
    preprocessor = DatasetPreprocessor(data_dir='data')
    
    # Step 1: Load data
    if not preprocessor.load_all_csv_files():
        return
    
    # Step 2: Clean columns
    preprocessor.clean_column_names()
    
    # Step 3: Find label column
    label_col = preprocessor.identify_label_column()
    if not label_col:
        return
    
    # Step 4: Clean data
    preprocessor.clean_data()
    
    # Step 5: Identify features
    preprocessor.identify_feature_types(label_col)
    
    # Step 6: Encode labels
    preprocessor.encode_label(label_col)
    
    # Step 8: Encode categorical features
    if preprocessor.categorical_features:
        preprocessor.encode_categorical()
    
    # Step 9: Prepare dataset
    # Using 50,000 samples for faster training (remove this limit for production)
    X, y, feature_columns = preprocessor.prepare_dataset(target_rows=50000, test_size=0.2)
    
    print("\n" + "="*60)
    print("PREPROCESSING COMPLETE!")
    print("="*60)
    print(f"Features: {len(feature_columns)}")
    print(f"Samples: {len(X)}")
    print(f"Classes: {len(preprocessor.label_encoder.classes_)}")
    print("="*60 + "\n")
    
    return X, y, preprocessor, feature_columns


if __name__ == '__main__':
    main()
