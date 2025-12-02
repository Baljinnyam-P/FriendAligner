
from flask import Flask
from config import Config
from .extensions import db, jwt, cors
from flask import render_template, request

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
    app.register_blueprint(group_bp, url_prefix="/api/group")

    from .controllers.event_finder import event_finder_bp
    app.register_blueprint(event_finder_bp, url_prefix="/api/event_finder")

    from .controllers.chat import chat_bp
    app.register_blueprint(chat_bp, url_prefix="/api/chat")

    @app.route("/")
    def welcome_page():
            return render_template("welcomePG.html")
    


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
        return render_template("calendar.html")

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
    
    # Shared Calendar View, accepts group_id and calendar_id as query parameters
    @app.route("/shared_calendar_view")
    def shared_calendar_view():
        group_id = request.args.get('group_id', type=int)
        calendar_id = request.args.get('calendar_id', type=int)
        # Fallbacks if not found
        selectedCalendarType = "group" if group_id else "personal"
        return render_template(
            "shared_calendar.html",
            selectedCalendarType=selectedCalendarType,
            group_id=group_id,
            calendar_id=calendar_id
        )
    
    @app.route("/notifications")
    def notifications():
        return render_template("notifications.html")
    
    @app.route("/groups_overview")
    def groups_overview():
        return render_template("groups_overview.html")

    return app
