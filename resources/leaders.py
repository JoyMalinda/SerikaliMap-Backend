from flask_restful import Resource
from flask import jsonify
from models import db, County, Constituency, Term, Official, Position, Party

class CountyOfficialsResource(Resource):
    def get(self, county_id):
        """
        Fetch all county-level officials (Governor, Senator, Women Rep, etc.)
        for a specific county, including past and present leaders.
        """
        terms = (
            db.session.query(Term)
            .join(Official)
            .join(Position)
            .outerjoin(Party)
            .filter(Term.county_id == county_id, Position.level == "county")
            .all()
        )

        results = []
        for term in terms:
            results.append({
                "official": {
                    "id": term.official.id,
                    "name": term.official.name,
                    "gender": term.official.gender,
                    "photo_url": term.official.photo_url,
                },
                "position": {
                    "id": term.position.id,
                    "name": term.position.name,
                    "level": term.position.level,
                },
                "party": {
                    "id": term.party.id if term.party else None,
                    "name": term.party.name if term.party else None,
                    "abbreviation": term.party.abbreviation if term.party else None,
                } if term.party else None,
                "term": {
                    "id": term.id,
                    "start_year": term.start_year,
                    "end_year": term.end_year,
                    "nomination_type": term.nomination_type,
                },
                "county": {
                    "id": term.county.id if term.county else None,
                    "name": term.county.name if term.county else None,
                }
            })

        return jsonify(results)


class CountyMPsResource(Resource):
    def get(self, county_id):
        """
        Fetch all MPs (constituency-level officials) for a specific county,
        including past and present leaders.
        """
        terms = (
            db.session.query(Term)
            .join(Official)
            .join(Position)
            .outerjoin(Party)
            .join(Constituency)
            .filter(Constituency.county_id == county_id, Position.level == "constituency")
            .all()
        )

        results = []
        for term in terms:
            results.append({
                "official": {
                    "id": term.official.id,
                    "name": term.official.name,
                    "gender": term.official.gender,
                    "photo_url": term.official.photo_url,
                },
                "position": {
                    "id": term.position.id,
                    "name": term.position.name,
                    "level": term.position.level,
                },
                "party": {
                    "id": term.party.id if term.party else None,
                    "name": term.party.name if term.party else None,
                    "abbreviation": term.party.abbreviation if term.party else None,
                } if term.party else None,
                "term": {
                    "id": term.id,
                    "start_year": term.start_year,
                    "end_year": term.end_year,
                    "nomination_type": term.nomination_type,
                },
                "constituency": {
                    "id": term.constituency.id if term.constituency else None,
                    "name": term.constituency.name if term.constituency else None,
                },
                "county": {
                    "id": term.constituency.county.id if term.constituency and term.constituency.county else None,
                    "name": term.constituency.county.name if term.constituency and term.constituency.county else None,
                }
            })

        return jsonify(results)
