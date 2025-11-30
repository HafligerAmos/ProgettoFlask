# ROI & Portfolio Planner

Premium Flask application that calculates ROI, manages a multi-asset portfolio, and renders Matplotlib charts saved under `static/charts`.

## Requirements

- Python 3.11+
- Dependencies listed in `requirements.txt`

## Quick setup

```bash
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
cp .env.example .env
```

Fill `.env` with your values:

```
FLASK_APP=wsgi.py
FLASK_ENV=development
SECRET_KEY=super-secret-key
DATABASE_URL=sqlite:///project.db
ADMIN_EMAIL=admin@example.com
ADMIN_PASSWORD=changeme
```
(The password is temporary)

## Database & migrations

```bash
flask db upgrade
```

Tables are auto-populated with the curated assets plus the admin user (credentials pulled from `.env`).

## Useful commands

```bash
flask run           # start the app locally
flask shell         # open a shell with the app context
```

## Features

- ROI calculator directly from the homepage
- Portfolio management with automatic allocations and recurring monthly / yearly plans
- Charts for each asset, the total portfolio, and multi-asset overlays (Matplotlib)
- REST APIs:
  - `POST /api/calc-asset`
  - `POST /api/calc-portfolio`
- Authentication with roles and automatic seeding

Charts are written under `app/static/charts/` and displayed inside `charts.html`.
