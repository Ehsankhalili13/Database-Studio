from flask import Blueprint, render_template
from flask_login import current_user, login_required

from models import DatabaseConnection

studio_bp = Blueprint("studio", __name__)


@studio_bp.get("/dashboard")
@login_required
def dashboard():
    connection_count = DatabaseConnection.query.filter_by(
        owner_id=current_user.id
    ).count()

    return render_template(
        "dashboard.html",
        username=current_user.username,
        connection_count=connection_count,
    )
