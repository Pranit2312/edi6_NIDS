"""
Professional ML Predictor with Hybrid Detection
Uses trained RandomForest model + rule-based fallback
"""

import joblib
import numpy as np
import pandas as pd
import os
import logging
from typing import Dict, Optional, Tuple
from .feature_extractor import FeatureExtractor
from .rule_engine import RuleBasedDetector, DetectionResult

logger = logging.getLogger(__name__)


class MLPredictor:
    """
    Professional ML predictor for network intrusion detection.
    Handles model loading, prediction, and confidence scoring.
    """
    
    def __init__(self, model_dir: str = 'models'):
        self.model_dir = model_dir
        self.model = None
        self.scaler = None
        self.label_encoder = None
        self.feature_columns = None
        self.rule_detector = RuleBasedDetector(ml_confidence_threshold=0.7)
        self.loaded = False
    
    def load_model(self) -> bool:
        """
        Load trained ML artifacts.
        
        Returns:
            True if loaded successfully, False otherwise
        """
        try:
            model_path = os.path.join(self.model_dir, 'model.pkl')
            scaler_path = os.path.join(self.model_dir, 'scaler.pkl')
            encoder_path = os.path.join(self.model_dir, 'label_encoder.pkl')
            features_path = os.path.join(self.model_dir, 'feature_columns.pkl')
            
            if not all(os.path.exists(p) for p in [model_path, scaler_path, encoder_path]):
                logger.warning("ML model artifacts not found. Using mock prediction.")
                return False
            
            # Load artifacts
            self.model = joblib.load(model_path)
            self.scaler = joblib.load(scaler_path)
            self.label_encoder = joblib.load(encoder_path)
            self.feature_columns = joblib.load(features_path) if os.path.exists(features_path) else None
            
            logger.info(f"ML model loaded from {self.model_dir}")
            self.loaded = True
            return True
            
        except Exception as e:
            logger.error(f"Error loading ML model: {e}")
            return False
    
    def predict_single(self, packet_data: Dict) -> Dict:
        """
        Predict attack on single packet.
        
        Args:
            packet_data: Packet information dictionary
            
        Returns:
            Prediction result dictionary
        """
        try:
            # Extract features
            flow_packets = packet_data.get('flow_packets', [])

            # If flow packets not available, fallback
            if not flow_packets:
                flow_packets = [packet_data]

            features, _ = FeatureExtractor.extract_flow_features(flow_packets)
            
            # Normalize features
            if self.scaler:
                feature_df = pd.DataFrame(
                    [features],
                    columns=self.feature_columns
                )

                features_normalized = self.scaler.transform(feature_df)[0]
            else:
                features_normalized = FeatureExtractor.normalize_features(features)
            
            if not self.loaded or self.model is None:
                # Mock prediction if model not loaded
                return self._mock_predict(packet_data, features)
            
            # Get ML prediction
            normalized_df = pd.DataFrame(
                [features_normalized],
                columns=self.feature_columns
            )

            prediction = self.model.predict(normalized_df)[0]
            probabilities = self.model.predict_proba(normalized_df)[0]
            
            # Get confidence
            confidence = np.max(probabilities)
            
            # Decode label
            if self.label_encoder:
                attack_type = self.label_encoder.inverse_transform([int(prediction)])[0]
            else:
                attack_type = 'Attack' if prediction == 1 else 'Normal'
            
            is_attack = prediction != 0
            
            # Use rule engine for low confidence
            ml_result = {
                'is_attack': is_attack,
                'attack_type': attack_type,
                'confidence': float(confidence),
                'probabilities': probabilities.tolist() if len(probabilities) > 1 else [1 - confidence, confidence]
            }
            
            # Apply hybrid detection
            hybrid_result = self.rule_detector.detect(packet_data, ml_result)
            
            return {
                'is_attack': hybrid_result.is_attack,
                'attack_type': hybrid_result.attack_type,
                'confidence': hybrid_result.confidence,
                'severity': hybrid_result.severity,
                'reason': hybrid_result.reason,
                'rules_triggered': hybrid_result.rules_triggered,
                'ml_confidence': float(confidence),
                'detection_method': 'hybrid' if len(hybrid_result.rules_triggered) > 0 else 'ml'
            }
            
        except Exception as e:
            logger.error(f"Error in prediction: {e}")
            return self._mock_predict(packet_data, None)
    
    def predict_batch(self, packets: list) -> list:
        """
        Predict attacks on multiple packets.
        
        Args:
            packets: List of packet dictionaries
            
        Returns:
            List of prediction results
        """
        results = []
        for packet in packets:
            result = self.predict_single(packet)
            results.append(result)
        return results
    
    def _mock_predict(self, packet_data: Dict, features) -> Dict:
        """
        Mock prediction for testing without ML model.
        Uses simple heuristics.
        """
        # Use rule engine for mock prediction
        result = self.rule_detector.detect(packet_data)
        
        return {
            'is_attack': result.is_attack,
            'attack_type': result.attack_type,
            'confidence': result.confidence,
            'severity': result.severity,
            'reason': result.reason,
            'rules_triggered': result.rules_triggered,
            'ml_confidence': 0.0,
            'detection_method': 'rule_engine'
        }


class HybridDetectionEngine:
    """
    Hybrid detection engine combining ML and rules.
    Production-ready with proper error handling.
    """
    
    def __init__(self, model_dir: str = 'models'):
        self.ml_predictor = MLPredictor(model_dir)
        self.ml_predictor.load_model()
        self.rule_detector = RuleBasedDetector()
        self.stats = {
            'total_packets': 0,
            'attacks_detected': 0,
            'rules_triggered': {},
        }
    
    def detect(self, packet_data: Dict) -> Dict:
        """
        Perform hybrid detection on packet.
        
        Args:
            packet_data: Packet information
            
        Returns:
            Detection result with all metadata
        """
        self.stats['total_packets'] += 1
        
        result = self.ml_predictor.predict_single(packet_data)
        
        if result.get('is_attack'):
            self.stats['attacks_detected'] += 1
        
        # Track rules
        for rule in result.get('rules_triggered', []):
            self.stats['rules_triggered'][rule] = self.stats['rules_triggered'].get(rule, 0) + 1
        
        return result
    
    def get_stats(self) -> Dict:
        """Get detection statistics"""
        return {
            'total_packets': self.stats['total_packets'],
            'attacks_detected': self.stats['attacks_detected'],
            'detection_rate': (
                self.stats['attacks_detected'] / self.stats['total_packets'] * 100
                if self.stats['total_packets'] > 0 else 0
            ),
            'top_rules': sorted(
                self.stats['rules_triggered'].items(),
                key=lambda x: x[1],
                reverse=True
            )[:5]
        }
