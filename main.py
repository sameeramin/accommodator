import os
from dotenv import load_dotenv
from telegram.ext import Updater, CommandHandler, ConversationHandler, MessageHandler, Filters
from handlers import (
    start,
    bot_help,
    reservations,
    search,
    select,
    reserve,
    confirm,
    cancel,
    error,
    SEARCH,
    SELECT,
    RESERVE,
    CONFIRM
)

load_dotenv(os.path.join(os.getcwd(), '.env'))

TOKEN = os.environ.get('TELEGRAM_TOKEN')
updater = Updater(token=TOKEN, use_context=True)
dispatcher = updater.dispatcher

# Define the conversation handler
conversation_handler = ConversationHandler(
    entry_points=[CommandHandler("search", search)],
    states={
        SEARCH: [MessageHandler(Filters.text, search)],
        SELECT: [MessageHandler(Filters.text, select)],
        RESERVE: [MessageHandler(Filters.text, reserve)],
        CONFIRM: [MessageHandler(Filters.text, confirm)]
    },
    fallbacks=[CommandHandler("cancel", cancel)]
)

# Add the conversation handler to the dispatcher
dispatcher.add_handler(CommandHandler("start", start))
dispatcher.add_handler(CommandHandler("help", bot_help))
dispatcher.add_handler(CommandHandler("reservations", reservations))
dispatcher.add_handler(conversation_handler)
dispatcher.add_error_handler(error)

updater.start_polling()

