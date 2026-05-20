from flask import Blueprint, request, jsonify, g
import sqlite3
from datetime import datetime, timedelta
import psutil
import os

monitoring_bp = Blueprint('monitoring', __name__)

DATABASE = 'nids.db'


@monitoring_bp.route('/stats', methods=['GET'])
def get_stats():
    """Get real-time monitoring statistics from NIDS_STATE"""
    try:
        # Get live stats from NIDS_STATE (injected by app.py)
        total_packets = g.stats.get('packets_captured', 0)
        total_attacks = g.stats.get('attacks_detected', 0)
        
        # Calculate safe traffic percentage
        safe_traffic = 100.0
        if total_packets > 0:
            safe_traffic = (1 - (total_attacks / total_packets)) * 100
        
        # Get system metrics
        try:
            cpu_usage = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            memory_usage = memory.percent
        except:
            cpu_usage = 0
            memory_usage = 0
        
        # Count active connections from recent packets
        active_connections = len(set(
            (p['src_ip'], p['dst_ip']) for p in g.recent_packets 
            if isinstance(p, dict) and 'src_ip' in p
        ))
        
        return jsonify({
            'totalPackets': total_packets,
            'threatsDetected': total_attacks,
            'safeTraffic': round(safe_traffic, 1),
            'activeConnections': active_connections,
            'cpuUsage': round(cpu_usage, 1),
            'memoryUsage': round(memory_usage, 1),
            'engineRunning': True,
            'lastUpdate': g.stats.get('last_update'),
        }), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@monitoring_bp.route('/packets', methods=['GET'])
def get_packets():
    """Get recent captured packets from NIDS_STATE"""
    try:
        limit = request.args.get('limit', 50, type=int)
        
        # Get recent packets from memory (real-time)
        packets = g.recent_packets[-limit:] if g.recent_packets else []
        
        # If no real packets yet, query database
        if not packets:
            conn = sqlite3.connect(DATABASE)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT src_ip, dst_ip, protocol, src_port, dst_port, packet_size, 
                       timestamp, threat_status, ml_confidence, attack_type
                FROM packets 
                ORDER BY timestamp DESC 
                LIMIT ?
            ''', (limit,))
            
            packets = [dict(row) for row in cursor.fetchall()]
            conn.close()
        
        return jsonify(packets), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@monitoring_bp.route('/packets/search', methods=['GET'])
def search_packets():
    """Search packets by IP or protocol"""
    try:
        query = request.args.get('query', '').lower()
        
        if not query:
            return jsonify([]), 200
        
        # Search in recent packets (real-time)
        results = []
        for p in g.recent_packets:
            if isinstance(p, dict):
                if (query in str(p.get('src_ip', '')).lower() or
                    query in str(p.get('dst_ip', '')).lower() or
                    query in str(p.get('protocol', '')).lower()):
                    results.append(p)
        
        # If not enough results, query database
        if len(results) < 10:
            conn = sqlite3.connect(DATABASE)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT src_ip, dst_ip, protocol, packet_size, timestamp, 
                       threat_status, ml_confidence, attack_type
                FROM packets 
                WHERE src_ip LIKE ? OR dst_ip LIKE ? OR protocol LIKE ?
                ORDER BY timestamp DESC
                LIMIT 100
            ''', (f'%{query}%', f'%{query}%', f'%{query}%'))
            
            db_results = [dict(row) for row in cursor.fetchall()]
            conn.close()
            results.extend(db_results)
        
        return jsonify(results[:100]), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@monitoring_bp.route('/packets/filter', methods=['GET'])
def filter_packets():
    """Filter packets by protocol or threat status"""
    try:
        protocol = request.args.get('protocol', '').upper()
        threat_status = request.args.get('threat_status', '')
        
        # Filter recent packets
        results = []
        for p in g.recent_packets:
            if isinstance(p, dict):
                match = True
                if protocol and str(p.get('protocol', '')).upper() != protocol:
                    match = False
                if threat_status:
                    is_threat = p.get('is_attack', False)
                    if threat_status == 'safe' and is_threat:
                        match = False
                    elif threat_status == 'threat' and not is_threat:
                        match = False
                if match:
                    results.append(p)
        
        # If not enough results, query database
        if len(results) < 20:
            conn = sqlite3.connect(DATABASE)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            query = 'SELECT * FROM packets WHERE 1=1'
            params = []
            
            if protocol:
                query += ' AND protocol = ?'
                params.append(protocol)
            
            if threat_status:
                if threat_status == 'threat':
                    query += ' AND threat_status = "Attack"'
                elif threat_status == 'safe':
                    query += ' AND threat_status = "Safe"'
            
            query += ' ORDER BY timestamp DESC LIMIT 100'
            
            cursor.execute(query, params)
            db_results = [dict(row) for row in cursor.fetchall()]
            conn.close()
            results.extend(db_results)
        
        return jsonify(results[:100]), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@monitoring_bp.route('/alerts', methods=['GET'])
def get_alerts():
    """Get recent detected attacks/alerts"""
    try:
        limit = request.args.get('limit', 10, type=int)
        
        # Get recent alerts from memory (real-time)
        alerts = g.recent_alerts[-limit:] if g.recent_alerts else []
        
        # If no real alerts yet, query database
        if not alerts:
            conn = sqlite3.connect(DATABASE)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT title, description, severity, source_ip, attack_type, timestamp
                FROM alerts 
                ORDER BY timestamp DESC 
                LIMIT ?
            ''', (limit,))
            
            alerts = [dict(row) for row in cursor.fetchall()]
            conn.close()
        
        return jsonify(alerts), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500
