"""
Professional NIDS Backend - Flask Application
Real-time packet capture, ML detection, and hybrid IDS engine
"""

import os
import sys
import sqlite3
import threading
import queue
import json
import logging
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import detection components
from utils.packet_capture import PacketSniffer, PacketProcessor
from utils.predictor import HybridDetectionEngine, MLPredictor
from utils.feature_extractor import FeatureExtractor
from routes.auth import auth_bp
from routes.monitoring import monitoring_bp
from routes.analytics import analytics_bp
from routes.logs import logs_bp
from routes.settings import settings_bp

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Configuration
app.config['SECRET_KEY'] = 'nids-production-secret-2024'
app.config['DATABASE'] = 'nids.db'
app.config['MAX_PACKETS_MEMORY'] = 10000

# Global state
class NIDS_STATE:
    """Global NIDS state management"""
    sniffer = None
    processor = None
    detector = None
    packet_queue = None
    running = False
    stats = {
        'packets_captured': 0,
        'attacks_detected': 0,
        'last_update': None,
    }
    recent_alerts = []
    recent_packets = []


def init_db():
    """Initialize database schema"""
    logger.info("Initializing database...")
    conn = sqlite3.connect(app.config['DATABASE'])
    cursor = conn.cursor()
    
    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Raw packets table - stores ALL captured packets
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS packets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            src_ip TEXT NOT NULL,
            dst_ip TEXT NOT NULL,
            protocol TEXT NOT NULL,
            src_port INTEGER,
            dst_port INTEGER,
            packet_size INTEGER,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            threat_status TEXT,
            ml_confidence REAL,
            attack_type TEXT,
            detection_method TEXT
        )
    ''')
    
    # Detection events - stores detected attacks
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS detection_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            src_ip TEXT NOT NULL,
            dst_ip TEXT NOT NULL,
            protocol TEXT,
            attack_type TEXT NOT NULL,
            severity TEXT,
            confidence REAL,
            rules_triggered TEXT,
            ml_confidence REAL,
            detection_method TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            packet_id INTEGER,
            FOREIGN KEY(packet_id) REFERENCES packets(id)
        )
    ''')
    
    # Logs table - activity logs
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            attack_type TEXT NOT NULL,
            source_ip TEXT NOT NULL,
            dest_ip TEXT NOT NULL,
            protocol TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            severity TEXT,
            confidence REAL,
            status TEXT
        )
    ''')
    
    # Alerts table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            severity TEXT,
            source_ip TEXT,
            attack_type TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            read INTEGER DEFAULT 0
        )
    ''')
    
    # Statistics table - aggregated data
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS statistics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            metric_name TEXT NOT NULL,
            metric_value REAL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create indexes for performance
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_packets_timestamp ON packets(timestamp)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_packets_src_ip ON packets(src_ip)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_detection_timestamp ON detection_events(timestamp)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_detection_attack ON detection_events(attack_type)')
    
    conn.commit()
    conn.close()
    logger.info("Database initialized successfully")


def packet_detection_callback(packet_data):
    """
    Callback function for packet processing.
    Receives parsed packets and performs detection.
    """
    try:
        # Perform detection
        detection_result = NIDS_STATE.detector.detect(packet_data)
        
        # Update statistics
        NIDS_STATE.stats['packets_captured'] += 1
        if detection_result.get('is_attack'):
            NIDS_STATE.stats['attacks_detected'] += 1
        NIDS_STATE.stats['last_update'] = datetime.utcnow().isoformat()
        
        # Store packet in database
        store_packet(packet_data, detection_result)
        
        # Keep recent packets in memory
        NIDS_STATE.recent_packets.append({
            'src_ip': packet_data.get('src_ip', ''),
            'dst_ip': packet_data.get('dst_ip', ''),
            'protocol': packet_data.get('protocol', ''),
            'timestamp': packet_data.get('timestamp', ''),
            'is_attack': detection_result.get('is_attack', False),
            'confidence': detection_result.get('confidence', 0),
        })
        
        # Keep only last N packets
        if len(NIDS_STATE.recent_packets) > app.config['MAX_PACKETS_MEMORY']:
            NIDS_STATE.recent_packets = NIDS_STATE.recent_packets[-app.config['MAX_PACKETS_MEMORY']:]
        
        # If attack detected, add to alerts
        if detection_result.get('is_attack'):
            alert = {
                'type': detection_result.get('attack_type', 'Unknown'),
                'severity': detection_result.get('severity', 'medium'),
                'confidence': detection_result.get('confidence', 0),
                'src_ip': packet_data.get('src_ip', ''),
                'timestamp': packet_data.get('timestamp', ''),
            }
            NIDS_STATE.recent_alerts.append(alert)
            
            # Keep only last N alerts
            if len(NIDS_STATE.recent_alerts) > 100:
                NIDS_STATE.recent_alerts = NIDS_STATE.recent_alerts[-100:]
            
            logger.warning(f"ATTACK DETECTED: {alert}")
    
    except Exception as e:
        logger.error(f"Error in detection callback: {e}")


def store_packet(packet_data: dict, detection_result: dict):
    """
    Store packet and detection result in database.
    """
    try:
        conn = sqlite3.connect(app.config['DATABASE'])
        cursor = conn.cursor()
        
        # Insert packet
        cursor.execute('''
            INSERT INTO packets 
            (src_ip, dst_ip, protocol, src_port, dst_port, packet_size, threat_status, 
             ml_confidence, attack_type, detection_method)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            packet_data.get('src_ip', ''),
            packet_data.get('dst_ip', ''),
            packet_data.get('protocol', ''),
            packet_data.get('src_port', 0),
            packet_data.get('dst_port', 0),
            packet_data.get('packet_size', 0),
            'Attack' if detection_result.get('is_attack') else 'Safe',
            detection_result.get('ml_confidence', 0),
            detection_result.get('attack_type', 'Normal'),
            detection_result.get('detection_method', 'unknown')
        ))
        
        packet_id = cursor.lastrowid
        
        # Insert detection event if attack
        if detection_result.get('is_attack'):
            cursor.execute('''
                INSERT INTO detection_events
                (src_ip, dst_ip, protocol, attack_type, severity, confidence, 
                 rules_triggered, ml_confidence, detection_method, packet_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                packet_data.get('src_ip', ''),
                packet_data.get('dst_ip', ''),
                packet_data.get('protocol', ''),
                detection_result.get('attack_type', 'Unknown'),
                detection_result.get('severity', 'medium'),
                detection_result.get('confidence', 0),
                json.dumps(detection_result.get('rules_triggered', [])),
                detection_result.get('ml_confidence', 0),
                detection_result.get('detection_method', 'unknown'),
                packet_id
            ))
            
            # Insert alert
            cursor.execute('''
                INSERT INTO alerts (title, description, severity, source_ip, attack_type)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                f"{detection_result.get('attack_type')} Detected",
                detection_result.get('reason', 'Attack detected by NIDS'),
                detection_result.get('severity', 'medium'),
                packet_data.get('src_ip', ''),
                detection_result.get('attack_type', 'Unknown')
            ))
        
        conn.commit()
        conn.close()
    
    except Exception as e:
        logger.error(f"Error storing packet: {e}")


def start_detection_engine():
    """Start the packet sniffer and detection engine"""
    logger.info("Starting detection engine...")
    
    # Create packet queue
    NIDS_STATE.packet_queue = queue.Queue(maxsize=1000)
    
    # Initialize detector
    NIDS_STATE.detector = HybridDetectionEngine(model_dir='models')
    
    # Initialize and start sniffer
    NIDS_STATE.sniffer = PacketSniffer(
        packet_queue=NIDS_STATE.packet_queue,
        interface=None,  # Auto-detect
        filter_expr="ip"
    )
    NIDS_STATE.sniffer.start()
    
    # Initialize and start processor
    NIDS_STATE.processor = PacketProcessor(
        packet_queue=NIDS_STATE.packet_queue,
        detection_callback=packet_detection_callback,
        batch_size=1
    )
    NIDS_STATE.processor.start()
    
    NIDS_STATE.running = True
    logger.info("Detection engine started successfully")


def stop_detection_engine():
    """Stop the detection engine gracefully"""
    logger.info("Stopping detection engine...")
    
    if NIDS_STATE.processor:
        NIDS_STATE.processor.stop()
    
    if NIDS_STATE.sniffer:
        NIDS_STATE.sniffer.stop()
    
    NIDS_STATE.running = False
    logger.info("Detection engine stopped")


# Register blueprints with detection context
@monitoring_bp.before_request
def inject_detector():
    """Inject detector into monitoring routes"""
    from flask import g
    g.detector = NIDS_STATE.detector
    g.recent_packets = NIDS_STATE.recent_packets
    g.recent_alerts = NIDS_STATE.recent_alerts
    g.stats = NIDS_STATE.stats


# Register blueprints
app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(monitoring_bp, url_prefix='/api')
app.register_blueprint(analytics_bp, url_prefix='/api/analytics')
app.register_blueprint(logs_bp, url_prefix='/api/logs')
app.register_blueprint(settings_bp, url_prefix='/api')


# Health check endpoint
@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({
        'status': 'healthy' if NIDS_STATE.running else 'stopped',
        'version': '2.0',
        'engine': 'Hybrid ML+Rules',
        'packets_captured': NIDS_STATE.stats['packets_captured'],
        'attacks_detected': NIDS_STATE.stats['attacks_detected'],
        'timestamp': datetime.utcnow().isoformat()
    })


# Real-time stats endpoint
@app.route('/api/realtime/stats', methods=['GET'])
def realtime_stats():
    return jsonify({
        'total_packets': NIDS_STATE.stats['packets_captured'],
        'total_attacks': NIDS_STATE.stats['attacks_detected'],
        'detection_rate': (
            NIDS_STATE.stats['attacks_detected'] / max(NIDS_STATE.stats['packets_captured'], 1) * 100
        ),
        'running': NIDS_STATE.running,
        'detector_stats': NIDS_STATE.detector.get_stats() if NIDS_STATE.detector else {},
        'timestamp': datetime.utcnow().isoformat()
    })


# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404


@app.errorhandler(500)
def server_error(error):
    logger.error(f"Server error: {error}")
    return jsonify({'error': 'Internal server error'}), 500


if __name__ == '__main__':
    try:
        # Initialize database
        init_db()
        
        # Start detection engine
        start_detection_engine()
        
        # Run Flask app
        logger.info("Starting NIDS Backend Server...")
        app.run(
            host='0.0.0.0',
            port=5000,
            debug=False,
            use_reloader=False,
            threaded=True
        )
    
    except KeyboardInterrupt:
        logger.info("Shutdown requested...")
        stop_detection_engine()
    
    except Exception as e:
        logger.error(f"Critical error: {e}")
        stop_detection_engine()
        sys.exit(1)
