from gekkonbot.bot import init
from gekkonbot.config import config


if __name__ == '__main__':
    updater = init(config)
    print("Logged in as {}".format(updater.bot.get_me().name))
    updater.start_polling()
    updater.idle()
