import os
import logging
from datetime import datetime
from dotenv import load_dotenv
from sqlalchemy import create_engine, Column, Integer, String, Date
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters

load_dotenv(os.path.join(os.getcwd(), '.env'))

engine = create_engine('sqlite:///accommodation.db')
Base = declarative_base()


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

Session = sessionmaker(bind=engine)
session = Session()

TOKEN = os.environ.get('TELEGRAM_TOKEN')
updater = Updater(token=TOKEN, use_context=True)

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Define the bot's description
BOT_DESCRIPTION = "This is the Accommodation Bot, a Telegram bot that helps you find and reserve accommodations. Use " \
                  "the /search command to find available accommodations, and the /help command to see a list of " \
                  "available commands. "

# Define the bot's commands
BOT_COMMANDS = """
Available commands:

/start - Start the bot
/help - Show this list of commands
/search - Search for available accommodations
/select <Id> - Select an accommodation to reserve
"""


def start(update, context):
    # Get the user's details and store them in the context and database
    user = update.effective_user
    context.user_data['user'] = user

    db_user = session.query(User).filter(User.telegram_id == user.id).first()
    if db_user is None:
        new_user = User(telegram_id=user.id, first_name=user.first_name,
                        last_name=user.last_name, username=user.username)
        session.add(new_user)
        session.commit()

    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"Hello {user.full_name}, Welcome to the Accommodator Bot!\n {BOT_DESCRIPTION}\n\n{BOT_COMMANDS}"
    )


def bot_help(update, context):
    # Send a message with a list of available commands
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"Here are the available commands:\n\n"
             "/start - Start the bot\n"
             "/help - Show this list of commands\n"
             "/search - Search for available accommodations\n"
             "/select <Id> - Select an accommodation to reserve\n"
    )


def search(update, context):
    # Query the database for available accommodations
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

    accommodation_strings.append("\n Please select an accommodation by entering the Id like: `/select 1`")
    # Send the list of accommodations to the user
    context.bot.send_message(chat_id=update.effective_chat.id, text='\n'.join(accommodation_strings))


def select(update, context):
    # Get the user's selection
    selection = update.message.text.split(" ")[1]

    # Query the database for the selected accommodation
    accommodation = session.query(Accommodation).filter(Accommodation.id == selection).first()

    if accommodation is None:
        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text="Sorry, we could not find the selected accommodation. Please try again.")
        return

    # Update the context with the selected accommodation
    context.user_data['selected_accommodation'] = accommodation
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Great! You have selected the following accommodation: \n\n"
             f"{accommodation.name} ({accommodation.location}): ${accommodation.price_per_night} per night, max guests:"
             f"{accommodation.max_guests}\n\n Please enter the start and end dates for your reservation in the format"
             "\n'/reserve YYYY-MM-DD YYYY-MM-DD':")


def reserve(update, context):
    # Get the start and end dates from the user's message
    dates = update.message.text.split(' ')
    start_date = datetime.strptime(dates[1], '%Y-%m-%d').date()
    end_date = datetime.strptime(dates[2], '%Y-%m-%d').date()

    # Get the selected accommodation from the context
    accommodation = context.user_data['selected_accommodation']

    # Check if the accommodation is available for the given dates
    reservations = session.query(Reservation).filter(
        Reservation.accommodation_id == accommodation.id,
        Reservation.start_date <= end_date,
        Reservation.end_date >= start_date
    ).all()

    if reservations:
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Sorry, the selected accommodation is not available for the given dates."
                 " Please try again with different dates."
        )
        return

    # Update the max_guests value of the accommodation
    accommodation.max_guests -= 1
    session.add(accommodation)
    session.commit()

    # Create a new reservation
    user = context.user_data['user']
    new_reservation = Reservation(
        accommodation_id=accommodation.id,
        user_id=user.id,
        start_date=start_date,
        end_date=end_date
    )
    session.add(new_reservation)
    session.commit()

    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Your reservation has been confirmed! Thank you for using the Accommodator Bot."
    )


start_handler = CommandHandler('start', start)
help_handler = CommandHandler('help', bot_help)
search_handler = CommandHandler('search', search)
select_handler = CommandHandler('select', select)
reserve_handler = CommandHandler('reserve', reserve)

updater.dispatcher.add_handler(start_handler)
updater.dispatcher.add_handler(help_handler)
updater.dispatcher.add_handler(search_handler)
updater.dispatcher.add_handler(select_handler)
updater.dispatcher.add_handler(reserve_handler)

updater.start_polling()
