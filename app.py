from flask import Flask
from extensions import db, migrate
from config import Config

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    migrate.init_app(app, db)

    from routes import main
    app.register_blueprint(main)

    return app

import models

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)