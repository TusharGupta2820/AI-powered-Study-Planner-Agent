import sqlite3
from datetime import datetime, timedelta
import os

class StudyPlannerDB:
    def __init__(self, db_path="study_planner.db"):
        self.db_path = db_path
        self.init_db()
    
    def init_db(self):
        """Initialize the database with required tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create study_plans table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS study_plans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                subject TEXT NOT NULL,
                exam_date DATE NOT NULL,
                daily_hours REAL NOT NULL,
                difficulty TEXT DEFAULT 'medium',
                total_hours REAL,
                completed_hours REAL DEFAULT 0,
                status TEXT DEFAULT 'active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Create daily_schedule table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS daily_schedule (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                plan_id INTEGER,
                study_date DATE NOT NULL,
                subject TEXT NOT NULL,
                planned_hours REAL NOT NULL,
                actual_hours REAL DEFAULT 0,
                completed BOOLEAN DEFAULT FALSE,
                missed BOOLEAN DEFAULT FALSE,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (plan_id) REFERENCES study_plans (id)
            )
        ''')
        
        # Create progress_tracking table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS progress_tracking (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                plan_id INTEGER,
                date DATE NOT NULL,
                subject TEXT NOT NULL,
                hours_completed REAL DEFAULT 0,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (plan_id) REFERENCES study_plans (id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def create_user(self):
        """Create a new user"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users DEFAULT VALUES")
        user_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return user_id
    
    def create_study_plan(self, user_id, subject, exam_date, daily_hours, difficulty='medium', total_hours=None):
        """Create a new study plan"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO study_plans 
            (user_id, subject, exam_date, daily_hours, difficulty, total_hours)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_id, subject, exam_date, daily_hours, difficulty, total_hours))
        
        plan_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return plan_id
    
    def get_study_plan(self, plan_id):
        """Get a specific study plan"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM study_plans WHERE id = ?
        ''', (plan_id,))
        
        result = cursor.fetchone()
        conn.close()
        return result
    
    def get_all_study_plans(self, user_id):
        """Get all study plans for a user"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM study_plans WHERE user_id = ? AND status = 'active'
        ''', (user_id,))
        
        results = cursor.fetchall()
        conn.close()
        return results
    
    def create_daily_schedule(self, plan_id, study_date, subject, planned_hours):
        """Create a daily schedule entry"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO daily_schedule 
            (plan_id, study_date, subject, planned_hours)
            VALUES (?, ?, ?, ?)
        ''', (plan_id, study_date, subject, planned_hours))
        
        schedule_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return schedule_id
    
    def get_daily_schedule(self, plan_id, date=None):
        """Get daily schedule for a plan, optionally filtered by date"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if date:
            cursor.execute('''
                SELECT * FROM daily_schedule 
                WHERE plan_id = ? AND study_date = ?
                ORDER BY study_date
            ''', (plan_id, date))
        else:
            cursor.execute('''
                SELECT * FROM daily_schedule 
                WHERE plan_id = ? 
                ORDER BY study_date
            ''', (plan_id,))
        
        results = cursor.fetchall()
        conn.close()
        return results
    
    def mark_day_missed(self, schedule_id):
        """Mark a day as missed"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE daily_schedule 
            SET missed = TRUE 
            WHERE id = ?
        ''', (schedule_id,))
        
        conn.commit()
        conn.close()
    
    def mark_day_completed(self, schedule_id, actual_hours=0):
        """Mark a day as completed"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE daily_schedule 
            SET completed = TRUE, actual_hours = ?
            WHERE id = ?
        ''', (actual_hours, schedule_id))
        
        conn.commit()
        conn.close()
    
    def update_progress(self, plan_id, date, subject, hours_completed, notes=None):
        """Update progress tracking"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO progress_tracking 
            (plan_id, date, subject, hours_completed, notes)
            VALUES (?, ?, ?, ?, ?)
        ''', (plan_id, date, subject, hours_completed, notes))
        
        conn.commit()
        conn.close()
    
    def get_progress(self, plan_id):
        """Get progress for a study plan"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM progress_tracking 
            WHERE plan_id = ?
            ORDER BY date
        ''', (plan_id,))
        
        results = cursor.fetchall()
        conn.close()
        return results
    
    def get_completed_hours(self, plan_id):
        """Get total completed hours for a plan"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT SUM(hours_completed) FROM progress_tracking 
            WHERE plan_id = ?
        ''', (plan_id,))
        
        result = cursor.fetchone()[0]
        conn.close()
        return result or 0
    
    def update_plan_status(self, plan_id, status):
        """Update the status of a study plan"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE study_plans 
            SET status = ? 
            WHERE id = ?
        ''', (status, plan_id))
        
        conn.commit()
        conn.close()