import logging

from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from telegram import KeyboardButton, ReplyKeyboardMarkup, ParseMode

import app.drinks_api as dr
from app.exceptions import *

logger = logging.getLogger(__name__)

emojis = {'tropical_drink': '🍹',
          'question_mark': '❓'}


class DrinkMixerBot:
    def __init__(self, token):
        self.token = token
        self.updater = Updater(token=token)
        self.dispatcher = self.updater.dispatcher


        start_handler = CommandHandler('start', self.display_menu)
        menu_handler = CommandHandler('menu', self.display_menu)
        usage_handler = CommandHandler('usage', self.usage)
        random_drink_handler = CommandHandler('random_drink', self.random_drink)
        repeat_ingredients_handler = CommandHandler('repeat_ingredients', self.repeat_ingredients, pass_user_data=True)
        by_ingredients_handler = MessageHandler(Filters.text, self.ingredients_received, pass_user_data=True)

        handlers = [start_handler,
                    menu_handler,
                    usage_handler,

                    random_drink_handler,
                    by_ingredients_handler,
                    repeat_ingredients_handler,
                    ]

        for handler in handlers:
            self.dispatcher.add_handler(handler)

    def usage(self, bot, update):
        u = """Enter your ingredients (separated by *,*) like *rum,coffee*.
        
*/repeat_ingredients* to get another drink with same ingredients.

*/random_drink* for completely random cocktail.

*/usage* - show this message."""



        bot.send_message(chat_id=update.message.chat_id, text=u, parse_mode=ParseMode.MARKDOWN)


    def random_drink(self, bot, update):
        drink = dr.get_random_drink()
        self.send_drink(bot, update, drink)

    def ingredients_received(self, bot, update, user_data):
        ingredients = update.message.text
        ingredients = [i.strip() for i in ingredients.split(',')]
        ingredients = ','.join(ingredients)
        try:
            drink_id = dr.get_random_drink_id_by_ingredients(ingredients)
            drink_dict = dr.get_drink_by_id(drink_id)
            self.send_drink(bot, update, drink_dict)

            user_data['ingredients'] = ingredients

        except NoDrinksFound:
            bot.send_message(chat_id=update.message.chat_id, text='No drinks found.')


    def repeat_ingredients(self, bot, update, user_data):
        try:
            ingredients = user_data['ingredients']
            drink_id = dr.get_random_drink_id_by_ingredients(ingredients)
            drink_dict = dr.get_drink_by_id(drink_id)
            self.send_drink(bot, update, drink_dict)
        except KeyError:
            bot.send_message(chat_id=update.message.chat_id, text='Nothing to repeat.')


    def send_drink(self, bot, update, drink_dict):
        drink_dict = dr.clean_up_ingredients(drink_dict)

        name = drink_dict['strDrink']
        img = drink_dict['strDrinkThumb']
        ingredients = drink_dict['ingredients']
        instructions = drink_dict['strInstructions']

        bot.send_photo(chat_id=update.message.chat_id, photo=img)
        bot.send_message(chat_id=update.message.chat_id, text=f'*{name}*', parse_mode=ParseMode.MARKDOWN)
        bot.send_message(chat_id=update.message.chat_id, text=ingredients)
        bot.send_message(chat_id=update.message.chat_id, text=f'_{instructions}_', parse_mode=ParseMode.MARKDOWN)

    def display_menu(self, bot, update):
        menu_options = [
            [KeyboardButton('/random_drink')],
            [KeyboardButton('/repeat_ingredients')],
            [KeyboardButton('/usage')]
        ]

        keyboard = ReplyKeyboardMarkup(menu_options)
        bot.send_message(chat_id=update.message.chat_id,
                         text=emojis['tropical_drink'],
                         reply_markup=keyboard)

    def start_webhook(self, url, port):
        self.updater.start_webhook(listen="0.0.0.0",
                                   port=port,
                                   url_path=self.token)
        self.updater.bot.set_webhook(url + self.token)
        self.updater.idle()

    def start_local(self):
        self.updater.start_polling()
        self.updater.idle()