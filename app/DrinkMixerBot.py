import logging

from telegram.ext import Updater, CommandHandler, MessageHandler, ConversationHandler, Filters
from telegram import KeyboardButton, ReplyKeyboardMarkup, ParseMode

import app.drinks_api as dr
from app.exceptions import *
from app.models import User

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from datetime import datetime

logger = logging.getLogger(__name__)

emojis = {'tropical_drink': '🍹'}

DRINK_RECEIVED, CANCEL = 0, 1

class DrinkMixerBot:
    def __init__(self, token, database_url):
        self.token = token
        self.updater = Updater(token=token)
        self.dispatcher = self.updater.dispatcher

        engine = create_engine(database_url)
        Session = sessionmaker(bind=engine)
        self.session = Session()

        start_handler = CommandHandler('start', self.menu)
        menu_handler = CommandHandler('menu', self.menu)
        cancel_handler = CommandHandler('cancel', self.cancel_conversation)

        usage_handler = CommandHandler('usage', self.usage)
        random_drink_handler = CommandHandler('random_drink', self.random_drink)
        repeat_ingredients_handler = CommandHandler('repeat_ingredients', self.repeat_ingredients, pass_user_data=True)
        by_ingredients_handler = MessageHandler(Filters.text, self.ingredients_received, pass_user_data=True)
        get_drink_handler = ConversationHandler(
            entry_points=[CommandHandler('find_drink', self.drink_command_received)],
            states={
                DRINK_RECEIVED: [MessageHandler(Filters.text, self.drink_name_received)],
                CANCEL: [cancel_handler]
            },
            fallbacks=[cancel_handler]
        )


        handlers = [start_handler,
                    menu_handler,
                    usage_handler,

                    random_drink_handler,
                    repeat_ingredients_handler,

                    get_drink_handler,
                    by_ingredients_handler,
                    ]

        for handler in handlers:
            self.dispatcher.add_handler(handler)

    def usage(self, bot, update):
        u = """Enter your ingredients (separated by *,*) like *rum,coffee*.
        
*/repeat_ingredients* - get another drink with same ingredients

*/random_drink* - completely random drink

*/find_drink* - get drink information

*/usage* - show this message."""



        bot.send_message(chat_id=update.message.chat_id, text=u, parse_mode=ParseMode.MARKDOWN)

    def update_user_in_database(self, user_id):
        user = self.session.query(User).filter(User.id == user_id).first()
        time = datetime.now()
        if user is None:
            user = User(id=user_id, date_started=time, date_last_used=time)
        else:
            user.update_time(time)

        self.session.add(user)
        self.session.commit()

    def cancel_conversation(self, bot, update):
        self.display_menu_keyboard(bot, update, emojis['tropical_drink'])
        return ConversationHandler.END

    def drink_command_received(self, bot, update):
        bot.send_message(chat_id=update.message.chat_id, text='Enter a drink name or /cancel', parse_mode=ParseMode.MARKDOWN)
        return DRINK_RECEIVED

    def drink_name_received(self, bot, update):
        drink_name = update.message.text
        try:
            drink_dict = dr.get_drink_by_name(drink_name)
            self.send_drink(bot, update, drink_dict)
        except NoDrinksFound:
            bot.send_message(chat_id=update.message.chat_id, text=f'Drink *{drink_name}* not found.', parse_mode=ParseMode.MARKDOWN)

        bot.send_message(chat_id=update.message.chat_id, text='Enter another drink or /cancel')


    def random_drink(self, bot, update):
        user_id = update.message.chat.id
        self.update_user_in_database(user_id)

        drink = dr.get_random_drink()
        self.send_drink(bot, update, drink)

    def ingredients_received(self, bot, update, user_data):
        user_id = update.message.chat.id
        self.update_user_in_database(user_id)

        ingredients = update.message.text
        ingredients = [i.lower().strip() for i in ingredients.split(',')]
        ingredients = ','.join(ingredients)
        try:
            drink_id = dr.get_random_drink_id_by_ingredients(ingredients)
            drink_dict = dr.get_drink_by_id(drink_id)
            self.send_drink(bot, update, drink_dict)

            user_data['ingredients'] = ingredients

        except NoDrinksFound:
            self.display_menu_keyboard(bot, update, f'No drinks containing *{ingredients}* found.')


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

    def menu(self, bot, update):
        user_id = update.message.chat.id
        self.update_user_in_database(user_id)

        self.display_menu_keyboard(bot, update, emojis['tropical_drink'])


    def display_menu_keyboard(self, bot, update, text):
        menu_options = [
            [KeyboardButton('/random_drink')],
            [KeyboardButton('/repeat_ingredients')],
            [KeyboardButton('/find_drink')],
            [KeyboardButton('/usage')]
        ]

        keyboard = ReplyKeyboardMarkup(menu_options)
        bot.send_message(chat_id=update.message.chat_id,
                         text=text,
                         parse_mode=ParseMode.MARKDOWN,
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