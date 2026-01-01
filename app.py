import streamlit as st
from datetime import datetime, timedelta
from database import StudyPlannerDB
from planner_agent import AIStudyPlannerAgent

# Initialize session state
if 'user_id' not in st.session_state:
    db = StudyPlannerDB()
    st.session_state.user_id = db.create_user()

if 'current_plan_id' not in st.session_state:
    st.session_state.current_plan_id = None

if 'show_schedule' not in st.session_state:
    st.session_state.show_schedule = False

if 'show_daily_plan' not in st.session_state:
    st.session_state.show_daily_plan = False

# App title
st.title("🧠 AI Study Planner Agent")

# Initialize database and agent
db = StudyPlannerDB()
agent = AIStudyPlannerAgent()

# Sidebar for navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["Home", "Create Plan", "View Schedule", "Daily Plan", "Progress Tracking"])

if page == "Home":
    st.header("Welcome to AI Study Planner Agent!")
    st.write("""
    This AI-powered agent helps you create personalized study timetables and adjust your schedule based on your progress.
    
    Features:
    - Personalized study plans based on subjects, exam date, and daily availability
    - Automatic schedule adjustment when days are missed
    - Progress tracking and visualization
    - AI-generated motivational tips
    """)
    
    # Show existing plans
    plans = db.get_all_study_plans(st.session_state.user_id)
    if plans:
        st.subheader("Your Study Plans")
        for plan in plans:
            plan_id, user_id, subject, exam_date, daily_hours, difficulty, total_hours, completed_hours, status, created_at = plan
            progress = (completed_hours / total_hours * 100) if total_hours and total_hours > 0 else 0
            st.write(f"**{subject}** - Exam: {exam_date} | Daily: {daily_hours}h | Progress: {progress:.1f}%")
            col1, col2 = st.columns(2)
            with col1:
                if st.button(f"View Plan #{plan_id}", key=f"view_{plan_id}"):
                    st.session_state.current_plan_id = plan_id
                    st.session_state.show_schedule = True
            with col2:
                if st.button(f"Daily Plan", key=f"daily_{plan_id}"):
                    st.session_state.current_plan_id = plan_id
                    st.session_state.show_daily_plan = True

elif page == "Create Plan":
    st.header("Create Your Study Plan")
    
    # Input form
    with st.form("study_plan_form"):
        subjects_input = st.text_input("Subjects (comma separated)", "Math, Physics, Chemistry")
        exam_date = st.date_input("Exam Date", value=datetime.today() + timedelta(days=30))
        daily_hours = st.slider("Daily Study Hours", min_value=1, max_value=12, value=4)
        difficulty_input = st.text_input("Subject Difficulties (comma separated, options: easy, medium, hard)", "medium, medium, medium")
        
        submitted = st.form_submit_button("Generate Study Plan")
    
    if submitted:
        subjects = [s.strip() for s in subjects_input.split(',')]
        difficulties = [d.strip() for d in difficulty_input.split(',')]
        
        # Map difficulties to subjects
        subject_difficulties = {}
        for i, subject in enumerate(subjects):
            if i < len(difficulties):
                subject_difficulties[subject] = difficulties[i]
            else:
                subject_difficulties[subject] = "medium"  # default
        
        # Generate the study plan
        plan_data = agent.calculate_study_schedule(
            subjects=subjects,
            exam_date_str=exam_date.strftime("%Y-%m-%d"),
            daily_hours=daily_hours,
            subject_difficulties=subject_difficulties
        )
        
        # Save the plan to database
        for subject in subjects:
            plan_id = db.create_study_plan(
                user_id=st.session_state.user_id,
                subject=subject,
                exam_date=exam_date.strftime("%Y-%m-%d"),
                daily_hours=daily_hours,
                difficulty=subject_difficulties[subject],
                total_hours=plan_data['subject_hours'][subject]
            )
            
            # Create daily schedule entries
            for sched_item in plan_data['schedule']:
                if sched_item['subject'] == subject:
                    db.create_daily_schedule(
                        plan_id=plan_id,
                        study_date=sched_item['date'],
                        subject=sched_item['subject'],
                        planned_hours=sched_item['hours']
                    )
        
        st.success("Study plan created successfully!")
        st.session_state.current_plan_id = plan_id  # Just set to last created plan ID
        st.rerun()

elif page == "View Schedule":
    st.header("Your Study Schedule")
    
    if st.session_state.current_plan_id:
        plan = db.get_study_plan(st.session_state.current_plan_id)
        if plan:
            plan_id, user_id, subject, exam_date, daily_hours, difficulty, total_hours, completed_hours, status, created_at = plan
            
            st.subheader(f"Subject: {subject}")
            st.write(f"**Exam Date:** {exam_date}")
            st.write(f"**Daily Hours:** {daily_hours}h")
            st.write(f"**Difficulty:** {difficulty}")
            
            # Calculate and show progress
            progress = (completed_hours / total_hours * 100) if total_hours and total_hours > 0 else 0
            st.write(f"**Progress:** {progress:.1f}% ({completed_hours:.1f} of {total_hours:.1f} hours completed)")
            st.progress(progress / 100)
            
            # Show daily schedule
            schedule = db.get_daily_schedule(st.session_state.current_plan_id)
            if schedule:
                st.subheader("Daily Schedule")
                
                # Create a dataframe for better display
                import pandas as pd
                schedule_data = []
                for item in schedule:
                    id, plan_id, study_date, subj, planned_hours, actual_hours, completed, missed, notes, created_at = item
                    status = "✅ Completed" if completed else ("❌ Missed" if missed else "📅 Scheduled")
                    schedule_data.append({
                        "Date": study_date,
                        "Subject": subj,
                        "Planned Hours": planned_hours,
                        "Actual Hours": actual_hours,
                        "Status": status
                    })
                
                df = pd.DataFrame(schedule_data)
                st.dataframe(df, use_container_width=True)
                
                # Option to mark a day as missed
                st.subheader("Mark Day as Missed")
                dates = [item[2] for item in schedule if not item[6] and not item[7]]  # Not completed and not missed
                if dates:
                    selected_date = st.selectbox("Select date to mark as missed", dates)
                    if st.button("Mark as Missed"):
                        # Find the schedule ID for the selected date
                        for item in schedule:
                            id, plan_id, study_date, subj, planned_hours, actual_hours, completed, missed, notes, created_at = item
                            if str(study_date) == str(selected_date) and not completed and not missed:
                                # Mark as missed
                                db.mark_day_missed(id)
                                
                                # Adjust the schedule
                                adjusted_schedule = agent.adjust_schedule_after_missed_day(st.session_state.current_plan_id, selected_date)
                                
                                st.success(f"Day {selected_date} marked as missed. Schedule has been adjusted.")
                                if adjusted_schedule:
                                    st.write("Schedule has been rebalanced for remaining days.")
                                st.rerun()
                else:
                    st.info("No upcoming days to mark as missed.")
            else:
                st.info("No schedule created yet. Create a plan first.")
        else:
            st.error("Plan not found.")
    else:
        st.info("Select a plan from the home page or create a new one.")

elif page == "Daily Plan":
    st.header("Daily Study Plan")
    
    if st.session_state.current_plan_id:
        plan = db.get_study_plan(st.session_state.current_plan_id)
        if plan:
            plan_id, user_id, subject, exam_date, daily_hours, difficulty, total_hours, completed_hours, status, created_at = plan
            
            # Get today's schedule
            today = datetime.now().date()
            schedule = db.get_daily_schedule(st.session_state.current_plan_id, str(today))
            
            if schedule:
                st.subheader(f"Today's Plan ({today}) - {subject}")
                
                for item in schedule:
                    id, plan_id, study_date, subj, planned_hours, actual_hours, completed, missed, notes, created_at = item
                    
                    if str(study_date) == str(today):
                        if missed:
                            st.error(f"❌ You missed studying {subj} for {planned_hours} hours today.")
                        elif completed:
                            st.success(f"✅ Completed {subj} for {actual_hours} hours (planned: {planned_hours}h)")
                        else:
                            st.info(f"📚 Study {subj} for {planned_hours} hours today")
                            
                            # Mark as completed
                            actual_hours_input = st.number_input(
                                f"Hours actually studied for {subj}", 
                                min_value=0.0, 
                                max_value=planned_hours*2, 
                                value=0.0,
                                step=0.5,
                                key=f"actual_{id}"
                            )
                            
                            if st.button(f"Mark as Completed", key=f"complete_{id}"):
                                db.mark_day_completed(id, actual_hours_input)
                                db.update_progress(plan_id, str(today), subj, actual_hours_input)
                                st.success("Day marked as completed!")
                                st.rerun()
                
                # Show motivational tip
                progress = (completed_hours / total_hours * 100) if total_hours and total_hours > 0 else 0
                if progress > 0:
                    tip = agent.generate_motivational_tip(subject, progress)
                    st.subheader("💡 Motivational Tip")
                    st.write(tip)
                
                # Show study advice
                remaining_days = (datetime.strptime(exam_date, "%Y-%m-%d").date() - today).days
                hours_left = total_hours - completed_hours
                if remaining_days > 0 and hours_left > 0:
                    advice = agent.generate_study_advice(subject, difficulty, remaining_days, hours_left)
                    st.subheader("📖 Study Advice")
                    st.write(advice)
            else:
                st.info(f"No schedule for today ({today}). The exam is on {exam_date}.")
        else:
            st.error("Plan not found.")
    else:
        st.info("Select a plan from the home page or create a new one.")

elif page == "Progress Tracking":
    st.header("Progress Tracking")
    
    if st.session_state.current_plan_id:
        plan = db.get_study_plan(st.session_state.current_plan_id)
        if plan:
            plan_id, user_id, subject, exam_date, daily_hours, difficulty, total_hours, completed_hours, status, created_at = plan
            
            st.subheader(f"Progress for {subject}")
            st.write(f"**Exam Date:** {exam_date}")
            
            # Show progress
            progress = (completed_hours / total_hours * 100) if total_hours and total_hours > 0 else 0
            st.write(f"**Overall Progress:** {progress:.1f}% ({completed_hours:.1f} of {total_hours:.1f} hours completed)")
            st.progress(progress / 100)
            
            # Show progress over time
            progress_data = db.get_progress(st.session_state.current_plan_id)
            if progress_data:
                import pandas as pd
                import matplotlib.pyplot as plt
                
                dates = []
                cumulative_hours = []
                running_total = 0
                
                for item in progress_data:
                    id, plan_id, date, subj, hours_completed, notes, created_at = item
                    running_total += hours_completed
                    dates.append(date)
                    cumulative_hours.append(running_total)
                
                # Create a dataframe
                df = pd.DataFrame({
                    'Date': pd.to_datetime(dates),
                    'Cumulative Hours': cumulative_hours
                })
                
                # Plot the progress
                st.line_chart(df.set_index('Date'))
                
                # Show progress details
                st.subheader("Daily Progress")
                progress_df = pd.DataFrame(progress_data, columns=['ID', 'Plan ID', 'Date', 'Subject', 'Hours Completed', 'Notes', 'Created At'])
                st.dataframe(progress_df[['Date', 'Subject', 'Hours Completed', 'Notes']])
            else:
                st.info("No progress data yet. Start studying to track your progress!")
        else:
            st.error("Plan not found.")
    else:
        st.info("Select a plan from the home page or create a new one.")