from flask_restful import Resource
from flask import jsonify
from sqlalchemy import func, cast
from geoalchemy2 import Geometry
from models import db, County, Constituency, Term, Position, Official, Party


def geom_to_svg(geom):
    return db.session.scalar(
        func.ST_AsSVG(cast(geom, Geometry("MULTIPOLYGON", 4326)), 0, 2)
    )


def get_leader_by_position(position_name, county_id=None, constituency_id=None):
    """Fetch leader info by position (e.g., Governor, MP)."""
    q = (
        db.session.query(Term, Official, Party, Position)
        .join(Official, Term.official_id == Official.id)
        .outerjoin(Party, Term.party_id == Party.id)  # <-- outer join instead of inner
        .join(Position, Term.position_id == Position.id)
        .filter(Position.name.ilike(position_name))
    )

    if county_id:
        q = q.filter(Term.county_id == county_id)
    if constituency_id:
        q = q.filter(Term.constituency_id == constituency_id)

    term = q.first()
    if not term:
        return None

    t, official, party, position = term
    if party and party.abbreviation:
        abbrev = party.abbreviation.split(",")[0].strip()
        abbrv = abbrev.replace("{", "").replace("}", "")
    else:
        abbrv = "Independent"

    return {
        "name": official.name,
        "gender": official.gender,
        "photo_url": official.photo_url,
        "position": position.name,
        "party": {
            "name": party.name if party else "Independent",
            "abbreviation": abbrv,
        },
        "term": f"{t.start_year}-{t.end_year or 'present'}",
    }


class CountiesMap(Resource):
    def get(self):
        counties = County.query.all()
        data = []
        for county in counties:
            svg_path = geom_to_svg(county.geom)
            data.append(
                {
                    "id": county.id,
                    "name": county.name,
                    "code": county.code,
                    "svgPath": svg_path,
                }
            )
        return jsonify(data)


class CountyDetailMap(Resource):
    def get(self, county_id):
        county = County.query.get_or_404(county_id)

        # County SVG
        county_svg = geom_to_svg(county.geom)

        # Leaders at county level
        leaders = {
            "governor": get_leader_by_position("Governor", county_id=county.id),
            "deputy_governor": get_leader_by_position("Deputy Governor", county_id=county.id),
            "senator": get_leader_by_position("Senator", county_id=county.id),
            "women_rep": get_leader_by_position("Women Representative", county_id=county.id),
        }

        # Constituencies + MPs
        constituencies_data = []
        mps = []
        for c in county.constituencies:
            svg_path = geom_to_svg(c.geom)
            mp = get_leader_by_position("MP", constituency_id=c.id)
            if mp:
                mps.append(mp)
            constituencies_data.append(
                {
                    "id": c.id,
                    "name": c.name,
                    "code": c.code,
                    "svgPath": svg_path,
                    "mp": mp,
                }
            )

        response = {
            "county": {
                "id": county.id,
                "name": county.name,
                "code": county.code,
                "svgPath": county_svg,
                "population": county.population,
                "population_density": county.population_density,
                "area": county.area,
            },
            "leaders": {**leaders, "mps": mps},
            "constituencies": constituencies_data,
        }

        return jsonify(response)


class ConstituenciesMap(Resource):
    def get(self):
        constituencies = Constituency.query.all()
        data = []
        for c in constituencies:
            svg_path = geom_to_svg(c.geom)
            mp = get_leader_by_position("MP", constituency_id=c.id)
            data.append(
                {
                    "id": c.id,
                    "name": c.name,
                    "code": c.code,
                    "county_id": c.county_id,
                    "svgPath": svg_path,
                    "mp": mp,
                }
            )
        return jsonify(data)