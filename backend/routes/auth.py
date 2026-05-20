from flask import Blueprint, request, jsonify
import sqlite3
import hashlib
from datetime import datetime
import json

auth_bp = Blueprint('auth', __name__)

DATABASE = 'nids.db'

def hash_password(password):
    """Hash password with SHA256"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password, hashed):
    """Verify password"""
    return hash_password(password) == hashed

@auth_bp.route('/login', methods=['POST'])
def login():
    """Authenticate user"""
    try:
        data = request.json
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return jsonify({'error': 'Missing username or password'}), 400
        
        conn = sqlite3.connect(DATABASE)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Find user
        cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
        user = cursor.fetchone()
        conn.close()
        
        if not user or not verify_password(password, user['password']):
            return jsonify({'error': 'Invalid credentials'}), 401
        
        # Generate simple token (in production, use JWT)
        token = hashlib.sha256(f"{username}:{datetime.now().isoformat()}".encode()).hexdigest()
        
        return jsonify({
            'token': token,
            'user': {
                'id': user['id'],
                'username': user['username'],
                'email': user['email']
            }
        }), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/signup', methods=['POST'])
def signup():
    """Register new user"""
    try:
        data = request.json
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        
        if not all([username, email, password]):
            return jsonify({'error': 'Missing required fields'}), 400
        
        # Validate email
        if '@' not in email:
            return jsonify({'error': 'Invalid email'}), 400
        
        if len(password) < 6:
            return jsonify({'error': 'Password too short'}), 400
        
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        try:
            # Create user
            hashed_password = hash_password(password)
            cursor.execute('''
                INSERT INTO users (username, email, password)
                VALUES (?, ?, ?)
            ''', (username, email, hashed_password))
            
            conn.commit()
            
            # Get created user
            cursor.execute('SELECT id, username, email FROM users WHERE username = ?', (username,))
            user = cursor.fetchone()
            conn.close()
            
            # Generate token
            token = hashlib.sha256(f"{username}:{datetime.now().isoformat()}".encode()).hexdigest()
            
            return jsonify({
                'token': token,
                'user': {
                    'id': user[0],
                    'username': user[1],
                    'email': user[2]
                }
            }), 201
        
        except sqlite3.IntegrityError:
            conn.close()
            return jsonify({'error': 'Username or email already exists'}), 409
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/logout', methods=['POST'])
def logout():
    """Logout user"""
    return jsonify({'message': 'Logged out successfully'}), 200
