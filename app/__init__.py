from flask import Flask
from config import Config
from .extensions import db, jwt, cors
from flask import render_template

def create_app():
    
    app = Flask(__name__, static_folder="../static", template_folder="../templates")
    app.config.from_object(Config)

    # init extensions
    db.init_app(app)
    jwt.init_app(app)
    cors.init_app(app)

    # register blueprints
    from .controllers.auth import auth_bp
    app.register_blueprint(auth_bp, url_prefix="/api/auth")

    from .controllers.events import events_bp
    app.register_blueprint(events_bp, url_prefix="/api/events")

    from .controllers.notification import notification_bp
    app.register_blueprint(notification_bp, url_prefix="/api/notifications")

    from .controllers.calendar import calendar_bp
    app.register_blueprint(calendar_bp, url_prefix="/api/calendar")

    from .controllers.invite import invite_bp
    app.register_blueprint(invite_bp, url_prefix="/api/invite")

    from .controllers.group import group_bp
    app.register_blueprint(group_bp, url_prefix="/api")

    from .controllers.event_finder import event_finder_bp
    app.register_blueprint(event_finder_bp, url_prefix="/api/event_finder")

    from .controllers.chat import chat_bp
    app.register_blueprint(chat_bp, url_prefix="/api/chat")

    @app.route("/")
    def home():
        return render_template("index.html")

    @app.route("/register")
    def register_page():
        return render_template("register.html")

    @app.route("/login")
    def login_page():
        return render_template("login.html")

    @app.route("/main_menu")
    def main_menu():
        return render_template("main_menu.html")

    @app.route("/event_finder")
    def event_finder():
        return render_template("event_finder.html")

    @app.route("/calendar_create")
    def calendar_create():
        return render_template("calendar_create.html")

    @app.route("/calendar_view")
    def calendar_view():
        return render_template("calendar_view.html")

    @app.route("/availability")
    def availability():
        return render_template("availability.html")

    @app.route("/invite")
    def invite():
        return render_template("invite.html")

    @app.route("/date_selection")
    def date_selection():
        return render_template("date_selection.html")

    @app.route("/invite_confirmation")
    def invite_confirmation():
        return render_template("invite_confirmation.html")

    @app.route("/calendar/create")
    def calendar_create_alt():
        return render_template("calendar_create.html")

    @app.route("/group/invite")
    def group_invite():
        return render_template("invite.html")

    return app
