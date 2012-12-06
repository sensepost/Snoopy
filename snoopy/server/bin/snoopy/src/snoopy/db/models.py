"""Contains all SQLAlchemy ORM models."""

from cryptacular import bcrypt
from sqlalchemy import Column
from sqlalchemy import Boolean, CHAR, DateTime, Integer, Numeric, SmallInteger, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.hybrid import hybrid_property


crypt = bcrypt.BCRYPTPasswordManager()

def hash_password(password):
    return unicode(crypt.encode(password))


Session = None
Base = declarative_base()


##########
# MODELS #
##########

class Probe(Base):
    __tablename__ = 'probes'

    # COLUMNS #
#    id = Column(Integer, primary_key=True)
    monitor = Column('monitor_id', String(20, convert_unicode=True), default=None, primary_key=True)
    device_mac = Column(CHAR(17), default=None, primary_key=True)
    probe_ssid = Column(String(100, convert_unicode=True), default=None, primary_key=True)
    signal_db = Column(Integer, default=None)
    timestamp = Column(DateTime, default=None, primary_key=True)
    run_id = Column(String(50), default=None)
    location = Column(String(50), default=None)
    proximity_session = Column(String(20), default=None)


class Cookie(Base):
    __tablename__ = 'cookies'

    # COLUMNS #
    id = Column(Integer, primary_key=True)
    device_mac = Column(CHAR(17), nullable=False, default='')
    device_ip = Column(CHAR(15), default=None)
    site = Column(String(256), nullable=False, default='')
    cookie_name = Column(String(256), nullable=False, default='')
    cookie_name = Column(String(4096), nullable=False, default='')


class GpsMovement(Base):
    __tablename__ = 'gps_movement'

    # COLUMNS #
    monitor = Column('monitor_id', String(20, convert_unicode=True), default=None, primary_key=True)
    run_id = Column(String(20), default=None)
    timestamp = Column(Integer, nullable=False, default=0, primary_key=True)
    gps_lat = Column(Numeric(8, 6))
    gps_long = Column(Numeric(8, 6))
    accuracy = Column(Numeric(8, 6))


class Wigle(Base):
    __tablename__ = 'wigle'

    # COLUMNS #
    ssid = Column(String(100), default=None, primary_key=True)
    gps_long = Column(Numeric(11, 8), default=None, primary_key=True)
    gps_lat = Column(Numeric(11, 8), default=None, primary_key=True)
    last_update = Column(DateTime, default=None)
    mac = Column(CHAR(17), default=None)
    overflow = Column(SmallInteger, default=None)


class User(Base):
    __tablename__ = 'snoopy_user'

    # COLUMNS #
    id = Column(Integer, primary_key=True)
    name = Column(String(255, convert_unicode=True), unique=True)
    password_raw = Column('password', String(255, convert_unicode=True), nullable=False, default=u'')
    is_admin = Column(Boolean, default=False, nullable=False)

    @hybrid_property
    def password(self):
        return self.password_raw

    @password.setter
    def password(self, password):
        if len(password) < 8:
            raise ValueError('Password too short')
        self.password_raw = hash_password(password)

    # CLASS METHODS #
    @classmethod
    def check_password(cls, name, password):
        user = Session().query(cls).filter_by(name=name).first()
        if not user:
            return None
        return crypt.check(user.password, password) and user or None

    # SPECIAL METHODS #
    def __repr__(self):
        admin = ''
        if self.is_admin:
            admin = '*'
        return '<%s%s %d:%r>' % (admin, self.__class__.__name__, self.id, self.name)
