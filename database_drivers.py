"""Database connection helpers for SQLite, MySQL, and Microsoft SQL Server."""

from pathlib import Path

from cryptography.fernet import Fernet
from sqlalchemy import URL, create_engine, inspect, text
from sqlalchemy.engine import Engine
from flask import current_app
import base64
import hashlib


SUPPORTED_DRIVERS = {"sqlite", "mysql", "sqlserver"}


def _cipher():
    secret = current_app.config["SECRET_KEY"]
    if isinstance(secret, str):
        secret = secret.encode("utf-8")
    key = base64.urlsafe_b64encode(hashlib.sha256(secret).digest())
    return Fernet(key)


def encrypt_password(password):
    if not password:
        return ""
    return _cipher().encrypt(password.encode("utf-8")).decode("ascii")


def decrypt_password(value):
    if not value:
        return ""
    return _cipher().decrypt(value.encode("ascii")).decode("utf-8")


def build_database_url(connection):
    """Build a SQLAlchemy URL without string-concatenating credentials."""
    driver = connection.driver

    if driver == "sqlite":
        path = Path(connection.database_path).expanduser()
        if not path.is_absolute():
            path = Path(current_app.instance_path) / path
        path.parent.mkdir(parents=True, exist_ok=True)
        return URL.create("sqlite", database=str(path))

    password = decrypt_password(connection.password_encrypted)

    if driver == "mysql":
        return URL.create(
            "mysql+pymysql",
            username=connection.username or None,
            password=password or None,
            host=connection.host or "127.0.0.1",
            port=connection.port or 3306,
            database=connection.database_name or None,
            query={"charset": "utf8mb4"},
        )

    if driver == "sqlserver":
        query = {
            "driver": connection.odbc_driver or "ODBC Driver 18 for SQL Server",
            "TrustServerCertificate": "yes" if connection.trust_server_certificate else "no",
        }
        if connection.encrypt_connection:
            query["Encrypt"] = "yes"
        else:
            query["Encrypt"] = "no"

        return URL.create(
            "mssql+pyodbc",
            username=connection.username or None,
            password=password or None,
            host=connection.host or "localhost",
            port=connection.port or 1433,
            database=connection.database_name or "master",
            query=query,
        )

    raise ValueError("درایور پشتیبانی نمی‌شود.")


def create_database_engine(connection) -> Engine:
    if connection.driver == "mysql":
        connect_args = {"connect_timeout": 8}
    elif connection.driver == "sqlserver":
        connect_args = {"timeout": 8}
    else:
        connect_args = {}

    return create_engine(
        build_database_url(connection),
        pool_pre_ping=True,
        pool_recycle=1800,
        future=True,
        hide_parameters=True,
        connect_args=connect_args,
    )


def test_connection(connection):
    engine = create_database_engine(connection)
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True, "اتصال با موفقیت برقرار شد."
    except Exception as exc:
        return False, _friendly_error(exc)
    finally:
        engine.dispose()


def _friendly_error(exc):
    message = str(exc).splitlines()[0] if str(exc) else "خطای نامشخص"
    return message[:500]


def list_databases(connection):
    engine = create_database_engine(connection)
    try:
        if connection.driver == "sqlite":
            return [connection.database_path or "SQLite"]
        if connection.driver == "mysql":
            with engine.connect() as conn:
                return list(conn.execute(text("SHOW DATABASES")).scalars())
        with engine.connect() as conn:
            result = conn.execute(text(
                "SELECT name FROM sys.databases ORDER BY name"
            ))
            return list(result.scalars())
    finally:
        engine.dispose()


def list_tables(connection):
    engine = create_database_engine(connection)
    try:
        inspector = inspect(engine)
        return sorted(inspector.get_table_names())
    finally:
        engine.dispose()


def table_columns(connection, table_name):
    engine = create_database_engine(connection)
    try:
        inspector = inspect(engine)
        if table_name not in inspector.get_table_names():
            raise ValueError("جدول انتخاب‌شده وجود ندارد.")
        return inspector.get_columns(table_name)
    finally:
        engine.dispose()


def run_query(connection, sql, limit=500):
    """Run one SQL statement and return column names and bounded result rows."""
    statement = sql.strip()
    if not statement:
        raise ValueError("کوئری خالی است.")
    if len(statement) > 100_000:
        raise ValueError("طول کوئری بیش از حد مجاز است.")
    # Prevent accidental multi-statement execution. Semicolons inside strings
    # are not parsed here, so a single trailing semicolon is the safe supported form.
    normalized = statement[:-1].rstrip() if statement.endswith(";") else statement
    if ";" in normalized:
        raise ValueError("در هر بار فقط یک دستور SQL اجرا کنید.")

    engine = create_database_engine(connection)
    try:
        with engine.connect() as conn:
            result = conn.execute(text(normalized))
            if result.returns_rows:
                columns = list(result.keys())
                rows = [list(row) for row in result.fetchmany(limit + 1)]
                truncated = len(rows) > limit
                rows = rows[:limit]
                safe_rows = [[_display_value(value) for value in row] for row in rows]
                return {
                    "columns": columns,
                    "rows": safe_rows,
                    "row_count": len(safe_rows),
                    "truncated": truncated,
                    "message": "نتایج نمایش داده شد.",
                }
            conn.commit()
            return {
                "columns": [],
                "rows": [],
                "row_count": result.rowcount,
                "truncated": False,
                "message": f"دستور اجرا شد؛ تعداد ردیف‌های گزارش‌شده: {result.rowcount}",
            }
    finally:
        engine.dispose()


def _display_value(value):
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, (bytes, bytearray, memoryview)):
        return f"<binary: {len(value)} bytes>"
    return str(value)
