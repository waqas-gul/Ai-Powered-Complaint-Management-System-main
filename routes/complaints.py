from flask import Blueprint, request, jsonify, render_template
import joblib
import sqlite3
from datetime import datetime
import os

complaints_bp = Blueprint('complaints', __name__)

# Initialize database and email service
from models.database import Database
from models.email_service import EmailService

db = Database()
email_service = EmailService()

# Load ML model with correct paths
try:
    # Get the current directory and parent directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    
    # Construct correct paths to model files
    model_path = os.path.join(parent_dir, 'customer_classification_model_lr.pkl')
    vectorizer_path = os.path.join(parent_dir, 'tfidf_vectorizer.pkl')
    encoder_path = os.path.join(parent_dir, 'label_encoder.pkl')
    
    print(f"Looking for model files in: {parent_dir}")
    print(f"Model path: {model_path}")
    print(f"Vectorizer path: {vectorizer_path}")
    print(f"Encoder path: {encoder_path}")
    
    # Check if files exist
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model file not found: {model_path}")
    if not os.path.exists(vectorizer_path):
        raise FileNotFoundError(f"Vectorizer file not found: {vectorizer_path}")
    if not os.path.exists(encoder_path):
        raise FileNotFoundError(f"Encoder file not found: {encoder_path}")
    
    # Load models
    model = joblib.load(model_path)
    tfidf_vect = joblib.load(vectorizer_path)
    encoder = joblib.load(encoder_path)
    
    model_loaded = True
    print("✅ ML models loaded successfully!")
    print(f"Model classes: {encoder.classes_}")
    
except Exception as e:
    print(f"❌ Error loading model: {e}")
    model_loaded = False

@complaints_bp.route('/')
def home():
    return render_template('index.html')

@complaints_bp.route('/case_management')
def case_management():
    return render_template('case_management.html')

@complaints_bp.route('/predict', methods=['POST'])
def predict():
    try:
        complaint = request.form['complaint']
        print(f"🔍 Received complaint: {complaint}")
        
        if not model_loaded:
            error_msg = 'Model not loaded properly'
            print(f"❌ {error_msg}")
            return jsonify({'success': False, 'error': error_msg})
        
        # Transform and predict
        X_input = tfidf_vect.transform([complaint])
        prediction = model.predict(X_input)
        predicted_label = encoder.inverse_transform(prediction)[0]
        
        print(f"✅ Prediction successful: {predicted_label}")
        
        # Save to database
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        complaint_id = db.execute_query('''
            INSERT INTO complaints (complaint_text, predicted_category, timestamp)
            VALUES (?, ?, ?)
        ''', (complaint, predicted_label, timestamp))
        
        print(f"✅ Complaint saved to database with ID: {complaint_id}")
        
        # Get departments for dropdown
        departments = db.fetch_all('SELECT id, name FROM departments ORDER BY name')
        
        return jsonify({
            'success': True,
            'prediction_text': f"Predicted Category: {predicted_label}",
            'complaint_id': complaint_id,
            'departments': [{'id': dept[0], 'name': dept[1]} for dept in departments]
        })
        
    except Exception as e:
        error_msg = f"Error during prediction: {str(e)}"
        print(f"❌ {error_msg}")
        return jsonify({'success': False, 'error': error_msg})

# ... keep the rest of your routes the same
@complaints_bp.route('/forward_complaint', methods=['POST'])
def forward_complaint():
    data = request.get_json()
    complaint_id = data.get('complaint_id')
    department_id = data.get('department_id')
    
    try:
        # Get department details
        department = db.fetch_one(
            'SELECT name, email FROM departments WHERE id = ?', 
            (department_id,)
        )
        
        if not department:
            return jsonify({'success': False, 'error': 'Department not found'})
        
        dept_name, dept_email = department
        
        # Update complaint
        forwarded_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        db.execute_query('''
            UPDATE complaints 
            SET forwarded = TRUE, forwarded_to = ?, forwarded_at = ?, 
                assigned_department_id = ?, resolution_status = 'Assigned'
            WHERE id = ?
        ''', (dept_name, forwarded_at, department_id, complaint_id))
        
        # Get complaint details for email
        complaint = db.fetch_one(
            'SELECT complaint_text, predicted_category, timestamp FROM complaints WHERE id = ?',
            (complaint_id,)
        )
        
        # Send email
        complaint_details = {
            'id': complaint_id,
            'text': complaint[0],
            'category': complaint[1],
            'timestamp': complaint[2],
            'department': dept_name
        }
        
        email_sent = email_service.send_complaint_forward_email(dept_email, complaint_details)
        
        return jsonify({
            'success': True, 
            'forwarded_at': forwarded_at,
            'email_sent': email_sent
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@complaints_bp.route('/complete_case', methods=['POST'])
def complete_case():
    data = request.get_json()
    complaint_id = data.get('complaint_id')
    
    try:
        # Get complaint and department details
        complaint = db.fetch_one('''
            SELECT c.complaint_text, c.predicted_category, c.forwarded_to, d.email
            FROM complaints c
            LEFT JOIN departments d ON c.assigned_department_id = d.id
            WHERE c.id = ?
        ''', (complaint_id,))
        
        if not complaint:
            return jsonify({'success': False, 'error': 'Complaint not found'})
        
        # Update complaint status
        completed_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        db.execute_query('''
            UPDATE complaints 
            SET resolution_status = 'Completed', case_completed = TRUE, completed_at = ?
            WHERE id = ?
        ''', (completed_at, complaint_id))
        
        # Send completion email if department email exists
        complaint_details = {
            'id': complaint_id,
            'text': complaint[0],
            'category': complaint[1],
            'department': complaint[2],
            'completed_at': completed_at
        }
        
        email_sent = False
        if complaint[3]:  # department email
            email_sent = email_service.send_case_completion_email(complaint[3], complaint_details)
        
        return jsonify({
            'success': True, 
            'completed_at': completed_at,
            'email_sent': email_sent
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@complaints_bp.route('/api/complaints')
def get_complaints():
    complaints = db.fetch_all('''
        SELECT c.*, d.email as department_email
        FROM complaints c
        LEFT JOIN departments d ON c.assigned_department_id = d.id
        ORDER BY c.timestamp DESC
    ''')
    
    complaints_list = []
    for comp in complaints:
        complaints_list.append({
            'id': comp[0],
            'complaint_text': comp[1],
            'predicted_category': comp[2],
            'timestamp': comp[3],
            'forwarded': bool(comp[4]),
            'forwarded_to': comp[5],
            'forwarded_at': comp[6],
            'resolution_status': comp[7],
            'assigned_department_id': comp[8],
            'case_completed': bool(comp[9]),
            'completed_at': comp[10],
            'department_email': comp[11]
        })
    
    return jsonify(complaints_list)

@complaints_bp.route('/api/complaint_details/<int:complaint_id>')
def get_complaint_details(complaint_id):
    complaint = db.fetch_one('''
        SELECT c.*, d.email as department_email
        FROM complaints c
        LEFT JOIN departments d ON c.assigned_department_id = d.id
        WHERE c.id = ?
    ''', (complaint_id,))
    
    if complaint:
        complaint_details = {
            'id': complaint[0],
            'complaint_text': complaint[1],
            'predicted_category': complaint[2],
            'timestamp': complaint[3],
            'forwarded': bool(complaint[4]),
            'forwarded_to': complaint[5],
            'forwarded_at': complaint[6],
            'resolution_status': complaint[7],
            'assigned_department_id': complaint[8],
            'case_completed': bool(complaint[9]),
            'completed_at': complaint[10],
            'department_email': complaint[11]
        }
        return jsonify(complaint_details)
    else:
        return jsonify({'error': 'Complaint not found'}), 404
    

def test_prediction():
    """Test route to verify model is working"""
    try:
        test_complaint = "I have issues with my billing statement"
        X_input = tfidf_vect.transform([test_complaint])
        prediction = model.predict(X_input)
        predicted_label = encoder.inverse_transform(prediction)[0]
        
        return jsonify({
            'success': True,
            'test_complaint': test_complaint,
            'prediction': predicted_label,
            'model_loaded': model_loaded
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'model_loaded': model_loaded
        })
    


@complaints_bp.route('/delete_case', methods=['POST'])
def delete_case():
    data = request.get_json()
    complaint_id = data.get('complaint_id')
    
    try:
        # Delete the complaint from database
        db.execute_query('DELETE FROM complaints WHERE id = ?', (complaint_id,))
        
        return jsonify({'success': True, 'message': 'Case deleted successfully'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@complaints_bp.route('/update_case', methods=['POST'])
def update_case():
    data = request.get_json()
    complaint_id = data.get('complaint_id')
    department_id = data.get('department_id')
    resolution_status = data.get('resolution_status')
    
    try:
        if department_id:
            # Get department details
            department = db.fetch_one(
                'SELECT name, email FROM departments WHERE id = ?', 
                (department_id,)
            )
            
            if not department:
                return jsonify({'success': False, 'error': 'Department not found'})
            
            dept_name, dept_email = department
            
            # Update complaint with department assignment
            forwarded_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            db.execute_query('''
                UPDATE complaints 
                SET forwarded = TRUE, forwarded_to = ?, forwarded_at = ?, 
                    assigned_department_id = ?, resolution_status = ?
                WHERE id = ?
            ''', (dept_name, forwarded_at, department_id, resolution_status, complaint_id))
            
            # Get complaint details for email
            complaint = db.fetch_one(
                'SELECT complaint_text, predicted_category, timestamp FROM complaints WHERE id = ?',
                (complaint_id,)
            )
            
            # Send email only if this is a new assignment
            existing_assignment = db.fetch_one(
                'SELECT assigned_department_id FROM complaints WHERE id = ?',
                (complaint_id,)
            )
            
            if existing_assignment and existing_assignment[0] is None:
                # This is a new assignment, send email
                complaint_details = {
                    'id': complaint_id,
                    'text': complaint[0],
                    'category': complaint[1],
                    'timestamp': complaint[2],
                    'department': dept_name
                }
                email_sent = email_service.send_complaint_forward_email(dept_email, complaint_details)
            else:
                email_sent = False
            
            return jsonify({
                'success': True, 
                'forwarded_at': forwarded_at,
                'email_sent': email_sent,
                'message': 'Case updated and assigned to department successfully'
            })
        
        elif resolution_status:
            # Only update resolution status
            db.execute_query('''
                UPDATE complaints 
                SET resolution_status = ?
                WHERE id = ?
            ''', (resolution_status, complaint_id))
            
            return jsonify({
                'success': True,
                'message': 'Case status updated successfully'
            })
        else:
            return jsonify({'success': False, 'error': 'No updates provided'})
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@complaints_bp.route('/api/sla_check')
def check_sla_violations():
    """Check for SLA violations and escalate"""
    try:
        # Find complaints that are overdue
        overdue_complaints = db.fetch_all('''
            SELECT id, predicted_category, timestamp, resolution_status 
            FROM complaints 
            WHERE resolution_status IN ('Pending', 'Assigned')
            AND datetime(timestamp) < datetime('now', '-24 hours')
        ''')
        
        for complaint in overdue_complaints:
            complaint_id, category, timestamp, status = complaint
            
            # Escalate the complaint
            db.execute_query('''
                UPDATE complaints 
                SET resolution_status = 'Escalated', 
                    sla_breached = TRUE,
                    escalated_at = ?
                WHERE id = ?
            ''', (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), complaint_id))
            
            print(f"⚠️ SLA Breach: Complaint #{complaint_id} escalated")
        
        return jsonify({
            'success': True,
            'escalated_count': len(overdue_complaints)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@complaints_bp.route('/api/priority_analysis')
def priority_analysis():
    """Analyze complaints and assign priority"""
    try:
        complaints = db.fetch_all('''
            SELECT id, complaint_text, predicted_category, timestamp 
            FROM complaints 
            WHERE priority IS NULL
        ''')
        
        for complaint in complaints:
            complaint_id, text, category, timestamp = complaint
            
            # Simple priority logic (can be enhanced with ML)
            priority = 'Medium'
            text_lower = text.lower()
            
            if any(word in text_lower for word in ['urgent', 'emergency', 'critical', 'immediately']):
                priority = 'High'
            elif any(word in text_lower for word in ['not working', 'broken', 'failed', 'outage']):
                priority = 'High'
            elif category in ['Billing', 'Technical']:
                priority = 'High'
            
            db.execute_query('''
                UPDATE complaints SET priority = ? WHERE id = ?
            ''', (priority, complaint_id))
        
        return jsonify({'success': True, 'updated_count': len(complaints)})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})