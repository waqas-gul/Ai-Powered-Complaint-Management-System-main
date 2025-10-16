import sqlite3
from datetime import datetime

class Database:
    def __init__(self, db_path='complaints.db'):
        self.db_path = db_path
        self.init_db()

    def init_db(self):
        conn = self.get_connection()
        c = conn.cursor()
        
        # Users table
        c.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                role TEXT DEFAULT 'customer',
                created_at TEXT NOT NULL,
                is_active BOOLEAN DEFAULT TRUE
            )
        ''')
        
        # Enhanced complaints table
        c.execute('''
            CREATE TABLE IF NOT EXISTS complaints (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                complaint_text TEXT NOT NULL,
                predicted_category TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                forwarded BOOLEAN DEFAULT FALSE,
                forwarded_to TEXT,
                forwarded_at TEXT,
                resolution_status TEXT DEFAULT "Pending",
                assigned_department_id INTEGER,
                case_completed BOOLEAN DEFAULT FALSE,
                completed_at TEXT,
                priority TEXT DEFAULT 'Medium',
                sla_breached BOOLEAN DEFAULT FALSE,
                escalated_at TEXT,
                customer_id INTEGER,
                feedback_provided BOOLEAN DEFAULT FALSE,
                FOREIGN KEY (assigned_department_id) REFERENCES departments (id),
                FOREIGN KEY (customer_id) REFERENCES users (id)
            )
        ''')
        
        # Feedback table
        c.execute('''
            CREATE TABLE IF NOT EXISTS feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                complaint_id INTEGER NOT NULL,
                rating INTEGER CHECK (rating >= 1 AND rating <= 5),
                comments TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (complaint_id) REFERENCES complaints (id)
            )
        ''')
        
        # Internal notes table
        c.execute('''
            CREATE TABLE IF NOT EXISTS case_notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                complaint_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                note_text TEXT NOT NULL,
                created_at TEXT NOT NULL,
                is_internal BOOLEAN DEFAULT TRUE,
                FOREIGN KEY (complaint_id) REFERENCES complaints (id),
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        conn.commit()
        conn.close()

    def get_connection(self):
        return sqlite3.connect(self.db_path)

    def execute_query(self, query, params=()):
        conn = self.get_connection()
        c = conn.cursor()
        c.execute(query, params)
        conn.commit()
        result = c.lastrowid
        conn.close()
        return result

    def fetch_all(self, query, params=()):
        conn = self.get_connection()
        c = conn.cursor()
        c.execute(query, params)
        result = c.fetchall()
        conn.close()
        return result

    def fetch_one(self, query, params=()):
        conn = self.get_connection()
        c = conn.cursor()
        c.execute(query, params)
        result = c.fetchone()
        conn.close()
        return result
    
    