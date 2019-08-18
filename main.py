import os
import logging

from app.DrinkMixerBot import DrinkMixerBot

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

    port = int(os.environ.get('PORT', 8443))

    bot = DrinkMixerBot(token)
    bot.start_webhook('https://drink-mixer-bot.herokuapp.com/', port)
