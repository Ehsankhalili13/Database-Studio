from flask import Blueprint, render_template
from flask_login import login_required, current_user

studio_bp = Blueprint('studio', __name__)

@studio_bp.get('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html', username=current_user.username)
