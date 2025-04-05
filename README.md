# Family Todo Organizer

A web application to help families organize cleaning tasks, assign them to family members, and track points earned.

## Features

- Create and manage family members
- Add tasks grouped by rooms
- Assign tasks to specific family members
- Track completion status
- Points system for completed tasks
- Clean and intuitive user interface

## Setup

1. Create a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the application:
```bash
python app.py
```

4. Open your browser and navigate to `http://localhost:5000`

## Usage

1. Add family members using the "Add Family Member" form
2. Create tasks by specifying:
   - Task title
   - Room
   - Points value
   - Assignee (optional)
3. View tasks organized by room
4. Mark tasks as complete to award points
5. Track family members' points in the leaderboard

## Technologies Used

- Python
- Flask
- SQLAlchemy
- Bootstrap 5
- SQLite 