from datetime import datetime, timezone

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from extensions import db


class User(UserMixin, db.Model):
    """A local account used to sign in to Database Studio."""

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(
        db.String(64),
        unique=True,
        nullable=False,
        index=True,
    )
    password_hash = db.Column(db.String(256), nullable=False)
    is_admin = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class DatabaseConnection(db.Model):
    """Saved connection profile. Passwords are encrypted before persistence."""

    id = db.Column(db.Integer, primary_key=True)
    owner_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    name = db.Column(db.String(100), nullable=False)
    driver = db.Column(db.String(20), nullable=False, index=True)
    host = db.Column(db.String(255), nullable=True)
    port = db.Column(db.Integer, nullable=True)
    database_name = db.Column(db.String(255), nullable=True)
    database_path = db.Column(db.String(1000), nullable=True)
    username = db.Column(db.String(255), nullable=True)
    password_encrypted = db.Column(db.Text, nullable=False, default="")
    odbc_driver = db.Column(
        db.String(255),
        nullable=False,
        default="ODBC Driver 18 for SQL Server",
    )
    encrypt_connection = db.Column(db.Boolean, nullable=False, default=True)
    trust_server_certificate = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
