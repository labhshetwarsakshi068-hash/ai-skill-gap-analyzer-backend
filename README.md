# AI Skill Gap Analyzer – Backend

## Project Overview

The backend of the AI-Based Skill Gap Analyzer and Personalized Career Recommendation System. It provides REST APIs for user authentication, resume processing, skill gap analysis, learning roadmaps, and AI-based career recommendations.

## Features

- User registration and login
- Resume upload and skill extraction
- Skill gap analysis based on target job roles
- Personalized learning roadmap
- AI-based career recommendations
- MySQL database integration

## Tech Stack

- Python
- Flask
- MySQL
- REST API
- Google Gemini API (if enabled in the project configuration)
- Gunicorn for deployment

## Project Structure

```text
backend/
├── app.py
├── db.py
├── ai_recommender.py
├── skill_extractor.py
├── requirements.txt
└── README.md
```

## Setup Instructions

### 1. Clone the Repository

```bash
git clone YOUR_BACKEND_REPOSITORY_URL
cd YOUR_BACKEND_REPOSITORY_FOLDER
```

Replace the placeholders with the actual repository URL and folder name.

### 2. Create a Virtual Environment

```bash
python -m venv venv
```

Activate it on Windows PowerShell:

```powershell
.\venv\Scripts\Activate.ps1
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Configure the required database connection details, API keys, and other settings using environment variables or the deployment platform's secret settings.

Do not commit `.env` files, passwords, or API keys to GitHub.

### 5. Run the Backend

Check `app.py` for the application's startup configuration, then run:

```bash
python app.py
```

The API address and port depend on the local configuration.

## Frontend Integration

The Streamlit frontend communicates with this backend through REST API endpoints. Configure the frontend API URL to match the running backend.

## Security

Keep credentials private and use environment variables for sensitive configuration.
