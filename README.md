# AI Study Planner Agent

This project implements an AI-powered student productivity agent that creates personalized study timetables and adjusts schedules based on user progress.

## Features

- Input subjects, exam date, and daily study hours
- AI-generated personalized study timetable based on subject difficulty
- Automatic schedule adjustment when days are missed
- Daily plan view with completion tracking
- Progress tracking with visualization
- AI-generated motivational tips and study advice

## Architecture

- `database.py` - SQLite database logic for storing plans and progress
- `planner_agent.py` - AI and rule-based logic for generating and adjusting schedules
- `app.py` - Streamlit UI for user interaction

## Installation

1. Install dependencies: `pip install -r requirements.txt`
2. Run the application: `streamlit run app.py`

## Agent Logic

### Study Plan Generation

The AI agent generates personalized study schedules by:
1. Calculating available days until the exam
2. Assigning difficulty levels to subjects (easy, medium, hard)
3. Estimating required hours per subject based on difficulty
4. Distributing study hours across available days proportionally

### Adaptive Scheduling

When a day is marked as missed, the agent:
1. Identifies remaining scheduled days
2. Calculates total remaining hours to be redistributed
3. Rebalances the schedule across remaining days
4. Updates the database with new allocations

### AI-Powered Features

- **Motivational Tips**: Generated using OpenRouter API with Qwen3-Coder model based on subject and progress percentage
- **Study Advice**: Personalized recommendations based on subject difficulty, remaining days, and hours left

### API Integration

The application uses OpenRouter API with the following configuration:
- Model: `qwen/qwen3-coder:free`
- API Key: `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`
- Referer: `http://localhost:8501` (for local Streamlit app)

The AI features are used for generating motivational content and personalized study advice based on the user's current progress and goals.