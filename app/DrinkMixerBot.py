import logging

from telegram.ext import Updater, CommandHandler, ConversationHandler, MessageHandler, Filters
from telegram import KeyboardButton, ReplyKeyboardMarkup

import app.drinks_api as dr
from app.exceptions import *

logger = logging.getLogger(__name__)

emojis = {'tropical_drink': '🍹',
          'question_mark': '❓'}

INGREDIENT_RECEIVED, DRINK_SENT, CANCEL = 0, 1, 2


class DrinkMixerBot:
    def __init__(self, token):
        self.token = token
        self.updater = Updater(token=token)
        self.dispatcher = self.updater.dispatcher

        start_handler = CommandHandler('start', self.display_menu)
        menu_handler = CommandHandler('menu', self.display_menu)
        cancel_handler = CommandHandler('cancel', self.cancel_conversation)
        random_drink_handler = ConversationHandler(
            entry_points=[CommandHandler('random_drink', self.random_drink)],
            states={
                DRINK_SENT: [CommandHandler('next', self.random_drink)],
                CANCEL: [cancel_handler]},
            fallbacks=[cancel_handler]
        )

        enter_ingredient_handler = ConversationHandler(
            entry_points=[CommandHandler('enter_ingredient', self.enter_ingredient_prompt)],
            states={
                INGREDIENT_RECEIVED: [MessageHandler(Filters.text, self.ingredient_received, pass_user_data=True)],
                DRINK_SENT: [CommandHandler('next', self.next_drink_same_ingredient, pass_user_data=True)],
                CANCEL: [cancel_handler]},
            fallbacks=[cancel_handler]
        )

        default_handler = MessageHandler(Filters.all, self.display_menu)

        handlers = [start_handler,
                    menu_handler,

                    random_drink_handler,
                    enter_ingredient_handler,

                    default_handler]

        for handler in handlers:
            self.dispatcher.add_handler(handler)


    def random_drink(self, bot, update):
        drink = dr.get_random_drink()
        self.send_drink(bot, update, drink)
        self.display_next_cancel_keyboard(bot, update)
        return DRINK_SENT

    def enter_ingredient_prompt(self, bot, update):
        bot.send_message(chat_id=update.message.chat_id, text='Enter ingredient or /cancel')
        return INGREDIENT_RECEIVED

    def ingredient_received(self, bot, update, user_data):
        ingredient = update.message.text
        try:
            drink_id = dr.get_random_drink_id_by_ingredient(ingredient)
            drink_dict = dr.get_drink_by_id(drink_id)
            self.send_drink(bot, update, drink_dict)
            self.display_next_cancel_keyboard(bot, update)

            user_data['ingredient'] = ingredient
            return DRINK_SENT

        except InvalidUserInput:
            bot.send_message(chat_id=update.message.chat_id, text='Invalid ingredient.')

    def next_drink_same_ingredient(self, bot, update, user_data):
        ingredient = user_data['ingredient']
        drink_id = dr.get_random_drink_id_by_ingredient(ingredient)
        drink_dict = dr.get_drink_by_id(drink_id)

        self.send_drink(bot, update, drink_dict)
        self.display_next_cancel_keyboard(bot, update)

        return DRINK_SENT

    def cancel_conversation(self, bot, update):
        self.display_menu(bot, update)
        return ConversationHandler.END

    def send_drink(self, bot, update, drink_dict):
        drink_dict = dr.clean_up_ingredients(drink_dict)

        name = drink_dict['strDrink']
        img = drink_dict['strDrinkThumb']
        ingredients = drink_dict['ingredients']
        instructions = drink_dict['strInstructions']

        bot.send_photo(chat_id=update.message.chat_id, photo=img)
        bot.send_message(chat_id=update.message.chat_id, text=name)
        bot.send_message(chat_id=update.message.chat_id, text=ingredients)
        bot.send_message(chat_id=update.message.chat_id, text=instructions)

    def display_menu(self, bot, update):
        menu_options = [
            [KeyboardButton('/enter_ingredient')],
            [KeyboardButton('/random_drink')],
        ]

        keyboard = ReplyKeyboardMarkup(menu_options)
        bot.send_message(chat_id=update.message.chat_id,
                         text=emojis['tropical_drink'],
                         reply_markup=keyboard)

    def display_next_cancel_keyboard(self, bot, update):
        options = [
            [KeyboardButton('/next')],
            [KeyboardButton('/cancel')]
        ]

        keyboard = ReplyKeyboardMarkup(options)
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
