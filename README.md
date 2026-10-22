# Database Studio

A local-only, multi-account database management workspace inspired by SSMS and phpMyAdmin.

## Current milestone
- Flask app, first-run account creation, login/logout
- Password hashing and a responsive Persian RTL dashboard
- Internal app metadata stored in SQLite
- Loopback-only server binding (`127.0.0.1`)

## Windows setup
1. Install Python 3.11+.
2. Create a virtual environment: `py -m venv .venv`
3. Activate it: `.\\.venv\\Scripts\\Activate.ps1`
4. Install: `pip install -r requirements.txt`
5. Copy `.env.example` to `.env` and set a long random `SECRET_KEY`.
6. Run `python app.py`.
7. Visit `http://127.0.0.1:5000/auth/signup` and create the first account.

## Planned next
Connection manager and validation; SQLite/MySQL/SQL Server adapters; schema explorer; paginated table browser; SQL editor; exports; local user and role administration.

## Scope and security
This is an early scaffold, **not yet a database-management replacement for SSMS/phpMyAdmin**. First-account setup is implemented; provisioning extra accounts and roles is unfinished. The app intentionally listens on loopback. Protect `.env` and `instance/`, and use low-privilege database credentials. SQL execution, credential protection, CSRF controls, and audit logging require implementation and review before working with important databases.
