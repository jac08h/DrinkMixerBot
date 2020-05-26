import os
import logging

from app import app
from app.DrinkMixerBot import DrinkMixerBot

basedir = os.path.abspath(os.path.dirname(__file__))

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                        handlers=[logging.StreamHandler()]
                        )
    try:
        token = os.environ['TELEGRAM_TOKEN']
    except KeyError:
        print('Missing token. You did not provide the TELEGRAM_TOKEN environment variable.')
        exit()

    try:
        database_url = os.environ['DATABASE_URL']
    except KeyError:
        print('Missing database url. You did not provide the DATABASE_URL environment variable.')
        exit()

    port = int(os.environ.get('PORT', 8443))

    bot = DrinkMixerBot(token, database_url)
    # bot.start_webhook('https://drink-mixer-bot.herokuapp.com/', port)
    bot.start_local()
