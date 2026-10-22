# Database Studio

A local-only database management workspace inspired by SSMS and phpMyAdmin.

## Current implementation

- Flask application factory.
- First-account setup, login, and logout.
- Password hashing using Werkzeug.
- Persian right-to-left dashboard.
- Internal application data stored in SQLite.
- Development server bound to `127.0.0.1`.

## Requirements

- Python 3.11 or newer.
- Python dependencies listed in `requirements.txt`.
- ODBC driver for SQL Server when its connector is implemented.

## Run on Windows

Open PowerShell in the project directory.

1. Create a virtual environment:

   ```powershell
   py -m venv .venv
   ```

2. Activate it:

   ```powershell
   .\.venv\Scripts\Activate.ps1
   ```

3. Install dependencies:

   ```powershell
   pip install -r requirements.txt
   ```

4. Copy `.env.example` to `.env` and set a long, random `SECRET_KEY`.
5. Start the application:

   ```powershell
   python app.py
   ```

6. Open [http://127.0.0.1:5000/auth/signup](http://127.0.0.1:5000/auth/signup) and create the first account.

## Not implemented yet

The current dashboard is a UI scaffold. These features are still pending:

- Saving, testing, and managing database connections.
- SQLite, MySQL, and SQL Server adapters.
- Database and schema explorer.
- Table data browser with pagination, search, and sorting.
- SQL editor and query execution.
- Import/export tools.
- Provisioning additional users and managing roles.

## Security notes

This is an early development scaffold, not yet a replacement for SSMS or phpMyAdmin. Public signup is only available until the first account is created. A proper local user-administration flow, CSRF protection, secure handling of database credentials, and safeguards for SQL execution still need to be implemented.

Keep the app bound to `127.0.0.1`. Do not expose it to a network or use it with important databases until the missing security controls have been implemented and tested. Protect the `.env` file and the `instance/` directory.
