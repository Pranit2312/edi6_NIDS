from flask import Blueprint, request, jsonify
import sqlite3
from datetime import datetime

settings_bp = Blueprint('settings', __name__)

DATABASE = 'nids.db'

# Global settings
monitoring_status = {'active': True}

@settings_bp.route('/settings', methods=['GET'])
def get_settings():
    """Get user settings"""
    try:
        return jsonify({
            'sensitivity': 7,
            'darkMode': True,
            'emailAlerts': True,
            'pushNotifications': True,
            'criticalOnly': False,
            'dailyReport': True,
            'autoResponse': True,
            'blockThreshold': 75,
            'refreshInterval': 5000
        }), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@settings_bp.route('/settings', methods=['PUT'])
def update_settings():
    """Update user settings"""
    try:
        data = request.json
        
        # Settings would be saved to database in production
        # For now, just validate and return
        
        return jsonify({
            'message': 'Settings updated successfully',
            'settings': data
        }), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@settings_bp.route('/monitoring/start', methods=['POST'])
def start_monitoring():
    """Start monitoring"""
    try:
        global monitoring_status
        monitoring_status['active'] = True
        
        return jsonify({
            'message': 'Monitoring started',
            'status': 'active'
        }), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@settings_bp.route('/monitoring/stop', methods=['POST'])
def stop_monitoring():
    """Stop monitoring"""
    try:
        global monitoring_status
        monitoring_status['active'] = False
        
        return jsonify({
            'message': 'Monitoring stopped',
            'status': 'inactive'
        }), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@settings_bp.route('/monitoring/status', methods=['GET'])
def get_monitoring_status():
    """Get monitoring status"""
    try:
        return jsonify({
            'status': 'active' if monitoring_status['active'] else 'inactive',
            'active': monitoring_status['active'],
            'uptime': '14d 5h 32m',
            'lastCheck': datetime.now().isoformat()
        }), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500
