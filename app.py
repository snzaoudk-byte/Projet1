from flask import Flask
from extensions import db, migrate
from config import config_by_name
import os

def create_app():
    app = Flask(__name__)

    env = os.environ.get('FLASK_ENV', 'default')
    app.config.from_object(config_by_name[env])

    db.init_app(app)
    migrate.init_app(app, db)

    with app.app_context():
        import models  # noqa: F401
        from routes import main
        app.register_blueprint(main)
        db.create_all()

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)