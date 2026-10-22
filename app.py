import os
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, redirect, url_for
from sqlalchemy import inspect, text

from auth import auth_bp, login_manager
from connections import connections_bp
from extensions import csrf, db
from studio import studio_bp

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent


def create_app():
    app = Flask(__name__)

    data_dir = Path(
        os.getenv("DATABASE_STUDIO_HOME", str(BASE_DIR / "instance"))
    )
    if not data_dir.is_absolute():
        data_dir = BASE_DIR / data_dir

    data_dir.mkdir(parents=True, exist_ok=True)

    secret_key = os.getenv("SECRET_KEY")
    if not secret_key:
        # Keep local sessions and encrypted connection passwords valid between restarts.
        key_file = data_dir / "secret.key"
        if key_file.exists():
            secret_key = key_file.read_text(encoding="utf-8").strip()
        else:
            secret_key = os.urandom(32).hex()
            key_file.write_text(secret_key, encoding="utf-8")
            try:
                key_file.chmod(0o600)
            except OSError:
                # Windows does not support POSIX permission bits in the same way.
                pass

    database_file = data_dir / "studio.sqlite3"

    app.config.update(
        SECRET_KEY=secret_key,
        SQLALCHEMY_DATABASE_URI=f"sqlite:///{database_file.as_posix()}",
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=(
            os.getenv("SESSION_COOKIE_SECURE", "false").lower() == "true"
        ),
        MAX_CONTENT_LENGTH=2 * 1024 * 1024,
    )

    db.init_app(app)
    csrf.init_app(app)
    login_manager.init_app(app)

    app.register_blueprint(auth_bp)
    app.register_blueprint(studio_bp)
    app.register_blueprint(connections_bp)

    @app.get("/")
    def index():
        return redirect(url_for("studio.dashboard"))

    with app.app_context():
        from models import User  # Register the model before creating tables.

        db.create_all()

        # Lightweight SQLite schema upgrade for installations created earlier.
        user_columns = {
            column["name"] for column in inspect(db.engine).get_columns("user")
        }
        if "is_admin" not in user_columns:
            with db.engine.begin() as connection:
                connection.execute(
                    text("ALTER TABLE user ADD COLUMN is_admin BOOLEAN NOT NULL DEFAULT 0")
                )

        if not User.query.filter_by(is_admin=True).first():
            first_user = User.query.order_by(User.id).first()
            if first_user:
                first_user.is_admin = True
                db.session.commit()

    return app


app = create_app()


if __name__ == "__main__":
    # This application is intentionally restricted to the local computer.
    app.run(host="127.0.0.1", port=5000, debug=False)
