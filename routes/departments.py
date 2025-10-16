from flask import Blueprint, request, jsonify, render_template
import sqlite3
from datetime import datetime

departments_bp = Blueprint('departments', __name__)

# Initialize database
from models.database import Database
db = Database()

@departments_bp.route('/departments')
def departments_page():
    return render_template('departments.html')

@departments_bp.route('/api/departments', methods=['GET'])
def get_departments():
    departments = db.fetch_all('''
        SELECT id, name, email, description, created_at 
        FROM departments ORDER BY name
    ''')
    
    departments_list = []
    for dept in departments:
        departments_list.append({
            'id': dept[0],
            'name': dept[1],
            'email': dept[2],
            'description': dept[3],
            'created_at': dept[4]
        })
    
    return jsonify(departments_list)

@departments_bp.route('/api/departments', methods=['POST'])
def add_department():
    data = request.get_json()
    name = data.get('name')
    email = data.get('email')
    description = data.get('description')
    
    if not name or not email:
        return jsonify({'success': False, 'error': 'Name and email are required'})
    
    try:
        created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        db.execute_query('''
            INSERT INTO departments (name, email, description, created_at)
            VALUES (?, ?, ?, ?)
        ''', (name, email, description, created_at))
        
        return jsonify({'success': True})
    except sqlite3.IntegrityError:
        return jsonify({'success': False, 'error': 'Department name already exists'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@departments_bp.route('/api/departments/<int:dept_id>', methods=['DELETE'])
def delete_department(dept_id):
    try:
        # Check if department has assigned complaints
        assigned_complaints = db.fetch_one(
            'SELECT COUNT(*) FROM complaints WHERE assigned_department_id = ?', 
            (dept_id,)
        )
        
        if assigned_complaints and assigned_complaints[0] > 0:
            return jsonify({
                'success': False, 
                'error': 'Cannot delete department with assigned complaints'
            })
        
        db.execute_query('DELETE FROM departments WHERE id = ?', (dept_id,))
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})