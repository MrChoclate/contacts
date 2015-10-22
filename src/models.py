# -*- coding: utf-8 -*-

import os.path
import datetime
import json

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine
from sqlalchemy import Column, Integer, String, DateTime, Date, Enum
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy import ForeignKey


# Database connection
_DATABASE = 'sqlite:///db.sqlite3'
_DEBUG = False

# ORM base
_Base = declarative_base()

def make_serializable(attr):
    if type(attr) in [datetime.datetime, datetime.date]:
        return str(attr)
    return attr

def to_dict(obj):
    return {c.name: make_serializable(getattr(obj, c.name))
        for c in obj.__table__.columns}

def serialize(dict):
    return json.dumps(to_dict(obj))

class Contact(_Base):
    """Contact class for the database.
    It is used to store a contact information.
    It is linked to an event.
    """

    __tablename__ = 'contact'

    id = Column(Integer, primary_key=True)
    last_name = Column(String, nullable=False)
    first_name = Column(String, nullable=False)
    gender = Column(Enum("Monsieur", "Madame"), nullable=False)
    postal_code = Column(Integer, nullable=False)
    street = Column(String, nullable=False)
    town = Column(String, nullable=False)
    country = Column(String, nullable=False)
    mail = Column(String, nullable=False)
    mail2 = Column(String, nullable=False)
    phone = Column(String, nullable=False)
    degree = Column(String, nullable=False)
    studies = Column(String, nullable=False)
    master = Column(Integer, nullable=False)
    comment = Column(String, nullable=False)
    eisti = Column(String, nullable=False)

    def __init__(self):
        self.last_name = self.first_name = self.mail = self.mail2 = ""
        self.phone = self.street = self.town = self.postal_code = ""
        self.degree = self.master = self.comment = ""
        self.studies = "-"
        self.gender = "Monsieur"
        self.country = "France"
        self.eisti = "Dans ce salon"

class Event(_Base):
    """Event class for the database.
    It is used to store the event information.
    It has several dates, many contacts and many accompanists.
    """

    __tablename__ = 'event'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    location = Column(String)
    begin =  Column(Date, default=datetime.date.today())
    end =  Column(Date, default=datetime.date.today())
    contacts = relationship('Participate', cascade='delete', order_by='Participate.date.desc()')

class Participate(_Base):
    """Contacts participate to an event.
    We store the time when the contact is registered.
    """

    __tablename__ = 'participate'

    event_id = Column(Integer, ForeignKey('event.id'), primary_key=True)
    contact_id = Column(Integer, ForeignKey('contact.id'), primary_key=True)
    date = Column(DateTime, nullable=False)
    contact = relationship('Contact', cascade='delete')

class Accompanists(_Base):
    """Store the number of accompanists at an event.
    We need to store the date because an event can last more than one day.
    """

    __tablename__ = 'accompanists'

    event_id = Column(Integer, ForeignKey('event.id'), primary_key=True)
    date = Column(Date, primary_key=True)
    number = Column(Integer, nullable=False, default=0)

# Connect to database
_engine = create_engine(_DATABASE, echo=_DEBUG, convert_unicode=True)
_session_factory = sessionmaker(bind=_engine)
Session = _session_factory()

# Initialize database if it doesn't exist
if not os.path.exists('db.sqlite3'):
    _Base.metadata.create_all(_engine)
