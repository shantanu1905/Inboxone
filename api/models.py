import datetime as _dt
import sqlalchemy as _sql
import sqlalchemy.orm as _orm
import passlib.hash as _hash
import database as _database

_database.Base.metadata.create_all(_database.engine)

class User(_database.Base):
    __tablename__ = "users"
    id = _sql.Column(_sql.Integer, primary_key=True, index=True)
    name = _sql.Column(_sql.String)
    email = _sql.Column(_sql.String, unique=True, index=True)
    is_verified = _sql.Column(_sql.Boolean , default=False)
    otp = _sql.Column(_sql.Integer)
    hashed_password = _sql.Column(_sql.String)
    organisation = _sql.Column(_sql.String, nullable=True)
    api_key = _sql.Column(_sql.String, unique=True, index=True, nullable=True)  # New API key field

    date_created = _sql.Column(_sql.DateTime, default=_dt.datetime.utcnow)
    
    def verify_password(self, password: str):
        return _hash.bcrypt.verify(password, self.hashed_password)


class Watchlist(_database.Base):
    __tablename__ = "watchlists"
    id = _sql.Column(_sql.Integer, primary_key=True, index=True)
    user_id = _sql.Column(_sql.Integer, _sql.ForeignKey('users.id'), nullable=False)
    stock_symbol = _sql.Column(_sql.String, nullable=False)
    stock_name = _sql.Column(_sql.String, nullable=False)  
    date_added = _sql.Column(_sql.DateTime, default=_dt.datetime.utcnow)

    user = _orm.relationship("User", back_populates="watchlists")


class Grant(_database.Base):
    __tablename__ = "grants"
    
    id = _sql.Column(_sql.String, primary_key=True, index=True)
    grant_status = _sql.Column(_sql.String)
    provider = _sql.Column(_sql.String)
    email = _sql.Column(_sql.String, index=True)
    created_at = _sql.Column(_sql.DateTime, default=_dt.datetime.utcnow)
    updated_at = _sql.Column(_sql.DateTime, default=_dt.datetime.utcnow, onupdate=_dt.datetime.utcnow)
    
    # Foreign key to User table
    user_id = _sql.Column(_sql.Integer, _sql.ForeignKey('users.id'))
    # Relationship with User
    user = _orm.relationship("User", back_populates="grants")

class Calendar(_database.Base):
    __tablename__ = "calendars"

    id = _sql.Column(_sql.String, primary_key=True, index=True)
    name = _sql.Column(_sql.String, nullable=False)
    grant_id = _sql.Column(_sql.String, nullable=False, index=True)
    object = _sql.Column(_sql.String, nullable=False)
    is_primary = _sql.Column(_sql.Boolean, default=False)
    read_only = _sql.Column(_sql.Boolean, default=False)
    is_owned_by_user = _sql.Column(_sql.Boolean, default=True)

    # Foreign key to the User model
    user_id = _sql.Column(_sql.Integer, _sql.ForeignKey("users.id"), nullable=False)

class CalendarData(_database.Base):
    __tablename__ = "calendar_event"

    id = _sql.Column(_sql.String, primary_key=True, index=True)
    calendar_id = _sql.Column(_sql.String, nullable=False)
    conferencing_provider = _sql.Column(_sql.String, nullable=True)
    conferencing_meeting_code = _sql.Column(_sql.String, nullable=True)
    conferencing_url = _sql.Column(_sql.String, nullable=True)
    organizer_name = _sql.Column(_sql.String, nullable=True)
    organizer_email = _sql.Column(_sql.String, nullable=False)
    title = _sql.Column(_sql.String, nullable=False)
    creator_name = _sql.Column(_sql.String, nullable=True)
    creator_email = _sql.Column(_sql.String, nullable=True)
    object = _sql.Column(_sql.String, nullable=False)
    start_time = _sql.Column(_sql.DateTime, nullable=False)
    end_time = _sql.Column(_sql.DateTime, nullable=False)
    created_at = _sql.Column(_sql.DateTime, default=_dt.datetime.utcnow)
    updated_at = _sql.Column(_sql.DateTime, default=_dt.datetime.utcnow, onupdate=_dt.datetime.utcnow)
    busy = _sql.Column(_sql.Boolean, default=False)
    # Foreign key to User model
    user_id = _sql.Column(_sql.Integer, _sql.ForeignKey("users.id"), nullable=False)
    user = _orm.relationship("User", back_populates="calendar_events")




# Add this to the User class to complete the relationship
user = _orm.relationship("User", back_populates="calendars")
User.grants = _orm.relationship("Grant", back_populates="user")
User.watchlists = _orm.relationship("Watchlist", order_by=Watchlist.id, back_populates="user")
User.calendar_events = _orm.relationship("CalendarData", back_populates="user")


