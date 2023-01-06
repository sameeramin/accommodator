import datetime
from models import Accommodation, Reservation, User, session


def get_accommodations():
    # Query the database for available accommodations and return them as formatted strings
    accommodations = session.query(Accommodation).filter(Accommodation.max_guests > 0).all()

    # Build a list of strings representing the accommodations
    accommodation_strings = [
        "Here are the available accommodations:\n",
        "| Id | Hotel name (Location) | Price per night | max guests |"
    ]
    for accommodation in accommodations:
        accommodation_strings.append(
            f"| {accommodation.id} | {accommodation.name} ({accommodation.location})| ${accommodation.price_per_night}"
            f" per night | max guests: {accommodation.max_guests} |"
        )

    return '\n'.join(accommodation_strings)


def get_accommodation(aid):
    # Query database with the given id
    accommodation = session.query(Accommodation).filter(Accommodation.id == aid).first()
    return accommodation


def create_reservation(accommodation, user_id, start_date, end_date):
    # Create new reservation record in the database
    reservation = Reservation(
        accommodation_id=accommodation.id,
        user_id=user_id,
        start_date=start_date,
        end_date=end_date
    )
    # Update the max_guests value of the accommodation
    accommodation.max_guests -= 1
    session.add(accommodation)
    session.commit()
    return reservation


def get_reservations(user_id):
    # Query the database for reservations for the given user
    reservations = session.query(Reservation).filter(Reservation.user_id == user_id).all()
    # add the accommodation name to the reservation
    for reservation in reservations:
        reservation.name = session.query(Accommodation).filter(
            Accommodation.id == reservation.accommodation_id).first().name

    return reservations


def get_user(user):
    user = session.query(User).filter(User.telegram_id == user.id).first()
    return user


def create_user(user):
    new_user = User(telegram_id=user.id, first_name=user.first_name,
                    last_name=user.last_name, username=user.username)
    session.add(new_user)
    session.commit()


def parse_date(date_string):
    try:
        return datetime.datetime.strptime(date_string, "%Y-%m-%d").date()
    except ValueError:
        return
