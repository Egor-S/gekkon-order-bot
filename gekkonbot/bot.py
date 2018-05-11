import os
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ParseMode
from telegram.ext import Updater, CommandHandler, ConversationHandler, CallbackQueryHandler, RegexHandler
from telegram.ext.filters import InvertedFilter, Filters
from .spreadsheets import ItemsCatalog, OrderList, get_credentials


class Text:
    """
    Enum of messages
    """
    CHOOSE_CATEGORY = "_Выберите категорию:_"
    CHOOSE_ITEM = "_Выберите позицию:_"
    CONFIRM_ITEM = "_Подтвердите позицию:_\n*{}*\n{}"
    CONFIRMED_ITEM = "*{}*\n{}"
    CHOOSE_COUNT = "_Укажите количество (только цифрами):_"
    DONE = "Заказ №{} на *{}* {}шт успешно создан."
    PRODUCTION = "Заказ №{}\n*[{}] {} {}шт*\nСотрудник: `{}`"


class State:
    """
    Enum of states
    """
    CHOOSE_CATEGORY = 1
    CHOOSE_ITEM = 2
    CONFIRM_ITEM = 3
    CHOOSE_COUNT = 4


def start_command(bot, update):
    """
    Initial information for user
    """
    update.message.reply_text(START_MSG)


def order_command(bot, update):
    """
    Start ordering process
    """
    update.message.reply_text(Text.CHOOSE_CATEGORY, reply_markup=get_category_menu(),
                              parse_mode=ParseMode.MARKDOWN)
    return State.CHOOSE_CATEGORY


def category_callback(bot, update, user_data):
    """
    Choose category and show available items
    """
    query = update.callback_query
    bot.answer_callback_query(query.id)  # To stop loading circles on buttons
    user_data['category'] = int(query.data)
    bot.edit_message_text(text=Text.CHOOSE_ITEM, reply_markup=get_items_menu(user_data['category']),
                          chat_id=query.message.chat_id, message_id=query.message.message_id,
                          parse_mode=ParseMode.MARKDOWN)
    return State.CHOOSE_ITEM


def items_callback(bot, update, user_data):
    """
    Choose item and show description
    """
    query = update.callback_query
    bot.answer_callback_query(query.id)  # To stop loading circles on buttons
    if 'back' in query.data.lower():
        del user_data['category']
        bot.edit_message_text(text=Text.CHOOSE_CATEGORY, reply_markup=get_category_menu(),
                              chat_id=query.message.chat_id, message_id=query.message.message_id,
                              parse_mode=ParseMode.MARKDOWN)
        return State.CHOOSE_CATEGORY
    user_data['item'] = int(query.data)
    item = ic.get(user_data['category'], user_data['item'])
    bot.edit_message_text(text=Text.CONFIRM_ITEM.format(item[1], item[2]), reply_markup=get_confirm_menu(),
                          chat_id=query.message.chat_id, message_id=query.message.message_id,
                          parse_mode=ParseMode.MARKDOWN)
    return State.CONFIRM_ITEM


def confirm_item_callback(bot, update, user_data):
    """
    Confirm or reject item
    """
    query = update.callback_query
    bot.answer_callback_query(query.id)  # To stop loading circles on buttons
    if 'back' in query.data.lower():
        del user_data['item']
        bot.edit_message_text(text=Text.CHOOSE_ITEM, reply_markup=get_items_menu(user_data['category']),
                              chat_id=query.message.chat_id, message_id=query.message.message_id,
                              parse_mode=ParseMode.MARKDOWN)
        return State.CHOOSE_ITEM
    else:
        item = ic.get(user_data['category'], user_data['item'])
        bot.edit_message_text(text=Text.CONFIRMED_ITEM.format(item[1], item[2]),
                              chat_id=query.message.chat_id, message_id=query.message.message_id,
                              parse_mode=ParseMode.MARKDOWN)
        bot.send_message(text=Text.CHOOSE_COUNT, chat_id=query.message.chat_id,
                         parse_mode=ParseMode.MARKDOWN)
        return State.CHOOSE_COUNT


def count_handler(bot, update, user_data):
    """
    Put order in DB and notify in channel
    """
    count = int(update.message.text)
    item = ic.get(user_data['category'], user_data['item'])
    name = update.message.from_user.name
    order_id = ol.new(item, count, name)
    update.message.reply_text(Text.DONE.format(order_id, item[1], count),
                              parse_mode=ParseMode.MARKDOWN)
    try:
        bot.send_message(text=Text.PRODUCTION.format(order_id, item[0], item[1], count, name),
                         chat_id=PRODUCTION_CHAT_ID, parse_mode=ParseMode.MARKDOWN)
    except Exception:
        print("Can't send message to notification chat")
    return ConversationHandler.END


def abort_command(bot, update):
    """
    Abort ordering process
    """
    update.message.reply_text("Заказ прерван")
    return ConversationHandler.END


def chatid_command(bot, update):
    """
    Send chat id
    """
    chat_id = update.message.chat_id
    bot.send_message(text="chat_id: {}".format(chat_id), chat_id=chat_id)


def forceupdate_command(bot, update):
    """
    Force update of catalog
    """
    ic.last_update = 0
    ic.all()
    bot.send_message(text="База успешно обновлена", chat_id=update.message.chat_id)


def error_handler(bot, update, telegram_error):
    """
    Error handler (seriously?!)
    """
    print("Error occured: ", telegram_error)


def get_token(token_path):
    """
    :param token_path: Path to token file
    :return: Token
    """
    with open(token_path, "r") as f:
        token = f.read()
    return token.strip()


def get_category_menu():
    """
    :return:  InlineKeyboardMarkup
    """
    categories = ic.get_categories()
    keyboard = []
    for i, title in categories:
        keyboard.append([InlineKeyboardButton(title, callback_data=str(i))])
    markup = InlineKeyboardMarkup(keyboard)
    return markup


def get_items_menu(category):
    """
    :param category: Category id
    :return: InlineKeyboardMarkup
    """
    subcatalog = ic.get_category(category)
    keyboard = []
    for i in range(len(subcatalog)):
        button = InlineKeyboardButton(subcatalog[i][1], callback_data=str(subcatalog[i][0]))
        if i % 2:
            keyboard[-1].append(button)
        else:
            keyboard.append([button])
    keyboard.append([InlineKeyboardButton("Назад", callback_data="back")])
    markup = InlineKeyboardMarkup(keyboard)
    return markup


def get_confirm_menu():
    """
    :return: InlineKeyboardMarkup
    """
    keyboard = [
        [
            InlineKeyboardButton("Далее", callback_data="next"),
            InlineKeyboardButton("Назад", callback_data="back")
        ]
    ]
    markup = InlineKeyboardMarkup(keyboard)
    return markup


def init(catalog_id, orders_id, secrets_dir, chat_id, start_msg, proxy=None):
    """
    :param catalog_id: Google spreadsheet id
    :param orders_id: Google spreadsheet id
    :param secrets_dir: Directory with secrets
    :param chat_id: Production chat id (for notifications)
    :param proxy: Tuple (url, username, password) for proxy or None
    :return: Updated object
    """
    global ic, ol, PRODUCTION_CHAT_ID, START_MSG
    credentials = get_credentials(os.path.join(secrets_dir, "google_service.json"))
    ic = ItemsCatalog(credentials, catalog_id)
    ol = OrderList(credentials, orders_id)
    PRODUCTION_CHAT_ID = chat_id
    START_MSG = start_msg

    request_kwargs = {}
    # proxy setup
    if proxy is not None:
        request_kwargs['proxy_url'] = proxy[0]
        request_kwargs['urllib3_proxy_kwargs'] = {
            'username': proxy[1],
            'password': proxy[2]
        }

    updater = Updater(get_token(os.path.join("telegram.secret")), request_kwargs=request_kwargs)
    updater.dispatcher.add_handler(CommandHandler('start', start_command, filters=InvertedFilter(Filters.group)))
    # Order process
    conversation_handler = ConversationHandler(
        entry_points=[CommandHandler('order', order_command, filters=InvertedFilter(Filters.group))],
        states={
            State.CHOOSE_CATEGORY: [CallbackQueryHandler(category_callback, pass_user_data=True)],
            State.CHOOSE_ITEM: [CallbackQueryHandler(items_callback, pass_user_data=True)],
            State.CONFIRM_ITEM: [CallbackQueryHandler(confirm_item_callback, pass_user_data=True)],
            State.CHOOSE_COUNT: [RegexHandler(r"^[0-9]+$", count_handler, pass_user_data=True)]
        },
        fallbacks=[CommandHandler('abort', abort_command, filters=InvertedFilter(Filters.group))]
    )
    updater.dispatcher.add_handler(conversation_handler)
    updater.dispatcher.add_handler(CommandHandler('chatid', chatid_command))
    updater.dispatcher.add_handler(CommandHandler('forceupdate', forceupdate_command))

    updater.dispatcher.add_error_handler(error_handler)
    return updater
