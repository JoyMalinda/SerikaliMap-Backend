"""
   These are just functions that help with debugging especially the wards stuff.
"""
import os
import json
from models import db, Ward
from dotenv import load_dotenv
from flask import Flask
from pathlib import Path

load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL') or os.getenv('DATABASE_URI')
if not DATABASE_URL:
    raise RuntimeError('Please set DATABASE_URL environment variable to your Postgres/Supabase connection string')

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / 'data' / 'maps'
FILES = {
    'wards_geojson': DATA_DIR / 'wards_geojson.json',
}

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

with app.app_context():
    # initialize db (models module provided the db object)
    db.init_app(app)

    def get_missing():
        wards = db.session.query(Ward.code).all()
        ward_codes = sorted([int(code[0]) for code in wards if code[0].isdigit()])

        if not ward_codes:
            print("No ward codes found.")
            return

        min_code = min(ward_codes)
        max_code = max(ward_codes)

        missing_wards = []
        for i in range(min_code, max_code + 1):
            if i not in ward_codes:
                missing_wards.append(f"{i:04d}")

        print("Missing ward codes in db:", missing_wards)
        return missing_wards
    
    def get_duplicate():
        wards_geo = None
        if Path(FILES['wards_geojson']).exists():
            with open(FILES['wards_geojson'], 'r', encoding='utf-8') as f:
               wards_geo = json.load(f)

        if not wards_geo:
            print("No wards_geojson file found or file is empty.")
            return

        # Collect all COUNTY_ASS codes
        ward_codes = []
        for feat in wards_geo.get('features', []):
            props = feat.get('properties') or {}
            wcode = props.get('COUNTY_ASS')
            if wcode is not None:
                try:
                    ward_codes.append(int(wcode))
                except ValueError:
                    print(f"Invalid code (non-numeric): {wcode}")

        # Detect duplicates
        seen = set()
        duplicates = set()
        for code in ward_codes:
            if code in seen:
                duplicates.add(code)
            else:
                seen.add(code)

        # Detect missing codes (from 1 to 1450)
        expected = set(range(1, 1451))
        existing = set(ward_codes)
        missing = sorted(list(expected - existing))

        # Print results
        print(f"Duplicate codes in json: {sorted(list(duplicates))}")
        print(f"Missing codes in json: {missing}")


    def manual_db():
        db.drop_all()
        db.create_all()
        pass

    if __name__ == "__main__":
        get_duplicate()
        get_missing()