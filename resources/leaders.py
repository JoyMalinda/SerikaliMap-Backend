from flask_restful import Resource
from flask import jsonify
from sqlalchemy.orm import joinedload
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
            if term.party and term.party.abbreviation:
                abbrev = term.party.abbreviation.split(",")[0].strip()
                abbrv = abbrev.replace("{", "").replace("}", "")
            else:
                abbrv = "Independent"
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
                    "abbreviation": abbrv,
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


def party_key(party):
    """Helper to normalize party data (handles independent)."""
    if party :
        abbrev = party.abbreviation.split(",")[0].strip()
        abbrv = abbrev.replace("{", "").replace("}", "")
    else:
        abbrv = "Independent"
    return (party.name if party else "Independent", abbrv)


class AllCountyOfficials(Resource):
    def get(self):
        terms = (
            Term.query.join(Position)
            .filter(Position.level == "county")
            .options(
                joinedload(Term.official),
                joinedload(Term.position),
                joinedload(Term.party),
                joinedload(Term.county),
            )
            .all()
        )

        officials_data = []
        stats = {}

        for term in terms:
            if not term.county:
                continue

            if term.party and term.party.abbreviation:
                abbrev = term.party.abbreviation.split(",")[0].strip()
                abbrv = abbrev.replace("{", "").replace("}", "")
            else:
                abbrv = "Independent"

            # Build official info
            official_info = {
                "id": term.official.id,
                "name": term.official.name,
                "gender": term.official.gender,
                "photo_url": term.official.photo_url,
                "position": term.position.name,
                "county": term.county.name,
                "party": {
                    "name": term.party.name if term.party else "Independent",
                    "abbrev": abbrv,
                },
                "start_year": term.start_year,
                "end_year": term.end_year,
            }
            officials_data.append(official_info)

            pos_name = term.position.name
            if pos_name not in stats:
                stats[pos_name] = {
                    "gender_counts": {"male": 0, "female": 0, "other": 0},
                    "party_distribution": {},
                }

            # Gender counts
            if term.official.gender in stats[pos_name]["gender_counts"]:
                stats[pos_name]["gender_counts"][term.official.gender] += 1
            else:
                stats[pos_name]["gender_counts"]["other"] += 1

            # Party distribution
            pname, pabbrev = party_key(term.party)
            if pname not in stats[pos_name]["party_distribution"]:
                stats[pos_name]["party_distribution"][pname] = {
                    "name": pname,
                    "abbrev": pabbrev,
                    "count": 0,
                }
            stats[pos_name]["party_distribution"][pname]["count"] += 1

        # Convert party_distribution dicts to lists
        for pos in stats:
            stats[pos]["party_distribution"] = list(stats[pos]["party_distribution"].values())

        return jsonify({
            "officials": officials_data,
            "stats": stats,
        })


class AllMPs(Resource):
    def get(self):
        terms = (
            Term.query.join(Position)
            .filter(Position.name == "MP")
            .options(
                joinedload(Term.official),
                joinedload(Term.position),
                joinedload(Term.party),
                joinedload(Term.constituency).joinedload(Constituency.county),
            )
            .all()
        )

        officials_data = []
        gender_counts_all = {"male": 0, "female": 0, "other": 0}
        gender_counts_elected = {"male": 0, "female": 0, "other": 0}
        party_counts_all = {}
        party_counts_elected = {}

        for term in terms:
            constituency = term.constituency
            county = constituency.county if constituency else None

            official_info = {
                "id": term.official.id,
                "name": term.official.name,
                "gender": term.official.gender,
                "photo_url": term.official.photo_url,
                "position": "MP",
                "county": county.name if county else None,
                "constituency": constituency.name if constituency else None,
                "party": {
                    "name": term.party.name if term.party else "Independent",
                    "abbrev": term.party.abbreviation if term.party else "IND",
                },
                "nomination_type": term.nomination_type,
                "start_year": term.start_year,
                "end_year": term.end_year,
            }
            officials_data.append(official_info)

            # Gender counts
            g = term.official.gender if term.official.gender in gender_counts_all else "other"
            gender_counts_all[g] += 1
            if not term.nomination_type:  # elected only
                gender_counts_elected[g] += 1

            # Party counts
            pname, pabbrev = party_key(term.party)

            if pname not in party_counts_all:
                party_counts_all[pname] = {"name": pname, "abbrev": pabbrev, "count": 0}
            party_counts_all[pname]["count"] += 1

            if not term.nomination_type:
                if pname not in party_counts_elected:
                    party_counts_elected[pname] = {"name": pname, "abbrev": pabbrev, "count": 0}
                party_counts_elected[pname]["count"] += 1

        return jsonify({
            "officials": officials_data,
            "stats": {
                "gender_counts": {
                    "all_mps": gender_counts_all,
                    "elected_only": gender_counts_elected,
                },
                "party_distribution": {
                    "all_mps": list(party_counts_all.values()),
                    "elected_only": list(party_counts_elected.values()),
                }
            }
        })