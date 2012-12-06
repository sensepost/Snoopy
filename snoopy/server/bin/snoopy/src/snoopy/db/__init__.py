"""Database initialisation."""

import logging
#log = logging.getLogger('snoopy.db')

import traceback
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

from . import models
from models import Base, Probe, Cookie, GpsMovement, Wigle, User

engine = None
Session = None


class SessionCtx(object):
    """Context manager that creates a SQLAlchemy session."""
    def __init__(self, sqla_session=None):
        if sqla_session is None:
            sqla_session = Session()
        self.session = sqla_session

    def __enter__(self):
        return self.session

    def __exit__(self, exctype, excvalue, traceb):
        """Call C{commit()} if not exception occurred, C{rollback()} and log
            otherwise."""
        if exctype is None:
            # No exception was raised
            self.session.commit()
            return
        # *sigh*. we have an exception to handle :(
        self.session.rollback()
        del self.session
        straceb = '\n'.join(traceback.format_tb(traceb))
        logging.error('Database error:\n%s\n%s' % (straceb, repr(excvalue)))


def init(uri=None, **kwargs):
    global engine, Session

    if not uri:
        uri = 'mysql://snoopy:RANDOMPASSWORDGOESHERE@localhost/snoopy'

    if engine is not None:
        raise ValueError('DB engine already initialised!')

    engine = create_engine(uri, **kwargs)
    Session = scoped_session(sessionmaker(bind=engine))
    models.Session = Session

    Base.metadata.bind = engine
    Base.metadata.create_all(engine)
    logging.info('create_all() complete')
    create_test_data()


def create_test_data():
    global Session

    with SessionCtx() as session:
#        if session.query(User).filter_by(name='admin').count() < 1:
#            session.add(User(name='admin', password='adminnimda', is_admin=True))
        if session.query(User).filter_by(name='admin').count() < 1:
            session.add(User(name='admin', password='YABADABADOO', is_admin=True))
