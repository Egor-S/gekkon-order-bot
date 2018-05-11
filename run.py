from gekkonbot.bot import init
from config import CATALOG_TABLE_ID, ORDERS_TABLE_ID, PRODUCTION_CHAT_ID, SECRETS_DIR, WELCOME_MSG, PROXY


if __name__ == '__main__':
    if PROXY:
        from config import PROXY_URL, PROXY_USER, PROXY_PASS
        updater = init(CATALOG_TABLE_ID, ORDERS_TABLE_ID, SECRETS_DIR,
                       PRODUCTION_CHAT_ID, WELCOME_MSG, proxy=[PROXY_URL, PROXY_USER, PROXY_PASS])
    else:
        updater = init(CATALOG_TABLE_ID, ORDERS_TABLE_ID, SECRETS_DIR, PRODUCTION_CHAT_ID, WELCOME_MSG)
    print("Logged in as {}".format(updater.bot.get_me().name))
    updater.start_polling()
    updater.idle()
