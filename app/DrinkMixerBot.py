import logging

from telegram.ext import Updater, CommandHandler, ConversationHandler, MessageHandler, Filters
from telegram import KeyboardButton, ReplyKeyboardMarkup

import app.drinks_api as dr
from app.exceptions import *

logger = logging.getLogger(__name__)

INGREDIENT_RECEIVED, CANCEL = 0, 1

class DrinkMixerBot:
    def __init__(self, token):
        self.token = token
        self.updater = Updater(token=token)
        self.dispatcher = self.updater.dispatcher

        start_handler = CommandHandler('start', self.display_menu)
        menu_handler = CommandHandler('menu', self.display_menu)
        cancel_handler = CommandHandler('cancel', self.cancel_conversation)
        random_drink_handler = CommandHandler('random_drink', self.random_drink)

        enter_ingredient_handler = ConversationHandler(
            entry_points= [CommandHandler('enter_ingredient', self.enter_ingredient_prompt)],
            states={
                INGREDIENT_RECEIVED: [MessageHandler(Filters.text, self.ingredient_received)],
                CANCEL: [cancel_handler]},
            fallbacks=[cancel_handler]
        )

        handlers = [start_handler,
                    menu_handler,

                    random_drink_handler,
                    enter_ingredient_handler]

        for handler in handlers:
            self.dispatcher.add_handler(handler)

    def display_menu(self, bot, update):
        """
        Display menu
        """
        menu_options = [
            [KeyboardButton('/enter_ingredient')],
            [KeyboardButton('/random_drink')],
        ]

        keyboard = ReplyKeyboardMarkup(menu_options)
        bot.send_message(chat_id=update.message.chat_id,
                         text="What's up",
                         reply_markup=keyboard)

    def random_drink(self, bot, update):
        drink = dr.get_random_drink()
        self.send_drink(bot, update, drink)

    def enter_ingredient_prompt(self, bot, update):
        bot.send_message(chat_id=update.message.chat_id, text='Enter ingredient')
        return INGREDIENT_RECEIVED

    def ingredient_received(self, bot, update):
        ingredient = update.message.text
        try:
            drink_id = dr.get_random_drink_id_by_ingredient(ingredient)
            drink_dict = dr.get_drink_by_id(drink_id)
            self.send_drink(bot, update, drink_dict)
        except InvalidUserInput:
            bot.send_message(chat_id=update.message.chat_id, text='Invalid ingredient.')


    def cancel_conversation(self, bot, update):
        self.display_menu(bot, update)
        return ConversationHandler.END

    def send_drink(self, bot, update, drink_dict):
        """Send drink picture and info"""

        drink_dict = dr.clean_up_ingredients(drink_dict)

        name = drink_dict['strDrink']
        img = drink_dict['strDrinkThumb']
        ingredients = drink_dict['ingredients']
        instructions = drink_dict['strInstructions']

        bot.send_photo(chat_id=update.message.chat_id, photo=img)
        bot.send_message(chat_id=update.message.chat_id, text=name)
        bot.send_message(chat_id=update.message.chat_id, text=ingredients)
        bot.send_message(chat_id=update.message.chat_id, text=instructions)

    def start_webhook(self, url, port):
        self.updater.start_webhook(listen="0.0.0.0",
                                   port=port,
                                   url_path=self.token)
        self.updater.bot.set_webhook(url + self.token)
        self.updater.idle()

    def start_local(self):
        self.updater.start_polling()
        self.updater.idle()