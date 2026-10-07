from flask import Flask
from config import Config
from .extensions import db, login_manager, csrf

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)

    from .models import User
    from .routes.auth import auth_bp
    from .routes.public import public_bp
    from .routes.admin import admin_bp

    app.register_blueprint(public_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp, url_prefix="/admin")

    @app.context_processor
    def inject_globals():
        from datetime import datetime
        return {"current_year": datetime.now().year}

    @app.errorhandler(404)
    def not_found(e):
        from flask import render_template
        return render_template("error.html", code=404, message="Halaman tidak ditemukan."), 404

    @app.errorhandler(500)
    def server_error(e):
        from flask import render_template
        return render_template("error.html", code=500, message="Terjadi kesalahan pada server."), 500

    @app.cli.command("init-db")
    def init_db():
        db.create_all()
        print("Database siap.")

    @app.cli.command("create-admin")
    def create_admin():
        import getpass
        from .models import User
        db.create_all()
        username = input("Username: ").strip()
        email = input("Email: ").strip()
        password = getpass.getpass("Password: ")
        if User.query.filter((User.username == username) | (User.email == email)).first():
            print("Admin sudah ada.")
            return
        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        print("Admin berhasil dibuat.")

    with app.app_context():
        db.create_all()

    return app
