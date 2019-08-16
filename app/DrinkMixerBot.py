from telegram.ext import Updater, CommandHandler

class DrinkMixerBot:
    def __init__(self, token):
        self.token = token
        self.updater = Updater(token=token)
        self.dispatcher = self.updater.dispatcher

        start_handler = CommandHandler('start', self.start)

        handlers = [start_handler]

        for handler in handlers:
            self.dispatcher.add_handler(handler)

    def start(self, bot, update):
        bot.send_message(chat_id=update.message.chat_id, text='Hey!')
        return


    def start_webhook(self, url, port):
        self.updater.start_webhook(listen="0.0.0.0",
                                   port=port,
                                   url_path=self.token)
        self.updater.bot.set_webhook(url + self.token)
        self.updater.idle()
        return

    def start_local(self):
        self.updater.start_polling()
        self.updater.idle()