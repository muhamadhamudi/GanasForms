from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, current_user
from ..models import User

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/login", methods=["GET","POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("admin.dashboard"))
    if request.method == "POST":
        identity = request.form.get("identity","").strip()
        password = request.form.get("password","")
        user = User.query.filter((User.username == identity) | (User.email == identity)).first()
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for("admin.dashboard"))
        flash("Username/email atau password salah.", "error")
    return render_template("auth/login.html")

@auth_bp.post("/logout")
def logout():
    logout_user()
    flash("Kamu telah keluar dari akun admin.", "success")
    return redirect(url_for("auth.login"))
