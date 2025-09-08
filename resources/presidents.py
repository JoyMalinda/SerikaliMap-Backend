from flask_restful import Resource
from flask import jsonify
from models import db, Term, Position, Official, Party


class PresidentsResource(Resource):
    def get(self):
        # Query all national-level leaders
        terms = (
            db.session.query(Term)
            .join(Official)
            .join(Position)
            .outerjoin(Party)
            .filter(Position.level == "national")
            .all()
        )

        current_leaders = []
        all_leaders = []

        for term in terms:
            leader_data = {
                "name": term.official.name,
                "photo": term.official.photo_url,
                "position": term.position.name,
                "start_year": term.start_year,
                "end_year": term.end_year,
                "party_name": term.party.name if term.party else None,
                "party_abbreviation": None,
            }

            # handle abbreviations (first one if multiple given)
            if term.party and term.party.abbreviation:
                # Take the first abbreviation, strip whitespace and braces
                abbrev = term.party.abbreviation.split(",")[0].strip()
                leader_data["party_abbreviation"] = abbrev.replace("{", "").replace("}", "")

            # Add to all_leaders
            all_leaders.append(leader_data)

            # Add to current_leaders if still serving
            if term.end_year is None:
                current_leaders.append(
                    {
                        "name": term.official.name,
                        "photo": term.official.photo_url,
                        "position": term.position.name,
                    }
                )

        response = {
            "current_leaders": current_leaders,
            "all_leaders": all_leaders,
        }
        return jsonify(response)
