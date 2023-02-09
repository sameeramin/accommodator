import logging
from telegram.ext import ConversationHandler, CallbackContext
from telegram import Update
from models import session
from helpers import (
    parse_date,
    get_accommodation,
    get_accommodations,
    get_reservations,
    create_reservation,
    get_user,
    create_user
)

SEARCH, SELECT, RESERVE, CONFIRM = range(4)

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)


# Define the bot's description
BOT_DESCRIPTION = """
This is the Accommodation Recommendation Bot, a Telegram bot that helps you find and reserve accommodations. 
Use the /search command to find available accommodations, and the /help command to see a list of available commands.
"""

# Define the bot's commands
BOT_COMMANDS = """
Available commands:

/start - Start the bot
/help - Show this list of commands
/search - Search for available accommodations and reserve
/cancel - Cancel your ongoing reservation
/reservations - Check you reservations
"""


def start(update: Update, context: CallbackContext):
    # Get the user's details and store them in the context and database
    user = update.effective_user
    context.user_data['user'] = user

    db_user = get_user(user)
    if db_user is None:
        create_user(user)

    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"Hello {user.full_name}, Welcome to the Accommodator Bot!\n {BOT_DESCRIPTION}\n{BOT_COMMANDS}"
    )


def bot_help(update: Update, context: CallbackContext):
    # Send a message with a list of available commands
    context.bot.send_message(chat_id=update.effective_chat.id, text=BOT_COMMANDS)


def reservations(update: Update, context: CallbackContext):
    # Get the user's reservations
    results = get_reservations(update.effective_user.id)
    if not results:
        update.message.reply_text("You have no reservations.")
        return
    message = "Your reservations:\n\n"
    for result in results:
        message += f"{result.name} - from {result.start_date} to {result.end_date} \n"

    # Send the message to the user
    context.bot.send_message(chat_id=update.effective_chat.id, text=message)


def search(update: Update, context: CallbackContext):
    # Get the available accommodations
    accommodations = get_accommodations()

    # Set the user's state
    context.user_data["state"] = SELECT

    # Send the message to the user
    update.message.reply_text(accommodations)
    return SELECT


def select(update: Update, context: CallbackContext):
    # Get the user's current conversation state
    state = context.user_data.get("state", "")
    if state != SELECT:
        update.message.reply_text(
            "You are not currently selecting an accommodation. Use the /search command to get started.")
        return

    try:
        aid = int(update.message.text)
        # Get the selected accommodation
        accommodation = get_accommodation(aid)
        if not accommodation:
            raise ValueError

    except ValueError:
        update.message.reply_text("Please provide a valid id for the accommodation you want to select.")
        return

    # Set the user's state to "reserving_accommodation"
    context.user_data["state"] = RESERVE
    context.user_data["accommodation"] = accommodation

    # Send a message to the user asking for the reservation dates
    update.message.reply_text("Please provide the dates for your reservation (e.g., 2022-12-24 2022-12-25).")

    return RESERVE


def reserve(update: Update, context: CallbackContext):
    # Get the user's current conversation state
    state = context.user_data.get("state", "")
    if state != RESERVE:
        update.message.reply_text(
            "You are not currently reserving an accommodation. Use the /search command to find one."
        )
        return ConversationHandler.END

    # Get the selected accommodation
    accommodation = context.user_data["accommodation"]

    try:
        start_date, end_date = map(parse_date, update.message.text.split())
    except ValueError:
        update.message.reply_text("Please provide valid dates for your reservation (e.g., 2022-12-24 2022-12-25).")
        return RESERVE

    # Create a new reservation for the selected accommodation
    reservation = create_reservation(accommodation, update.effective_user.id, start_date, end_date)

    # Set the user's state to "confirming_reservation"
    context.user_data["state"] = CONFIRM
    context.user_data["reservation"] = reservation

    # Send a message to the user confirming the reservation details
    message = f"You have reserved the {accommodation.name} from {start_date} to {end_date}. Is this correct?"
    update.message.reply_text(message)

    return CONFIRM


def confirm(update: Update, context: CallbackContext):
    # Get the user's current conversation state
    state = context.user_data.get("state", "")
    if state != CONFIRM:
        update.message.reply_text(
            "You are not currently confirming a reservation. Use the /search command to find one."
        )
        return ConversationHandler.END

    # Get the user's reservation
    reservation = context.user_data["reservation"]

    if update.message.text.lower() in ["yes", "y", "yeah", "sure", "ok", "okay"]:
        # Save the reservation to the database
        session.add(reservation)
        session.commit()
        update.message.reply_text("Your reservation has been confirmed.")

    else:
        update.message.reply_text("Your reservation has been cancelled.")

    # Reset the user's state and data
    context.user_data.clear()
    return ConversationHandler.END


def cancel(update: Update, context: CallbackContext):
    print("cancel", context.user_data)
    # Reset the user's state and data
    context.user_data.clear()
    update.message.reply_text("The reservation process has been cancelled.")
    return ConversationHandler.END


def error(update: Update, context: CallbackContext):
    print("error", context.user_data)
    """Log Errors caused by Updates."""
    context.user_data.clear()
    logger.warning('Update "%s" caused error "%s"', update, context.error)
    update.message.reply_text(
        "An error occurred. Please try again by using the /search command or /help for more information."
    )
    return ConversationHandler.END
