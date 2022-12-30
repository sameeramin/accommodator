from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine, Column, Integer, String, Date
from sqlalchemy.ext.declarative import declarative_base

engine = create_engine('sqlite:///accommodation.db')
Base = declarative_base()


Session = sessionmaker(bind=engine)
session = Session()


class Accommodation(Base):
    __tablename__ = 'accommodations'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    location = Column(String)
    price_per_night = Column(Integer)
    max_guests = Column(Integer)


class Reservation(Base):
    __tablename__ = 'reservations'

    id = Column(Integer, primary_key=True)
    accommodation_id = Column(Integer)
    user_id = Column(Integer)
    start_date = Column(Date)
    end_date = Column(Date)


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer)
    first_name = Column(String)
    last_name = Column(String)
    username = Column(String)


Base.metadata.create_all(engine)
