# 🌙 Morpheus

> Personal AI Journaling Application

Morpheus helps you journal daily and uses AI to automatically evaluate your schedule compliance and rule adherence.

## Quick Start

```bash
# 1. Create a virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS / Linux

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
copy .env.example .env       # then edit .env as needed

# 4. Run the development server
uvicorn app.main:app --reload
```

Open [http://localhost:8000](http://localhost:8000) to view the homepage.

## Project Structure

```
Morpheus/
├── app/
│   ├── main.py            # FastAPI app factory & startup
│   ├── config/
│   │   └── settings.py    # Environment-based configuration
│   ├── database/
│   │   ├── base.py        # SQLAlchemy declarative Base
│   │   └── engine.py      # Engine, session factory, init_db()
│   ├── models/            # ORM model classes (one file per table)
│   ├── schemas/           # Pydantic request/response schemas
│   ├── services/          # Business logic layer
│   ├── routes/            # API & page route modules
│   ├── templates/         # Jinja2 HTML templates
│   └── static/css/        # Stylesheets
├── .env                   # Local environment variables (not committed)
├── .env.example           # Template for .env
├── requirements.txt       # Python dependencies
└── README.md
```

## Tech Stack

| Layer        | Technology          |
|--------------|---------------------|
| Framework    | FastAPI             |
| ORM          | SQLAlchemy 2.x      |
| Database     | SQLite              |
| Templates    | Jinja2              |
| Config       | pydantic-settings   |
| Server       | Uvicorn             |
| AI (planned) | Gemini API          |
