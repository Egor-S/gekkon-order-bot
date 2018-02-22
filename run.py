import os
from gekkonbot.bot import init

CATALOG_TABLE_ID = ""  # TODO CHANGE
ORDERS_TABLE_ID = ""  # TODO CHANGE
SECRETS_DIR = os.getcwd()
PRODUCTION_CHAT_ID = -0  # TODO CHANGE


if __name__ == '__main__':
    updater = init(CATALOG_TABLE_ID, ORDERS_TABLE_ID, SECRETS_DIR, PRODUCTION_CHAT_ID)
    print("Logged in as {}".format(updater.bot.get_me().name))
    updater.start_polling()
    updater.idle()
