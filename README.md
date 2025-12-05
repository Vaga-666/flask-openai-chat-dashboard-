# Flask OpenAI Chat Dashboard

Simple Flask web app with:
- user registration/login
- chat history stored per user (SQLite)
- max_tokens setting per user
- OpenAI chat responses

## Features
- Auth (register/login/logout)
- Per-user chat history
- Settings page: `max_tokens`
- SQLite database via SQLAlchemy
- Logging to `error.log`

## Tech Stack
Python • Flask • SQLAlchemy • OpenAI API • SQLite

## Setup
### 1) Create virtual environment
```bash
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

##Install dependencies
pip install -r requirements.txt

#Configure environment

Create .env from example:

# Windows:
copy .env.example .env
# Linux/Mac:
cp .env.example .env


.env must include:

OPENAI_API_KEY

SECRET_KEY

#Run
python app.py

#Open:

http://127.0.0.1:5000

#Project structure

app.py — Flask routes, DB models, OpenAI call

templates/ — HTML pages

chat.db — SQLite database (created automatically)

#Notes

Do not commit .env (contains secrets).

Passwords should be stored hashed (Werkzeug).
