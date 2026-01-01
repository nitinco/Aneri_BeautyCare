# Aneri BeautyCare — Backend + Admin UI

This repository contains the Aneri BeautyCare Flask application (backend + Jinja2 frontend). The README below explains how to prepare a development environment and run the project on another machine.

Prerequisites
- Python 3.10+ (3.8 may work but 3.10+ recommended)
- MySQL server (or XAMPP with MySQL)
- Git

Quick setup (copy-and-paste)
1. Clone the repo:

   git clone <repo_url>
   cd "Aneri_BeautyCare_Backend"

2. Create and activate a virtual environment:

   python3 -m venv venv
   source venv/bin/activate

3. Install Python dependencies:

   pip install --upgrade pip
   pip install -r requirements.txt

4. Create the database (choose one):

   - Option A — let the helper create DB (set `DATABASE_URL`):

       export DATABASE_URL='mysql+pymysql://root:password@localhost:3306/aneri_beauty_care'
       python create_db.py

   - Option B — create DB manually using your MySQL client:

       CREATE DATABASE aneri_beauty_care CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

   Note: `config.py` contains `SQLALCHEMY_DATABASE_URI`. Update it to point to your DB if you prefer editing the file instead of using `DATABASE_URL`.

5. Apply migrations (optional) or let app create tables:

   # If you want to use Flask-Migrate
   flask db upgrade

   # Or simply run the app once — it will call `db.create_all()` on startup

6. Create an admin user (optional):

   export ADMIN_EMAIL=admin@aneri.local
   export ADMIN_PASSWORD=admin123
   python seed.py

7. Run the application:

   # development (debug):
   python app.py

   # production (example using gunicorn):
   gunicorn -w 4 -b 0.0.0.0:8000 app:app

Project layout (important files)
- `app.py` — application factory and blueprint registration
- `config.py` — default configuration (update DB URI / secret key here)
- `create_db.py` — helper script to create the MySQL database if missing
- `seed.py` — creates an initial admin user
- `routes/` — blueprint implementations for auth, orders, deliveries, staff, etc.
- `templates/` and `static/` — frontend pages and JS used by the admin/customer UI

Notes & troubleshooting
- If you use XAMPP, ensure MySQL is running and update `config.py` or set `DATABASE_URL` accordingly.
- If you see authentication or JWT problems, check `JWT_SECRET_KEY` in `config.py`.
- If product names do not show in orders, ensure `products` table is populated (use admin UI or seed data).
- To create tables deterministically, use `flask db migrate` and `flask db upgrade` (Flask-Migrate is included).

Optional improvements before handing off
- Add a `.env.example` with environment variables and instructions.
- Add unit/integration tests and a small script to run them.
- Add a Dockerfile / docker-compose to simplify environment setup for the recipient.

If you want, I can also generate a `.env.example` and a simple `docker-compose.yml` for one-command setup. Which would you prefer?
