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




User.watchlists = _orm.relationship("Watchlist", order_by=Watchlist.id, back_populates="user")