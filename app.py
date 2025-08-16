import os
from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from models import db 

def create_app():
    app = Flask(__name__)

    # --- Configuration ---
    app.config['SQLALCHEMY_DATABASE_URI'] = "postgres"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['JSON_SORT_KEYS'] = False

    # Initialize extensions
    db.init_app(app)
    Migrate(app, db)

    # --- Simple test route ---
    @app.route("/")
    def index():
        return jsonify({"message": "Flask app is running!"})

    return app


if __name__ == "__main__":
    app = create_app()

    # For first-time quick testing without migrations
    with app.app_context():
        db.create_all()

    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)), debug=True)
