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
from datetime import datetime, timedelta, timezone
from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import time
import signal
import socket
from functools import lru_cache

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import detection components
from utils.packet_capture import PacketSniffer, PacketProcessor, rate_tracker
from utils.predictor import HybridDetectionEngine, MLPredictor
from utils.feature_extractor import FeatureExtractor
from utils.stats_manager import stats_manager

# Import routes
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

@app.route('/api/stats', methods=['GET'])
def get_stats():
    return jsonify(stats_manager.get_stats())   


# ============================================================
# GLOBAL NIDS STATE
# ============================================================

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


# ============================================================
# DATABASE INITIALIZATION
# ============================================================

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
            role TEXT DEFAULT 'user',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Raw packets table
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

    # Detection events table
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

    # Logs table
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

    # Statistics table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS statistics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            metric_name TEXT NOT NULL,
            metric_value REAL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Indexes
    cursor.execute(
        'CREATE INDEX IF NOT EXISTS idx_packets_timestamp ON packets(timestamp)')
    cursor.execute(
        'CREATE INDEX IF NOT EXISTS idx_packets_src_ip ON packets(src_ip)')
    cursor.execute(
        'CREATE INDEX IF NOT EXISTS idx_detection_timestamp ON detection_events(timestamp)')
    cursor.execute(
        'CREATE INDEX IF NOT EXISTS idx_detection_attack ON detection_events(attack_type)')

    # Create demo user if it doesn't exist
    try:
        import hashlib
        demo_password = hashlib.sha256('demo123'.encode()).hexdigest()
        cursor.execute(
            'INSERT INTO users (username, email, password) VALUES (?, ?, ?)',
            ('demo', 'demo@nids.local', demo_password)
        )
        logger.info("Demo user created successfully")
    except sqlite3.IntegrityError:
        logger.info("Demo user already exists")

    conn.commit()
    conn.close()

    logger.info("Database initialized successfully")


# ============================================================
# PACKET DETECTION CALLBACK
# ============================================================

def packet_detection_callback(packet_data):
    """
    Called whenever packet processor processes a packet.
    Enriches raw packet with computed rates before detection.
    """

    try:
        # CRITICAL: Enrich packet with real-time rate data
        # This computes packet_rate, byte_rate, syn_rate, flow_packets
        # Without this, all rate-based rules see 0 and never trigger
        enriched_packet = rate_tracker.record_packet(packet_data)

        # Perform hybrid detection on enriched packet
        detection_result = NIDS_STATE.detector.detect(enriched_packet)

        # Update statistics
        is_attack = detection_result.get('is_attack', False)
        stats_manager.update_packet(packet_data, is_attack)
        
        # Keep NIDS_STATE.stats in sync
        NIDS_STATE.stats['packets_captured'] = stats_manager.total_packets
        if is_attack:
            NIDS_STATE.stats['attacks_detected'] = stats_manager.threats_detected
            stats_manager.update_alert(detection_result.get('attack_type', 'Unknown'))
            logger.warning(f"ATTACK DETECTED: {detection_result.get('attack_type')} from {packet_data.get('src_ip')} ({detection_result.get('confidence'):.1%})")

        NIDS_STATE.stats['last_update'] = datetime.now(timezone.utc).isoformat()

        # Store packet in DB
        store_packet(packet_data, detection_result)

        # Store recent packets in memory for real-time frontend
        packet_info = {
            'src_ip': packet_data.get('src_ip', '0.0.0.0'),
            'dst_ip': packet_data.get('dst_ip', '0.0.0.0'),
            'protocol': packet_data.get('protocol', 'OTHER'),
            'timestamp': packet_data.get('timestamp', datetime.now(timezone.utc).isoformat()),
            'packet_size': packet_data.get('packet_size', 0),
            'is_attack': is_attack,
            'threat_status': 'Attack' if is_attack else 'Safe',
            'attack_type': detection_result.get('attack_type', 'Normal'),
            'ml_confidence': round(detection_result.get('ml_confidence', 0) * 100, 2),
            'detection_method': detection_result.get('detection_method', 'unknown')
        }
        
        NIDS_STATE.recent_packets.append(packet_info)

        # Limit packet memory
        if len(NIDS_STATE.recent_packets) > app.config['MAX_PACKETS_MEMORY']:
            NIDS_STATE.recent_packets = NIDS_STATE.recent_packets[-app.config['MAX_PACKETS_MEMORY']:]

        # Add alerts
        if is_attack:
            alert = {
                'id': len(NIDS_STATE.recent_alerts) + 1,
                'type': detection_result.get('attack_type', 'Unknown'),
                'severity': detection_result.get('severity', 'medium'),
                'confidence': detection_result.get('confidence', 0),
                'src_ip': packet_data.get('src_ip', ''),
                'dst_ip': packet_data.get('dst_ip', ''),
                'timestamp': packet_data.get('timestamp', ''),
                'description': detection_result.get('reason', 'Suspicious activity detected')
            }

            NIDS_STATE.recent_alerts.append(alert)

            if len(NIDS_STATE.recent_alerts) > 100:
                NIDS_STATE.recent_alerts = NIDS_STATE.recent_alerts[-100:]

    except Exception as e:
        logger.error(f"Error in detection callback: {e}")


# ============================================================
# STORE PACKETS
# ============================================================

def store_packet(packet_data: dict, detection_result: dict):

    try:

        conn = sqlite3.connect(app.config['DATABASE'])
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO packets 
            (
                src_ip,
                dst_ip,
                protocol,
                src_port,
                dst_port,
                packet_size,
                threat_status,
                ml_confidence,
                attack_type,
                detection_method
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (

            packet_data.get('src_ip', ''),
            packet_data.get('dst_ip', ''),
            packet_data.get('protocol', ''),
            packet_data.get('src_port', 0),
            packet_data.get('dst_port', 0),
            packet_data.get('packet_size', 0),

            'Attack' if detection_result.get('is_attack') else 'Safe',

            round(detection_result.get('ml_confidence', 0) * 100, 2),
            detection_result.get('attack_type', 'Normal'),
            detection_result.get('detection_method', 'unknown')

        ))

        packet_id = cursor.lastrowid

        # Store attack event
        if detection_result.get('is_attack'):

            cursor.execute('''
                INSERT INTO detection_events
                (
                    src_ip,
                    dst_ip,
                    protocol,
                    attack_type,
                    severity,
                    confidence,
                    rules_triggered,
                    ml_confidence,
                    detection_method,
                    packet_id
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (

                packet_data.get('src_ip', ''),
                packet_data.get('dst_ip', ''),
                packet_data.get('protocol', ''),

                detection_result.get('attack_type', 'Unknown'),
                detection_result.get('severity', 'medium'),
                detection_result.get('confidence', 0),

                json.dumps(
                    detection_result.get('rules_triggered', [])
                ),

                detection_result.get('ml_confidence', 0),
                detection_result.get('detection_method', 'unknown'),

                packet_id

            ))

        conn.commit()
        conn.close()

    except Exception as e:
        logger.error(f"Error storing packet: {e}")


# ============================================================
# DETECTION ENGINE
# ============================================================

def start_detection_engine():

    logger.info("Starting detection engine...")

    # Packet queue
    NIDS_STATE.packet_queue = queue.Queue(maxsize=1000)

    # Hybrid detector
    NIDS_STATE.detector = HybridDetectionEngine(
        model_dir='models'
    )

    # Log detector status
    logger.info(f"Detector initialized: ML Loaded={NIDS_STATE.detector.ml_predictor.loaded}")

    # Packet sniffer
    NIDS_STATE.sniffer = PacketSniffer(
        packet_queue=NIDS_STATE.packet_queue,
        interface=None,
        filter_expr="ip"
    )

    NIDS_STATE.sniffer.start()

    # Packet processor
    NIDS_STATE.processor = PacketProcessor(
        packet_queue=NIDS_STATE.packet_queue,
        detection_callback=packet_detection_callback,
        batch_size=1
    )

    NIDS_STATE.processor.start()

    NIDS_STATE.running = True

    logger.info("Detection engine started successfully")


def stop_detection_engine():

    logger.info("Stopping detection engine...")

    if NIDS_STATE.processor:
        NIDS_STATE.processor.stop()

    if NIDS_STATE.sniffer:
        NIDS_STATE.sniffer.stop()

    NIDS_STATE.running = False
    logger.info("Detection engine stopped")


def signal_handler(sig, frame):
    """Handle termination signals"""
    logger.info("Shutdown signal received...")
    stop_detection_engine()
    sys.exit(0)


# Register signal handlers
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)


@lru_cache(maxsize=1024)
def resolve_hostname(ip):
    """Resolve IP to hostname with caching"""
    try:
        # Don't resolve local/private IPs to save time
        if ip.startswith(('192.168.', '10.', '127.', '172.')):
            return None
        return socket.gethostbyaddr(ip)[0]
    except (socket.herror, socket.gaierror, socket.timeout):
        return None


# ============================================================
# API ROUTES
# ============================================================

@monitoring_bp.before_request
def inject_detector():

    from flask import g

    g.detector = NIDS_STATE.detector
    g.recent_packets = NIDS_STATE.recent_packets
    g.recent_alerts = NIDS_STATE.recent_alerts
    g.stats = NIDS_STATE.stats


# ============================================================
# REGISTER ROUTES
# ============================================================

app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(monitoring_bp, url_prefix='/api')
app.register_blueprint(analytics_bp, url_prefix='/api/analytics')
app.register_blueprint(logs_bp, url_prefix='/api/logs')
app.register_blueprint(settings_bp, url_prefix='/api')


# ============================================================
# API ROUTES
# ============================================================

@app.route('/api/interfaces', methods=['GET'])
def get_interfaces():
    """Get list of available network interfaces"""
    try:
        interfaces = PacketSniffer.get_interfaces()
        return jsonify(interfaces), 200
    except Exception as e:
        logger.error(f"Error getting interfaces: {e}")
        return jsonify([]), 500


@app.route('/api/settings/interface', methods=['POST'])
def set_interface():
    """Set active network interface"""
    try:
        data = request.json
        interface = data.get('interface')
        
        if not interface:
            return jsonify({'error': 'No interface provided'}), 400
            
        logger.info(f"Changing interface to: {interface}")
        
        # Stop current engine
        stop_detection_engine()
        
        # Start with new interface
        NIDS_STATE.sniffer = PacketSniffer(
            packet_queue=NIDS_STATE.packet_queue,
            interface=interface if interface != 'auto' else None
        )
        NIDS_STATE.sniffer.start()
        
        NIDS_STATE.processor = PacketProcessor(
            packet_queue=NIDS_STATE.packet_queue,
            detection_callback=packet_detection_callback
        )
        NIDS_STATE.processor.start()
        NIDS_STATE.running = True
        
        return jsonify({'message': f'Interface changed to {interface}'}), 200
        
    except Exception as e:
        logger.error(f"Error setting interface: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/health', methods=['GET'])
def health():

    return jsonify({
        'status': 'healthy' if NIDS_STATE.running else 'stopped',
        'version': '2.0',
        'engine': 'Hybrid ML + Rules',
        'packets_captured': NIDS_STATE.stats['packets_captured'],
        'attacks_detected': NIDS_STATE.stats['attacks_detected'],
        'timestamp': datetime.now(timezone.utc).isoformat()
    })


@app.route('/api/realtime/stats', methods=['GET'])
def get_realtime_stats():

    return jsonify({
        'packets_captured': NIDS_STATE.stats.get('packets_captured', 0),
        'attacks_detected': NIDS_STATE.stats.get('attacks_detected', 0),

        'detection_rate': (
            NIDS_STATE.stats.get('attacks_detected', 0)
            /
            max(1, NIDS_STATE.stats.get('packets_captured', 1))
        ) * 100,

        'last_update': NIDS_STATE.stats.get('last_update'),

        'engine_status': (
            'running'
            if NIDS_STATE.running
            else 'stopped'
        )
    })


# ============================================================
# AFTER REQUEST
# ============================================================

@app.after_request
def after_request(response):

    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'

    return response


# ============================================================
# ERROR HANDLERS
# ============================================================

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404


@app.errorhandler(500)
def server_error(error):

    logger.error(f"Server error: {error}")

    return jsonify({'error': 'Internal server error'}), 500


# ============================================================
# MAIN
# ============================================================

if __name__ == '__main__':

    # Initialize database
    init_db()

    # Start detection engine
    try:
        start_detection_engine()

    except Exception as e:
        logger.error(f"Failed to start detection engine: {e}")

    # Run Flask app
    try:

        logger.info("Starting NIDS Backend Server...")

        app.run(
            host='127.0.0.1',
            port=8081,
            debug=False,
            threaded=True,
            use_reloader=False
        )

    except KeyboardInterrupt:

        logger.info("Shutdown requested...")

    except Exception as e:

        logger.error(f"Critical server error: {e}")

    # finally:

    #     stop_detection_engine()