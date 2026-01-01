import requests
import json
from datetime import datetime, timedelta
from database import StudyPlannerDB
import sqlite3

class AIStudyPlannerAgent:
    def __init__(self, api_key="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"):
        self.api_key = api_key
        self.db = StudyPlannerDB()
        self.model = "qwen/qwen3-coder:free"
    
    def calculate_study_schedule(self, subjects, exam_date_str, daily_hours, subject_difficulties=None):
        """
        Generate a personalized study schedule based on subjects, exam date, and daily hours
        """
        exam_date = datetime.strptime(exam_date_str, "%Y-%m-%d").date()
        today = datetime.now().date()
        
        # Calculate available days
        available_days = (exam_date - today).days
        if available_days <= 0:
            available_days = 1  # At least one day for planning
        
        # Set default difficulties if not provided
        if not subject_difficulties:
            subject_difficulties = {subject: "medium" for subject in subjects}
        
        # Calculate total hours needed per subject based on difficulty
        difficulty_multiplier = {
            "easy": 0.8,
            "medium": 1.0,
            "hard": 1.5
        }
        
        # Calculate total hours needed per subject
        subject_hours = {}
        for subject in subjects:
            difficulty = subject_difficulties.get(subject, "medium")
            multiplier = difficulty_multiplier.get(difficulty, 1.0)
            # Base hours assumption - can be adjusted based on subject complexity
            base_hours = 20  # Base assumption of 20 hours per subject
            subject_hours[subject] = base_hours * multiplier
        
        # Total hours needed
        total_hours_needed = sum(subject_hours.values())
        
        # Calculate if the plan is feasible
        total_available_hours = available_days * daily_hours
        
        # Adjust subject hours proportionally if needed
        if total_available_hours < total_hours_needed:
            # Scale down hours proportionally
            scaling_factor = total_available_hours / total_hours_needed
            for subject in subject_hours:
                subject_hours[subject] *= scaling_factor
        
        # Generate daily schedule
        schedule = self._generate_daily_schedule(
            subjects, 
            subject_hours, 
            available_days, 
            daily_hours, 
            today, 
            exam_date
        )
        
        return {
            "subjects": subjects,
            "exam_date": exam_date_str,
            "daily_hours": daily_hours,
            "available_days": available_days,
            "subject_hours": subject_hours,
            "total_hours_needed": total_hours_needed,
            "total_available_hours": total_available_hours,
            "schedule": schedule
        }
    
    def _generate_daily_schedule(self, subjects, subject_hours, available_days, daily_hours, start_date, exam_date):
        """
        Generate a daily schedule by distributing subject hours across available days
        """
        schedule = []
        subject_progress = {subject: 0 for subject in subjects}  # Track hours allocated per subject
        
        # Calculate daily allocation strategy
        current_date = start_date
        
        for day in range(available_days):
            day_schedule = []
            remaining_daily_hours = daily_hours
            
            # Distribute hours based on remaining subject requirements
            total_remaining_subject_hours = 0
            remaining_subjects = {}
            
            for subject in subjects:
                remaining_for_subject = subject_hours[subject] - subject_progress[subject]
                if remaining_for_subject > 0:
                    remaining_subjects[subject] = remaining_for_subject
                    total_remaining_subject_hours += remaining_for_subject
            
            if total_remaining_subject_hours == 0:
                break  # All subjects completed
            
            # Allocate hours to subjects based on their remaining needs
            for subject, remaining_hours in remaining_subjects.items():
                # Calculate proportion of remaining hours this subject needs
                proportion = remaining_hours / total_remaining_subject_hours
                allocated_hours = min(remaining_daily_hours, 
                                    round(proportion * daily_hours, 2))
                
                if allocated_hours > 0 and remaining_daily_hours >= allocated_hours:
                    day_schedule.append({
                        "date": str(current_date + timedelta(days=day)),
                        "subject": subject,
                        "hours": allocated_hours
                    })
                    subject_progress[subject] += allocated_hours
                    remaining_daily_hours -= allocated_hours
                    
                    # Break if no more daily hours available
                    if remaining_daily_hours <= 0.1:  # Account for floating point precision
                        break
            
            # Add the day's schedule to the overall schedule
            schedule.extend(day_schedule)
        
        return schedule
    
    def adjust_schedule_after_missed_day(self, plan_id, missed_date):
        """
        Adjust the remaining schedule when a day is marked as missed
        """
        # Get the original plan details
        plan_details = self.db.get_study_plan(plan_id)
        if not plan_details:
            return None
        
        # Extract plan information
        _, user_id, subject, exam_date, daily_hours, difficulty, total_hours, completed_hours, status, _ = plan_details
        
        # Get all remaining schedule items after the missed date
        all_schedule = self.db.get_daily_schedule(plan_id)
        
        # Find the missed day and mark it
        missed_schedule_id = None
        for schedule_item in all_schedule:
            id, plan_id_db, study_date, subject, planned_hours, actual_hours, completed, missed, notes, created_at = schedule_item
            if str(study_date) == str(missed_date) and not missed:
                self.db.mark_day_missed(id)
                missed_schedule_id = id
                break
        
        if not missed_schedule_id:
            return None  # Day was not found or already marked as missed
        
        # Get all remaining days after the missed date
        remaining_schedule = []
        for item in all_schedule:
            id, plan_id_db, study_date, subject, planned_hours, actual_hours, completed, missed, notes, created_at = item
            if datetime.strptime(str(study_date), "%Y-%m-%d").date() > datetime.strptime(str(missed_date), "%Y-%m-%d").date():
                remaining_schedule.append(item)
        
        # Rebalance the remaining schedule
        return self._rebalance_remaining_schedule(plan_id, remaining_schedule, daily_hours)
    
    def _rebalance_remaining_schedule(self, plan_id, remaining_schedule, daily_hours):
        """
        Rebalance the remaining schedule after a missed day
        """
        # Calculate total remaining hours to be redistributed
        total_remaining_hours = 0
        for item in remaining_schedule:
            id, plan_id_db, study_date, subject, planned_hours, actual_hours, completed, missed, notes, created_at = item
            total_remaining_hours += planned_hours
        
        # Get the remaining days
        remaining_days = len(remaining_schedule)
        if remaining_days == 0:
            return None
        
        # Calculate new daily allocation
        new_daily_hours = total_remaining_hours / remaining_days
        
        # Update the schedule with new allocations
        updated_schedule = []
        for item in remaining_schedule:
            id, plan_id_db, study_date, subject, planned_hours, actual_hours, completed, missed, notes, created_at = item
            
            # Distribute based on subject priority/difficulty
            updated_item = {
                "id": id,
                "date": study_date,
                "subject": subject,
                "original_hours": planned_hours,
                "new_hours": round(new_daily_hours, 2)
            }
            updated_schedule.append(updated_item)
            
            # Update the database with new hours
            conn = sqlite3.connect(self.db.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE daily_schedule 
                SET planned_hours = ?
                WHERE id = ?
            ''', (round(new_daily_hours, 2), id))
            conn.commit()
            conn.close()
        
        return updated_schedule
    
    def generate_motivational_tip(self, subject, progress_percentage):
        """
        Generate a motivational tip using AI based on subject and progress
        """
        prompt = f"""
        Generate a motivational tip for a student studying {subject}. 
        The student has completed {progress_percentage}% of their study plan. 
        Keep the tip encouraging, actionable, and under 100 words.
        """
        
        try:
            response = requests.post(
                url="https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "http://localhost:8501",  # Local Streamlit app
                    "X-Title": "AI Study Planner Agent"
                },
                data=json.dumps({
                    "model": self.model,
                    "messages": [
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ]
                })
            )
            
            if response.status_code == 200:
                result = response.json()
                tip = result['choices'][0]['message']['content'].strip()
                return tip
            else:
                return "Keep going! Consistency is key to success. You're making progress every day you study."
        except Exception as e:
            print(f"Error generating motivational tip: {e}")
            return "Stay focused and keep moving forward. Every small step counts towards your success!"
    
    def generate_study_advice(self, subject, difficulty, remaining_days, hours_left):
        """
        Generate personalized study advice for a specific subject
        """
        prompt = f"""
        Provide personalized study advice for {subject} which is marked as {difficulty} difficulty.
        The exam is in {remaining_days} days and there are {hours_left} hours left to study for this subject.
        Give specific, actionable tips for effective studying in 100 words or less.
        """
        
        try:
            response = requests.post(
                url="https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "http://localhost:8501",
                    "X-Title": "AI Study Planner Agent"
                },
                data=json.dumps({
                    "model": self.model,
                    "messages": [
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ]
                })
            )
            
            if response.status_code == 200:
                result = response.json()
                advice = result['choices'][0]['message']['content'].strip()
                return advice
            else:
                return f"Focus on the most important topics for {subject}. Practice problems and review key concepts daily."
        except Exception as e:
            print(f"Error generating study advice: {e}")
            return f"Review key concepts for {subject} and practice problems daily to improve your understanding."