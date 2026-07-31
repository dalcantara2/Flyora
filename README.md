# Flyora ✈️

A flight booking web application built with Python, Flask, and SQLite.  
Final project for [University Name] — [Course Name].

---

## Features

- Search for flights by departure city, destination, and date
- Book a selected flight and receive a booking confirmation
- Look up an existing booking using a booking reference
- **Smart Travel Assistant** — generates a personalised travel checklist after booking based on trip purpose, destination, and flight duration

---

## Project Structure

```
SkyRoute/                   ← internal project folder (unchanged)
├── app.py           # Flask app, all routes
├── config.py        # Configuration (DB path, secret key)
├── database.py      # DB connection, schema creation, seed data
├── checklist.py     # Smart Travel Assistant logic
├── database/        # SQLite database file (auto-created)
├── templates/       # Jinja2 HTML templates
├── static/          # CSS, JavaScript, images
├── requirements.txt
└── README.md
```

---

## Local Setup

### 1. Clone the repository

```bash
git clone https://github.com/your-username/flyora.git
cd flyora
```

### 2. Create and activate a virtual environment

```bash
python -m venv venv
source venv/bin/activate        # macOS / Linux
venv\Scripts\activate           # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the application

```bash
python app.py
```

The app will be available at **http://127.0.0.1:5000**

The database is created and seeded automatically on first run — no manual setup needed.

### 5. Reset the database

Delete the database file and restart the app to start fresh:

```bash
rm database/skyroute.db
python app.py
```

---

## Deployment (Render)

1. Push the project to a public GitHub repository.
2. Create a new **Web Service** on [Render](https://render.com).
3. Connect your GitHub repository.
4. Set the following:
   - **Build command:** `pip install -r requirements.txt`
   - **Start command:** `gunicorn app:app`
5. Add an environment variable:
   - `SECRET_KEY` → a long random string
6. Deploy. The database is created and seeded automatically on first start.

> **Note:** Render's free tier uses an ephemeral filesystem, meaning the database resets on each redeploy. This is expected for a demo/student project.

---

## Tech Stack

| Layer      | Technology          |
|------------|---------------------|
| Backend    | Python 3, Flask     |
| Database   | SQLite (via sqlite3)|
| Frontend   | HTML, CSS, JS       |
| Deployment | Render              |

---

## License

This project was created for educational purposes.
