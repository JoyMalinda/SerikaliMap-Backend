from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import CheckConstraint, UniqueConstraint, Index, text
from sqlalchemy.orm import validates
from sqlalchemy_serializer import SerializerMixin
from geoalchemy2 import Geometry

db = SQLAlchemy()

class TimestampMixin:
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )


class County(db.Model, SerializerMixin, TimestampMixin):
    __tablename__ = "counties"

    serialize_rules = (
        "-constituencies.county",
        "-terms.county",
    )

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False, unique=True)
    code = db.Column(db.String, nullable=False, unique=True)
    population = db.Column(db.Integer, nullable=True)
    area = db.Column(db.Float, nullable=True)
    population_density = db.Column(db.Integer, nullable=True)
    geom = db.Column(Geometry(geometry_type="MULTIPOLYGON", srid=4326))

    constituencies = db.relationship(
        "Constituency",
        back_populates="county",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    terms = db.relationship("Term", back_populates="county", passive_deletes=True)

    __table_args__ = (
        Index("ix_counties_name", text("lower(name)")),
    )

    def __repr__(self):
        return f"<County id={self.id} name={self.name!r}>"


class Constituency(db.Model, SerializerMixin, TimestampMixin):
    __tablename__ = "constituencies"

    serialize_rules = (
        "-county.constituencies",
        "-wards.constituency",
        "-terms.constituency",
    )

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    county_id = db.Column(
        db.Integer, db.ForeignKey("counties.id", ondelete="CASCADE"), nullable=False
    )
    code = db.Column(db.String, nullable=False, unique=True)
    population = db.Column(db.Integer, nullable=True)
    area = db.Column(db.Float, nullable=True)
    population_density = db.Column(db.Float, nullable=True)
    geom = db.Column(Geometry(geometry_type="MULTIPOLYGON", srid=4326))

    county = db.relationship("County", back_populates="constituencies")

    wards = db.relationship(
        "Ward",
        back_populates="constituency",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    terms = db.relationship("Term", back_populates="constituency", passive_deletes=True)

    __table_args__ = (
        UniqueConstraint("name", "county_id", name="uq_constituencies_name_per_county"),
        Index("ix_constituencies_name", text("lower(name)")),
    )

    def __repr__(self):
        return f"<Constituency id={self.id} name={self.name!r}>"


class Ward(db.Model, SerializerMixin, TimestampMixin):
    __tablename__ = "wards"

    serialize_rules = (
        "-constituency.wards",
        "-terms.ward",
    )

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    constituency_id = db.Column(
        db.Integer, db.ForeignKey("constituencies.id", ondelete="CASCADE"), nullable=False
    )
    code = db.Column(db.String, nullable=False, unique=True)
    geom = db.Column(Geometry(geometry_type="MULTIPOLYGON", srid=4326))

    constituency = db.relationship("Constituency", back_populates="wards")
    terms = db.relationship("Term", back_populates="ward", passive_deletes=True)

    __table_args__ = (
        Index("ix_wards_name", text("lower(name)")),
    )

    def __repr__(self):
        return f"<Ward id={self.id} name={self.name!r}>"
    

class Position(db.Model, SerializerMixin, TimestampMixin):
    __tablename__ = "positions"

    serialize_rules = ("-terms.position",)

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False, unique=True)  # MP, Senator, Governor, Women Rep, MCA
    level = db.Column(db.String, nullable=False)  # national, county, ward

    terms = db.relationship("Term", back_populates="position", passive_deletes=True)

    __table_args__ = (
        CheckConstraint(
            "level IN ('national','county','constituency','ward')",
            name="ck_positions_level_valid",
        ),
        Index("ix_positions_name", text("lower(name)")),
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Position id={self.id} name={self.name!r} level={self.level}>"


class Party(db.Model, SerializerMixin, TimestampMixin):
    __tablename__ = "parties"

    serialize_rules = ("-terms.party",)

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False, unique=True)
    abbreviation = db.Column(db.String, nullable=True)
    colors = db.Column(db.String, nullable=True)

    terms = db.relationship("Term", back_populates="party", passive_deletes=True)

    __table_args__ = (
        Index("ix_parties_name", text("lower(name)")),
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Party id={self.id} name={self.name!r}>"


class Official(db.Model, SerializerMixin, TimestampMixin):
    __tablename__ = "officials"

    serialize_rules = ("-terms.official",)

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    gender = db.Column(db.String, nullable=False)
    photo_url = db.Column(db.String, nullable=False)

    terms = db.relationship(
        "Term",
        back_populates="official",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    __table_args__ = (
        CheckConstraint("gender IN ('male','female','other')", name="ck_officials_gender_valid"),
        Index("ix_officials_name", text("lower(name)")),
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Official id={self.id} name={self.name!r}>"


class Term(db.Model, SerializerMixin, TimestampMixin):
    __tablename__ = "terms"

    serialize_rules = (
        "-official.terms",
        "-position.terms",
        "-party.terms",
        "-county.terms",
        "-constituency.terms",
        "-ward.terms",
    )

    id = db.Column(db.Integer, primary_key=True)

    official_id = db.Column(
        db.Integer, db.ForeignKey("officials.id", ondelete="CASCADE"), nullable=False
    )
    position_id = db.Column(
        db.Integer, db.ForeignKey("positions.id", ondelete="RESTRICT"), nullable=False
    )
    party_id = db.Column(
        db.Integer, db.ForeignKey("parties.id", ondelete="RESTRICT"), nullable=True
    )

    start_year = db.Column(db.Integer, nullable=False)
    end_year = db.Column(db.Integer, nullable=True)

    county_id = db.Column(
        db.Integer, db.ForeignKey("counties.id", ondelete="SET NULL"), nullable=True
    )
    constituency_id = db.Column(
        db.Integer, db.ForeignKey("constituencies.id", ondelete="SET NULL"), nullable=True
    )
    ward_id = db.Column(
        db.Integer, db.ForeignKey("wards.id", ondelete="SET NULL"), nullable=True
    )

    nomination_type = db.Column(db.String, nullable=True)  # e.g., Gender balance, Marginalized group, Youth, NULL if elected

    official = db.relationship("Official", back_populates="terms")
    position = db.relationship("Position", back_populates="terms")
    party = db.relationship("Party", back_populates="terms")

    county = db.relationship("County", back_populates="terms")
    constituency = db.relationship("Constituency", back_populates="terms")
    ward = db.relationship("Ward", back_populates="terms")

    __table_args__ = (
        CheckConstraint("start_year > 1900", name="ck_terms_start_year_valid"),
        CheckConstraint(
            "end_year IS NULL OR end_year >= start_year",
            name="ck_terms_end_year_after_start",
        ),
        Index("ix_terms_years", "start_year", "end_year"),
        Index("ix_terms_official", "official_id"),
    )

    @validates("start_year", "end_year")
    def validate_years(self, key, value):
        if value is None:
            return value
        if not (1900 <= int(value) <= 2100):
            raise ValueError("Year must be between 1900 and 2100")
        return int(value)

    @validates("nomination_type")
    def validate_nomination(self, key, value):
        if value is None:
            return None
        allowed = {"Gender balance", "Marginalized group", "Youth", "Nominated"}
        if value not in allowed:
            # Keep flexible but guard common typos; you can relax this if needed
            raise ValueError(
                f"nomination_type must be one of {sorted(allowed)} or NULL if elected"
            )
        return value

    def __repr__(self) -> str:  # pragma: no cover
        span = f"{self.start_year}-{self.end_year or 'present'}"
        return f"<Term id={self.id} official_id={self.official_id} position_id={self.position_id} {span}>"
    