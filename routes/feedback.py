from flask import Blueprint, request, jsonify
from models.database import Database
from datetime import datetime

feedback_bp = Blueprint('feedback', __name__)
db = Database()

@feedback_bp.route('/api/feedback', methods=['POST'])
def submit_feedback():
    data = request.get_json()
    complaint_id = data.get('complaint_id')
    rating = data.get('rating')
    comments = data.get('comments')
    
    try:
        created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        db.execute_query('''
            INSERT INTO feedback (complaint_id, rating, comments, created_at)
            VALUES (?, ?, ?, ?)
        ''', (complaint_id, rating, comments, created_at))
        
        # Update complaint with feedback status
        db.execute_query('''
            UPDATE complaints SET feedback_provided = TRUE WHERE id = ?
        ''', (complaint_id,))
        
        return jsonify({'success': True, 'message': 'Feedback submitted successfully'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@feedback_bp.route('/api/feedback/<int:complaint_id>')
def get_feedback(complaint_id):
    try:
        feedback = db.fetch_one(
            'SELECT rating, comments, created_at FROM feedback WHERE complaint_id = ?',
            (complaint_id,)
        )
        
        if feedback:
            return jsonify({
                'success': True,
                'feedback': {
                    'rating': feedback[0],
                    'comments': feedback[1],
                    'created_at': feedback[2]
                }
            })
        else:
            return jsonify({'success': False, 'error': 'No feedback found'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})