import os
from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_restful import Api
from flask_cors import CORS
from dotenv import load_dotenv
from models import db 

from urllib.parse import quote_plus

from resources.location_search import LocationLookup

load_dotenv()

app = Flask(__name__)

password = os.getenv("POSTGRES_PASSWORD")
encoded_password = quote_plus(password)

username = os.getenv("POSTGRES_USER")
database = os.getenv("POSTGRES_DB")

# Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = f"postgresql://{username}:{encoded_password}@localhost/{database}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False 
app.config['JSON_SORT_KEYS'] = False

# Initialize extensions
db.init_app(app)
migrate = Migrate(app, db)
CORS(app, supports_credentials=True, resources={
    r"/*": {"origins": ["http://127.0.0.1:5555", "http://127.0.0.1:5555", "http://127.0.0.1:5432", "http://localhost:5432"]}
})
api = Api(app)


@app.route("/")
def index():
    return jsonify({"message": "Flask app is running!"})

api.add_resource(LocationLookup, "/location_search")

if __name__ == "__main__":
    app.run(debug=True)