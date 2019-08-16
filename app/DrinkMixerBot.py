import logging

from telegram.ext import Updater, CommandHandler
from telegram import KeyboardButton, ReplyKeyboardMarkup

import app.drinks_api as dr

logger = logging.getLogger(__name__)

class DrinkMixerBot:
    def __init__(self, token):
        self.token = token
        self.updater = Updater(token=token)
        self.dispatcher = self.updater.dispatcher

        start_handler = CommandHandler('start', self.display_menu)
        menu_handler = CommandHandler('menu', self.display_menu)

        random_drink_handler = CommandHandler('random_drink', self.random_drink)


        handlers = [start_handler,
                    menu_handler,

                    random_drink_handler]

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