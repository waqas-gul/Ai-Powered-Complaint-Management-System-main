from flask import Blueprint, jsonify, render_template
from models.database import Database
from datetime import datetime, timedelta
from collections import Counter

dashboard_bp = Blueprint('dashboard', __name__)
db = Database()

@dashboard_bp.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@dashboard_bp.route('/api/analytics')
def get_analytics():
    try:
        # Get all complaints
        complaints = db.fetch_all('''
            SELECT predicted_category, timestamp, forwarded, resolution_status, 
                   case_completed, assigned_department_id
            FROM complaints
        ''')
        
        # Get departments
        departments = db.fetch_all('SELECT id, name FROM departments')
        dept_names = {dept[0]: dept[1] for dept in departments}
        
        total_complaints = len(complaints)
        
        # Category distribution
        categories = [comp[0] for comp in complaints]
        category_counts = Counter(categories)
        
        # Forwarding status
        forwarded_count = sum(1 for comp in complaints if comp[2])
        not_forwarded_count = total_complaints - forwarded_count
        
        # Resolution status
        status_counts = Counter(comp[3] for comp in complaints)
        
        # Case completion
        completed_count = sum(1 for comp in complaints if comp[4])
        
        # Department distribution
        dept_complaints = Counter(comp[5] for comp in complaints if comp[5])
        department_stats = {dept_names.get(dept_id, 'Unknown'): count 
                          for dept_id, count in dept_complaints.items()}
        
        # Monthly trends (last 6 months)
        monthly_data = {}
        for i in range(6):
            month = datetime.now().replace(day=1) - timedelta(days=30*i)
            month_key = month.strftime("%Y-%m")
            
            count = db.fetch_one('''
                SELECT COUNT(*) FROM complaints 
                WHERE strftime('%Y-%m', timestamp) = ?
            ''', (month_key,))
            
            if count:
                monthly_data[month_key] = count[0]
            else:
                monthly_data[month_key] = 0
        
        # Response time analysis
        response_time_result = db.fetch_one('''
            SELECT AVG((julianday(forwarded_at) - julianday(timestamp)) * 24) 
            FROM complaints WHERE forwarded = TRUE AND forwarded_at IS NOT NULL
        ''')
        avg_response_hours = round(response_time_result[0], 1) if response_time_result and response_time_result[0] else 0
        
        # Today's complaints
        today = datetime.now().strftime("%Y-%m-%d")
        today_count_result = db.fetch_one('''
            SELECT COUNT(*) FROM complaints WHERE date(timestamp) = ?
        ''', (today,))
        today_count = today_count_result[0] if today_count_result else 0
        
        # Calculate days since first complaint for average
        first_complaint_result = db.fetch_one('SELECT MIN(timestamp) FROM complaints')
        if first_complaint_result and first_complaint_result[0]:
            first_date = datetime.strptime(first_complaint_result[0], '%Y-%m-%d %H:%M:%S')
            days_since_first = (datetime.now() - first_date).days
            avg_complaints_per_day = total_complaints / max(1, days_since_first)
        else:
            avg_complaints_per_day = 0
        
        analytics = {
            'total_complaints': total_complaints,
            'category_distribution': dict(category_counts),
            'forwarding_status': {
                'forwarded': forwarded_count,
                'not_forwarded': not_forwarded_count
            },
            'resolution_status': dict(status_counts),
            'completion_rate': {
                'completed': completed_count,
                'pending': total_complaints - completed_count
            },
            'monthly_trends': monthly_data,
            'department_stats': department_stats,
            'avg_response_hours': avg_response_hours,
            'today_complaints': today_count,
            'avg_complaints_per_day': round(avg_complaints_per_day, 1)
        }
        
        return jsonify(analytics)
    except Exception as e:
        print(f"Analytics error: {e}")
        return jsonify({'error': str(e)}), 500




@dashboard_bp.route('/api/kpi_metrics')
def get_kpi_metrics():
    try:
        # Total complaints
        total_complaints = db.fetch_one('SELECT COUNT(*) FROM complaints')[0]
        
        # Resolved complaints (last 30 days)
        resolved_30_days = db.fetch_one('''
            SELECT COUNT(*) FROM complaints 
            WHERE case_completed = TRUE 
            AND datetime(completed_at) > datetime('now', '-30 days')
        ''')[0]
        
        # Average resolution time
        avg_resolution = db.fetch_one('''
            SELECT AVG((julianday(completed_at) - julianday(timestamp)) * 24) 
            FROM complaints WHERE case_completed = TRUE
        ''')[0]
        
        # SLA compliance rate
        total_with_sla = db.fetch_one('''
            SELECT COUNT(*) FROM complaints 
            WHERE datetime(timestamp) < datetime('now', '-24 hours')
        ''')[0]
        
        sla_breached = db.fetch_one('''
            SELECT COUNT(*) FROM complaints WHERE sla_breached = TRUE
        ''')[0]
        
        sla_compliance = ((total_with_sla - sla_breached) / total_with_sla * 100) if total_with_sla > 0 else 100
        
        # Customer satisfaction
        avg_rating = db.fetch_one('''
            SELECT AVG(rating) FROM feedback WHERE rating IS NOT NULL
        ''')[0]
        
        metrics = {
            'total_complaints': total_complaints,
            'resolved_30_days': resolved_30_days,
            'avg_resolution_hours': round(avg_resolution, 1) if avg_resolution else 0,
            'sla_compliance_rate': round(sla_compliance, 1),
            'avg_customer_rating': round(avg_rating, 1) if avg_rating else 0,
            'escalated_cases': sla_breached
        }
        
        return jsonify(metrics)
    except Exception as e:
        return jsonify({'error': str(e)}), 500