from database_drivers import decrypt_password, encrypt_password, run_query, test_connection
from models import DatabaseConnection
from app import app


def test_sqlite_connection_and_query_execution(tmp_path):
    connection = DatabaseConnection(
        name="test",
        driver="sqlite",
        database_path=str(tmp_path / "test.sqlite3"),
        password_encrypted="",
    )

    with app.app_context():
        ok, message = test_connection(connection)
        assert ok, message

        run_query(
            connection,
            "CREATE TABLE sample (id INTEGER PRIMARY KEY, label TEXT NOT NULL)",
        )
        run_query(connection, "INSERT INTO sample (label) VALUES ('hello')")
        result = run_query(connection, "SELECT id, label FROM sample")

        assert result["columns"] == ["id", "label"]
        assert result["rows"] == [[1, "hello"]]
        assert result["row_count"] == 1


def test_connection_password_encryption_round_trip():
    with app.app_context():
        encrypted = encrypt_password("a strong test password")
        assert encrypted != "a strong test password"
        assert decrypt_password(encrypted) == "a strong test password"
