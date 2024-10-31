from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from flask_login import LoginManager
from flask_migrate import Migrate

db = SQLAlchemy()
csrf = CSRFProtect()
login_manager = LoginManager()
migrate = Migrate()

def create_app():
    app = Flask(__name__)
    
    # Configuration
    app.config['SECRET_KEY'] = 'your-secret-key-here'  # Change this to a secure secret key
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['UPLOAD_FOLDER'] = 'app/static/uploads'
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

    # Initialize extensions
    db.init_app(app)
    csrf.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'info'
    migrate.init_app(app, db)

    # Register blueprints
    from app.routes.auth import auth
    from app.routes.main import main
    from app.routes.experiments import experiments
    from app.routes.vessels import vessels
    app.register_blueprint(auth)
    app.register_blueprint(main)
    app.register_blueprint(experiments)
    app.register_blueprint(vessels)

    # Register error handlers
    from app.errors import register_error_handlers
    register_error_handlers(app)

    # Create database tables and initialize data
    with app.app_context():
        db.create_all()
        
        # Add initial cultivation media if none exist
        from app.models import CultivationMedium
        if not CultivationMedium.query.first():
            initial_media = [
                CultivationMedium(type='Petri Dish', status='clean'),
                CultivationMedium(type='Grow Bag', status='clean'),
                CultivationMedium(type='Liquid Culture', status='clean'),
                CultivationMedium(type='Grain Spawn', status='clean'),
                CultivationMedium(type='Agar Plate', status='clean')
            ]
            for medium in initial_media:
                db.session.add(medium)
            db.session.commit()

    return app
