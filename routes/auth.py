from flask import Blueprint, request, jsonify, session
from models.database import Database
import hashlib
import secrets
from datetime import datetime, timedelta

auth_bp = Blueprint('auth', __name__)
db = Database()

# User roles
USER_ROLES = {
    'admin': ['view', 'create', 'edit', 'delete', 'manage_users'],
    'manager': ['view', 'create', 'edit'],
    'agent': ['view', 'edit_assigned'],
    'customer': ['view_own', 'create']
}

@auth_bp.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    role = data.get('role', 'customer')
    
    if not all([username, email, password]):
        return jsonify({'success': False, 'error': 'All fields are required'})
    
    try:
        # Hash password
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        db.execute_query('''
            INSERT INTO users (username, email, password, role, created_at)
            VALUES (?, ?, ?, ?, ?)
        ''', (username, email, hashed_password, role, created_at))
        
        return jsonify({'success': True, 'message': 'User registered successfully'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@auth_bp.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'success': False, 'error': 'Username and password required'})
    
    try:
        # Hash the password
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        
        user = db.fetch_one(
            'SELECT id, username, email, role FROM users WHERE username = ? AND password = ?',
            (username, hashed_password)
        )
        
        if user:
            # Create session
            session_token = secrets.token_hex(16)
            session[session_token] = {
                'user_id': user[0],
                'username': user[1],
                'email': user[2],
                'role': user[3],
                'login_time': datetime.now().isoformat()
            }
            
            return jsonify({
                'success': True,
                'token': session_token,
                'user': {
                    'id': user[0],
                    'username': user[1],
                    'email': user[2],
                    'role': user[3]
                }
            })
        else:
            return jsonify({'success': False, 'error': 'Invalid credentials'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})