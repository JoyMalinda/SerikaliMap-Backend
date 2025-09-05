# routes/location_routes.py
from flask_restful import Resource, reqparse
from flask import request
from services.mapbox_geocoding import MapboxGeocodingService

geo_service = MapboxGeocodingService()

parser = reqparse.RequestParser()
parser.add_argument("place", type=str, required=True, location="args")

class LocationLookup(Resource):
    def get(self):
        args = parser.parse_args()
        place = args.get("place")

        # Lookup constituency
        constituency = geo_service.search_place_and_lookup(place)
        if not constituency:
            return {"message": "No constituency found for this place"}, 404

        # Get leaders
        leaders = geo_service.get_current_leaders(constituency["constituency_id"]) or {}

        return {
            "location": {
                "county": constituency["county_name"],
                "constituency": constituency["constituency_name"],
            },
            "leaders": leaders,
        }, 200
    
    
    def post(self):
        data = request.get_json()
        place = data.get("place")
        if not place:
            return {"message": "Place is required"}, 400

        service = MapboxGeocodingService()
        constituency = service.search_place_and_lookup(place)
        if not constituency:
            return {"message": "Place not found"}, 404

        leaders = service.get_current_leaders(constituency["constituency_id"])

        return {
            "location": {
                "county": constituency["county_name"],
                "constituency": constituency["constituency_name"],
            },
            "leaders": leaders,
        }, 200

