import os
from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_restful import Api
from flask_cors import CORS
from dotenv import load_dotenv
from models import db 

load_dotenv()

app = Flask(__name__)

# Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = "postgres"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JSON_SORT_KEYS'] = False

# Initialize extensions
db.init_app(app)
migrate = Migrate(app, db)
CORS(app, supports_credentials=True, resources={
    r"/*": {"origins": ["http://127.0.0.1:5173", "http://localhost:5173", "https://coursify-frontend-psi.vercel.app"]}
})
api = Api(app)


@app.route("/")
def index():
    return jsonify({"message": "Flask app is running!"})


if __name__ == "__main__":
    app.run(debug=True)