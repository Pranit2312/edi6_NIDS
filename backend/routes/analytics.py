from flask import Blueprint, request, jsonify, g
import sqlite3
from datetime import datetime, timedelta, timezone
from collections import defaultdict

analytics_bp = Blueprint('analytics', __name__)

DATABASE = 'nids.db'


@analytics_bp.route('/attack-distribution', methods=['GET'])
def get_attack_distribution():
    """Get attack type distribution from real detection events"""
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        # Get attack distribution from detection_events table
        cursor.execute('''
            SELECT attack_type, COUNT(*) as count 
            FROM detection_events 
            GROUP BY attack_type
            ORDER BY count DESC
        ''')
        
        results = cursor.fetchall()
        conn.close()
        
        data = [
            {'name': row[0] if row[0] else 'Unknown', 
             'value': row[1], 
             'color': get_attack_color(row[0] if row[0] else 'Unknown')}
            for row in results
        ]
        
        return jsonify(data if data else [{'name': 'No attacks detected', 'value': 0, 'color': '#00ff88'}]), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@analytics_bp.route('/traffic-trends', methods=['GET'])
def get_traffic_trends():
    """Get real traffic trends from detected attacks over time"""
    try:
        time_range = request.args.get('range', '24h')
        
        # Calculate time period
        if time_range == '1h':
            hours = 1
        elif time_range == '7d':
            hours = 168
        else:
            hours = 24
        
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        # Get packet counts per hour from real data
        cursor.execute(f'''
            SELECT strftime('%Y-%m-%d %H', timestamp) as hour, 
                   COUNT(*) as total_packets,
                   SUM(CASE WHEN attack_type IN ('DoS', 'ddos', 'syn flood') THEN 1 ELSE 0 END) as dos,
                   SUM(CASE WHEN attack_type IN ('Port Scan', 'portscan') THEN 1 ELSE 0 END) as portScan,
                   SUM(CASE WHEN attack_type IN ('Brute Force', 'bruteforce') THEN 1 ELSE 0 END) as bruteForce,
                   SUM(CASE WHEN threat_status = 'Attack' AND attack_type NOT IN ('DoS', 'ddos', 'syn flood', 'Port Scan', 'portscan', 'Brute Force', 'bruteforce') THEN 1 ELSE 0 END) as suspicious
            FROM packets 
            WHERE timestamp > datetime('now', '-{hours} hours')
            GROUP BY hour
            ORDER BY hour
        ''')
        
        results = cursor.fetchall()
        conn.close()
        
        # Format data
        data = []
        for row in results:
            hour_str = row[0].split(' ')[1] + ":00" if row[0] else '00:00'
            dos_count = row[2] or 0
            port_scan_count = row[3] or 0
            brute_force_count = row[4] or 0
            suspicious_count = row[5] or 0
            
            data.append({
                'time': hour_str,
                'packets': row[1] or 0,
                'threats': dos_count + port_scan_count + brute_force_count + suspicious_count,
                'dos': dos_count,
                'portScan': port_scan_count,
                'bruteForce': brute_force_count,
                'suspicious': suspicious_count
            })
        
        return jsonify(data if data else []), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@analytics_bp.route('/threat-heatmap', methods=['GET'])
def get_threat_heatmap():
    """Get top threat sources for bar chart"""
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        # Get top attack sources in last 24 hours
        cursor.execute('''
            SELECT src_ip, COUNT(*) as count
            FROM detection_events
            WHERE timestamp > datetime('now', '-24 hours')
            GROUP BY src_ip
            ORDER BY count DESC
            LIMIT 10
        ''')
        
        results = cursor.fetchall()
        conn.close()
        
        data = [
            {'ip': row[0], 'threats': row[1]}
            for row in results
        ]
        
        return jsonify(data), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@analytics_bp.route('/detection-stats', methods=['GET'])
def get_detection_stats():
    """Get detection statistics from real data"""
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        # Count attack packets
        cursor.execute('SELECT COUNT(*) FROM packets WHERE threat_status = "Attack"')
        attacks = cursor.fetchone()[0] or 0
        
        # Count safe packets
        cursor.execute('SELECT COUNT(*) FROM packets WHERE threat_status = "Safe"')
        safe = cursor.fetchone()[0] or 0
        
        # Get detection method breakdown
        cursor.execute('SELECT COUNT(*) FROM detection_events WHERE detection_method = "ML"')
        ml_detections = cursor.fetchone()[0] or 0
        
        cursor.execute('SELECT COUNT(*) FROM detection_events WHERE detection_method = "Rules"')
        rule_detections = cursor.fetchone()[0] or 0
        
        total = attacks + safe
        
        # Calculate statistics
        accuracy = 0
        precision = 0
        if total > 0:
            # Accuracy: (TP + TN) / Total
            accuracy = round((attacks + safe) / total * 100, 2) if total > 0 else 0
        
        if attacks > 0:
            # Precision: TP / (TP + FP)
            precision = round(ml_detections / (ml_detections + 1) * 100, 2)
        
        conn.close()
        
        # Format for frontend pie chart
        data = [
            {'category': 'True Positive', 'value': attacks, 'color': '#00ff88'},
            {'category': 'Safe Traffic', 'value': safe, 'color': '#00d9ff'},
            {'category': 'ML Detections', 'value': ml_detections, 'color': '#b536d9'},
            {'category': 'Rule Detections', 'value': rule_detections, 'color': '#ffb003'}
        ]
        
        return jsonify(data), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@analytics_bp.route('/severity-breakdown', methods=['GET'])
def get_severity_breakdown():
    """Get breakdown of detected attacks by severity"""
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT severity, COUNT(*) as count
            FROM detection_events
            GROUP BY severity
            ORDER BY count DESC
        ''')
        
        results = cursor.fetchall()
        conn.close()
        
        severity_colors = {
            'critical': '#ff0000',
            'high': '#ff6b35',
            'medium': '#ffb700',
            'low': '#ffd700',
        }
        
        data = [
            {'name': row[0] if row[0] else 'Unknown',
             'value': row[1],
             'color': severity_colors.get(row[0].lower() if row[0] else 'unknown', '#666666')}
            for row in results
        ]
        
        return jsonify(data if data else []), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@analytics_bp.route('/confidence-distribution', methods=['GET'])
def get_confidence_distribution():
    """Get ML confidence distribution from real detection events"""
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        # Get confidence values
        cursor.execute('SELECT ml_confidence FROM packets')
        results = cursor.fetchall()
        conn.close()
        
        # Group into 10% bins
        bins = [0] * 10
        for row in results:
            conf = row[0] or 0
            bin_idx = min(int(conf * 10), 9)
            bins[bin_idx] += 1
            
        data = [
            {'range': f'{i*10}-{(i+1)*10}%', 'count': count}
            for i, count in enumerate(bins)
        ]
        
        return jsonify(data), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


def get_attack_color(attack_type):
    """Get color for attack type"""
    attack_type = str(attack_type).lower()
    colors = {
        'dos': '#ff006e',
        'ddos': '#ff006e',
        'port scan': '#b536d9',
        'portscan': '#b536d9',
        'brute force': '#ffb003',
        'bruteforce': '#ffb003',
        'syn flood': '#00d9ff',
        'synflood': '#00d9ff',
        'icmp flood': '#ff69b4',
        'icmpflood': '#ff69b4',
        'infiltration': '#ff8c00',
        'botnet': '#8b0000',
        'normal': '#00ff88',
        'unknown': '#a8b3be'
    }
    return colors.get(attack_type, '#a8b3be')
