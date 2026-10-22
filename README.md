# Database Studio

A local-first, multi-user database management studio inspired by SSMS and phpMyAdmin.

## Planned stack

- Python, Flask, SQLAlchemy 2.x
- Jinja2, HTML, CSS, JavaScript
- SQLite, MySQL, Microsoft SQL Server adapters

## Initial development

Create a virtual environment, install requirements, copy `.env.example` to `.env`, set a strong secret key, and run `python app.py`.

**Security:** keep the server bound to localhost. Database access and arbitrary SQL execution are powerful; do not expose this development app to untrusted networks.
