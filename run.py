from gekkonbot.bot import init
from gekkonbot.config import config
# from config import CATALOG_TABLE_ID, ORDERS_TABLE_ID, PRODUCTION_CHAT_ID, SECRETS_DIR, WELCOME_MSG, PROXY


if __name__ == '__main__':
    updater = init(config)
    print("Logged in as {}".format(updater.bot.get_me().name))
    updater.start_polling()
    updater.idle()
