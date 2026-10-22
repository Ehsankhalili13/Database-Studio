import re

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import (
    LoginManager,
    current_user,
    login_required,
    login_user,
    logout_user,
)

from extensions import db
from models import User

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")

login_manager = LoginManager()
login_manager.login_view = "auth.login"
login_manager.login_message = "برای ادامه وارد حساب شوید."


@login_manager.user_loader
def load_user(user_id):
    """Load a logged-in user from the local application database."""
    try:
        return db.session.get(User, int(user_id))
    except (TypeError, ValueError):
        return None


@auth_bp.route("/signup", methods=["GET", "POST"])
def signup():
    """Allow creation of the first account only."""
    if User.query.first():
        flash(
            "ساخت حساب اولیه قبلاً انجام شده است. "
            "مدیریت کاربران هنوز پیاده‌سازی نشده است.",
            "warning",
        )
        return redirect(url_for("auth.login"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        if not re.fullmatch(r"[A-Za-z0-9_.-]{3,64}", username):
            flash(
                "نام کاربری باید ۳ تا ۶۴ حرف انگلیسی، عدد یا . _ - باشد.",
                "error",
            )
        elif len(password) < 12:
            flash("گذرواژه باید دست‌کم ۱۲ کاراکتر باشد.", "error")
        else:
            user = User(username=username)
            user.set_password(password)

            db.session.add(user)
            db.session.commit()

            login_user(user, fresh=True)
            return redirect(url_for("studio.dashboard"))

    return render_template("signup.html")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("studio.dashboard"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            login_user(user, remember=False, fresh=True)
            return redirect(url_for("studio.dashboard"))

        flash("نام کاربری یا گذرواژه نادرست است.", "error")

    return render_template("login.html")


@auth_bp.post("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("auth.login"))
