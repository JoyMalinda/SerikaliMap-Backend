import os
import requests
from sqlalchemy import func
from models import db, Constituency, Term, Position, Official


class MapboxGeocodingService:
    def __init__(self):
        self.api_key = os.getenv("MAPBOX_ACCESS_TOKEN")
        self.base_url = "https://api.mapbox.com/search/geocode/v6/forward"

    def search_place_and_lookup(self, place: str):
        """Forward geocode with Mapbox, then find constituency in DB."""
        coords = self._forward_geocode(place)
        if not coords:
            return None

        lng, lat = coords  # Mapbox returns [lng, lat]
        constituency = self._get_constituency_by_point(lng, lat)
        return constituency
    
    def _forward_geocode(self, place: str):
        """Call Mapbox API to get [lng, lat]."""
        url = "https://api.mapbox.com/search/geocode/v6/forward"
        params = {
            "q": place,
            "access_token": self.api_key,
            "limit": 1
        }

        try:
            response = requests.get(url, params=params)
            response.raise_for_status()  # raise if not 200

            data = response.json()
        except Exception as e:
            print("Mapbox error:", e)
            print("Raw response:", getattr(response, "text", "No response"))
            return None

        if not data.get("features"):
            return None

        return data["features"][0]["geometry"]["coordinates"]


    def _get_constituency_by_point(self, lng, lat):
        """Find constituency containing this point using ST_Contains."""
        point = func.ST_SetSRID(func.ST_MakePoint(lng, lat), 4326)

        constituency = (
            db.session.query(Constituency)
            .filter(func.ST_Contains(Constituency.geom, point))
            .first()
        )
        if not constituency:
            return None

        return {
            "constituency_id": constituency.id,
            "constituency_name": constituency.name,
            "county_id": constituency.county.id,
            "county_name": constituency.county.name,
        }

    def get_current_leaders(self, constituency_id: int):
        """Fetch only current leaders for a constituency + its county."""
        constituency = Constituency.query.get(constituency_id)
        if not constituency:
            return {}

        county_id = constituency.county_id

        # Query current leaders: Term.end_year is NULL means ongoing
        terms = (
            db.session.query(Term)
            .join(Official)
            .join(Position)
            .filter(Term.end_year.is_(None))
            .filter(
                (Term.constituency_id == constituency_id)
                | (Term.county_id == county_id)
            )
            .all()
        )

        leaders = {}
        for t in terms:
            pos_name = t.position.name.lower()
            if "governor" in pos_name and "deputy" not in pos_name:
                leaders["governor"] = t.official.name
            elif "deputy governor" in pos_name or "dep governor" in pos_name:
                leaders["dep_governor"] = t.official.name
            elif "senator" in pos_name:
                leaders["senator"] = t.official.name
            elif "women rep" in pos_name or "woman representative" in pos_name:
                leaders["women_rep"] = t.official.name
            elif pos_name == "mp" or "member of parliament" in pos_name:
                leaders["mp"] = t.official.name

        return leaders