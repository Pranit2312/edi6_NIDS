from flask import Blueprint, request, jsonify, send_file
import sqlite3
from datetime import datetime
import csv
import io

logs_bp = Blueprint('logs', __name__)

DATABASE = 'nids.db'


@logs_bp.route('', methods=['GET'])
def get_logs():
    """Get attack logs with pagination"""
    try:
        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', 50, type=int)
        offset = (page - 1) * limit
        
        conn = sqlite3.connect(DATABASE)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Get total count from detection_events
        cursor.execute('SELECT COUNT(*) FROM detection_events')
        total = cursor.fetchone()[0]
        
        # Get paginated detection logs
        cursor.execute('''
            SELECT id, src_ip, dst_ip, protocol, attack_type, severity, 
                   confidence, ml_confidence, detection_method, timestamp
            FROM detection_events 
            ORDER BY timestamp DESC 
            LIMIT ? OFFSET ?
        ''', (limit, offset))
        
        logs = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return jsonify({
            'logs': logs,
            'page': page,
            'limit': limit,
            'total': total,
            'pages': (total + limit - 1) // limit
        }), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@logs_bp.route('/search', methods=['GET'])
def search_logs():
    """Search detection logs"""
    try:
        query = request.args.get('query', '').lower()
        severity = request.args.get('severity', '')
        attack_type = request.args.get('attack_type', '')
        
        if not query and not severity and not attack_type:
            return jsonify([]), 200
        
        conn = sqlite3.connect(DATABASE)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        sql = '''
            SELECT id, src_ip, dst_ip, protocol, attack_type, severity, 
                   confidence, ml_confidence, detection_method, timestamp
            FROM detection_events 
            WHERE 1=1
        '''
        params = []
        
        if query:
            sql += ''' AND (src_ip LIKE ? OR dst_ip LIKE ? OR attack_type LIKE ?)'''
            params.extend([f'%{query}%', f'%{query}%', f'%{query}%'])
        
        if severity:
            sql += ' AND severity = ?'
            params.append(severity)
        
        if attack_type:
            sql += ' AND attack_type = ?'
            params.append(attack_type)
        
        sql += ' ORDER BY timestamp DESC LIMIT 100'
        
        cursor.execute(sql, params)
        logs = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return jsonify(logs), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@logs_bp.route('/export', methods=['GET'])
def export_logs():
    """Export detection logs as CSV"""
    try:
        conn = sqlite3.connect(DATABASE)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, src_ip, dst_ip, protocol, attack_type, severity, 
                   confidence, ml_confidence, detection_method, timestamp
            FROM detection_events 
            ORDER BY timestamp DESC
        ''')
        logs = cursor.fetchall()
        conn.close()
        
        # Create CSV
        output = io.StringIO()
        if logs:
            writer = csv.writer(output)
            writer.writerow([
                'ID', 'Source IP', 'Dest IP', 'Protocol', 'Attack Type', 
                'Severity', 'Confidence', 'ML Confidence', 'Detection Method', 'Timestamp'
            ])
            
            for log in logs:
                writer.writerow([
                    log['id'],
                    log['src_ip'],
                    log['dst_ip'],
                    log['protocol'],
                    log['attack_type'],
                    log['severity'],
                    log['confidence'],
                    log['ml_confidence'],
                    log['detection_method'],
                    log['timestamp']
                ])
        
        # Convert to bytes
        output.seek(0)
        return send_file(
            io.BytesIO(output.getvalue().encode()),
            mimetype='text/csv',
            as_attachment=True,
            download_name=f'detection_logs_{datetime.now().isoformat()}.csv'
        ), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@logs_bp.route('/summary', methods=['GET'])
def get_logs_summary():
    """Get summary statistics of attack logs"""
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        # Total attacks
        cursor.execute('SELECT COUNT(*) FROM detection_events')
        total_attacks = cursor.fetchone()[0]
        
        # By severity
        cursor.execute('SELECT severity, COUNT(*) FROM detection_events GROUP BY severity')
        severity_stats = dict(cursor.fetchall())
        
        # By detection method
        cursor.execute('SELECT detection_method, COUNT(*) FROM detection_events GROUP BY detection_method')
        method_stats = dict(cursor.fetchall())
        
        # Latest attacks
        cursor.execute('''
            SELECT attack_type, severity, timestamp
            FROM detection_events
            ORDER BY timestamp DESC
            LIMIT 5
        ''')
        latest = [dict(zip(['attack_type', 'severity', 'timestamp'], row)) for row in cursor.fetchall()]
        
        conn.close()
        
        return jsonify({
            'totalAttacks': total_attacks,
            'bySeverity': severity_stats,
            'byDetectionMethod': method_stats,
            'latestAttacks': latest
        }), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@logs_bp.route('', methods=['DELETE'])
def clear_logs():
    """Clear all detection logs"""
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM detection_events')
        cursor.execute('DELETE FROM alerts')
        conn.commit()
        conn.close()
        
        return jsonify({'message': 'All detection logs cleared'}), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@logs_bp.route('/<int:log_id>', methods=['DELETE'])
def delete_log(log_id):
    """Delete specific detection log"""
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM detection_events WHERE id = ?', (log_id,))
        conn.commit()
        conn.close()
        
        return jsonify({'message': 'Detection log deleted'}), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500
