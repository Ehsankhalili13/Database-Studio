# Database Studio

A local-only database management workspace inspired by SSMS and phpMyAdmin. The application binds to `127.0.0.1` and is intended for use on the same computer.

## Implemented

- First-account setup, login, logout, administrator-created local user accounts, and CSRF protection for POST forms.
- Saved connection profiles for SQLite, MySQL, and Microsoft SQL Server.
- Connection test before saving, connection edit/delete, and per-user connection visibility.
- Encryption of saved connection passwords using a key derived from the Flask secret key.
- Database listing and table/column explorer.
- SQL editor that executes a single statement and displays up to 500 result rows.
- Paginated table data browser (100 rows per page).
- CSV export and CSV import into an existing table (up to 2 MB and 10,000 rows per upload).
- Local secret key persistence when `SECRET_KEY` is not configured, so saved connection credentials remain decryptable after restarts.
- Persian right-to-left interface.

## Requirements

- Python 3.11 or newer.
- Python dependencies in `requirements.txt`.
- For MySQL, a reachable MySQL server and valid credentials.
- For SQL Server, Microsoft ODBC Driver (for example, ODBC Driver 18 for SQL Server) installed on Windows, in addition to the Python `pyodbc` package.

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
   python -m pip install --upgrade pip
   python -m pip install -r requirements.txt
   ```

4. Optional but recommended: copy `.env.example` to `.env` and set a long random `SECRET_KEY`. If you omit it, the application creates a local key file under `instance/secret.key`. Protect the `instance/` directory.
5. Start the application:

   ```powershell
   python app.py
   ```

6. Open [http://127.0.0.1:5000/auth/signup](http://127.0.0.1:5000/auth/signup) and create the first account.
7. Open **اتصال‌ها** in the dashboard, create a connection, and use **تست اتصال** to diagnose configuration problems.

## Run smoke tests

The repository includes SQLite connection/query smoke tests. Install pytest and run:

\`\`\`powershell
python -m pip install pytest
python -m pytest -q
\`\`\`

GitHub Actions is configured to run these tests on pushes and pull requests. This does not replace testing against real MySQL and SQL Server instances.

## Driver notes

- **SQLite:** select a path such as `sample.sqlite3`. A relative path is resolved under the application's instance directory.
- **MySQL:** enter the server host, port (usually 3306), database name, username, and password. The application uses PyMySQL.
- **SQL Server:** enter the host, port (usually 1433), database name, username, and password. The ODBC driver name must match a driver installed on the machine. Windows integrated authentication is not currently exposed in the form.

## Important limitations and security notes

This is an early-stage local development tool, not yet a fully audited replacement for SSMS or phpMyAdmin.

- SQL entered in the editor runs with the privileges of the configured database account. Use a least-privilege database account and do not connect to production databases until the code has been reviewed and tested.
- The editor accepts one statement per execution. It is not a complete SQL parser; semicolons inside string literals may be rejected.
- The table browser is read-only; change data using SQL statements in the editor.
- CSV import inserts rows into an existing table; it does not create tables or infer schema.
- Fine-grained roles/permissions, query history, editing table rows through the grid, database/schema creation wizards, and comprehensive automated integration tests are not yet implemented.
- Existing application tables are created automatically, but schema changes are not managed by a migration system yet. Back up `instance/studio.sqlite3` before future model changes.
- Keep the app bound to `127.0.0.1`. Do not expose it to a network. Protect `.env`, `instance/secret.key`, and `instance/studio.sqlite3`.

