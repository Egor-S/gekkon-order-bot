from gekkonbot.bot import init
from config import CATALOG_TABLE_ID, ORDERS_TABLE_ID, PRODUCTION_CHAT_ID, SECRETS_DIR


if __name__ == '__main__':
    updater = init(CATALOG_TABLE_ID, ORDERS_TABLE_ID, SECRETS_DIR, PRODUCTION_CHAT_ID)
    print("Logged in as {}".format(updater.bot.get_me().name))
    updater.start_polling()
    updater.idle()
