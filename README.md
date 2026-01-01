# AI-powered-Study-Planner-Agent
📚 AI Study Planner Agent

An AI-powered Study Planner Agent that creates a personalized study timetable for students based on subjects, exam date, and daily study hours.
The agent dynamically adjusts schedules if a student misses a day and provides AI-generated motivational tips to improve consistency.

This project demonstrates Agentic AI behavior using perception, reasoning, memory, and action.

🚀 What This Project Does

✔ Generates a personalized study timetable
✔ Considers subject difficulty and available time
✔ Stores study plans in SQLite
✔ Automatically rebalances the plan if a day is missed
✔ Tracks progress day-by-day
✔ Displays daily study plans
✔ Provides AI-generated motivational tips

🤖 Agentic AI Behavior

The AI Study Planner functions as an intelligent student productivity agent:

1️⃣ Perception

Takes user input:

Subjects

Exam date

Daily study hours

Tracks completed and missed study days

2️⃣ Reasoning

Uses AI + rule-based logic to:

Distribute study time based on subject difficulty

Adjust the schedule if a day is missed

Rebalance remaining days intelligently

3️⃣ Memory

Stores study plan and progress in SQLite

Remembers completed and pending sessions

4️⃣ Action

Updates daily plan

Displays revised timetable

Generates motivational messages

🛠 Tech Stack

Python 3.10+

Streamlit – UI

SQLite – Data storage

LLM API (OpenAI / compatible) – Planning & motivation

dotenv – Environment variable management

📁 Project Structure
ai-study-planner-agent/
│
├── app.py               # Streamlit UI
├── planner_agent.py     # AI + scheduling logic
├── database.py          # SQLite operations
├── requirements.txt
├── .env                 # API keys (not committed)
├── study_plan.db        # SQLite database
└── README.md

📌 Features

✅ Subject-wise timetable generation

✅ AI-based difficulty balancing

✅ Daily study plan view

✅ Missed-day auto adjustment

✅ Progress tracking

✅ AI motivational tips

✅ Persistent storage with SQLite

🔑 Prerequisites

Python 3.10 or higher

LLM API key (OpenAI / compatible)

Git (optional)

⚙️ Setup Instructions
1️⃣ Clone the Repository
git clone https://github.com/your-username/ai-study-planner-agent.git
cd ai-study-planner-agent

2️⃣ Create Virtual Environment
python -m venv venv


Activate it:

Windows

venv\Scripts\activate


Linux / Mac

source venv/bin/activate

3️⃣ Install Dependencies
pip install -r requirements.txt

4️⃣ Set Environment Variables

Create a .env file in the project root:

OPENAI_API_KEY=your_api_key_here


⚠️ Never commit API keys to GitHub

5️⃣ Run the Application
streamlit run app.py


Open in browser:

http://localhost:8501

🧠 How the AI Planner Works
📌 Study Plan Generation

Calculates total available study days

Distributes time based on:

Subject difficulty

Remaining exam days

Daily study hours

📌 Missed Day Handling

Detects missed sessions

Redistributes remaining workload

Updates future timetable dynamically

📌 Motivation Engine

Generates daily motivational tips

Encourages consistency and focus

🖥 Example Workflow

User enters:

Subjects: Math, Physics, Chemistry

Exam Date: 30 days away

Daily Study Hours: 4

AI generates a personalized plan

User marks Day 5 as missed

AI rebalances remaining days automatically

Updated plan is displayed instantly

📊 Database Schema (SQLite)
study_plan Table
Column	Type
id	INTEGER (Primary Key)
date	TEXT
subject	TEXT
hours	INTEGER
status	TEXT
🔮 Future Enhancements

🔔 Smart reminders & notifications

📱 Mobile-friendly UI

📊 Visual progress charts

🎤 Voice input support

🐳 Docker deployment

☁️ Cloud database integration
