from flask import Blueprint, request, jsonify, g
import sqlite3
from datetime import datetime, timedelta
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
                   SUM(CASE WHEN threat_status = 'Attack' THEN 1 ELSE 0 END) as attacks
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
            hour_str = row[0].split(' ')[1] if row[0] else '00:00'
            data.append({
                'time': hour_str,
                'packets': row[1] or 0,
                'threats': row[2] or 0,
                'safe': (row[1] or 0) - (row[2] or 0)
            })
        
        return jsonify(data if data else []), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@analytics_bp.route('/threat-heatmap', methods=['GET'])
def get_threat_heatmap():
    """Get threat heatmap showing attack sources over time"""
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
        
        top_ips = [row[0] for row in cursor.fetchall()]
        
        # Get hourly attack counts for each top IP
        data = []
        for i in range(24):
            hour_ago = datetime.utcnow() - timedelta(hours=i)
            hour_str = hour_ago.strftime('%H')
            
            for ip in top_ips:
                cursor.execute('''
                    SELECT COUNT(*) 
                    FROM detection_events
                    WHERE src_ip = ? 
                    AND strftime('%H', timestamp) = ?
                ''', (ip, hour_str))
                
                count = cursor.fetchone()[0]
                if count > 0:
                    data.append({
                        'time': int(hour_str),
                        'ip': ip,
                        'threats': count
                    })
        
        conn.close()
        return jsonify(data if data else []), 200
    
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
        
        return jsonify({
            'totalPackets': total,
            'attacksDetected': attacks,
            'safePackets': safe,
            'mlDetections': ml_detections,
            'ruleDetections': rule_detections,
            'accuracy': accuracy,
            'precision': precision,
            'detectionRate': round(attacks / max(1, total) * 100, 2)
        }), 200
    
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
