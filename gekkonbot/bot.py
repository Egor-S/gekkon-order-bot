import os
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ParseMode
from telegram.ext import Updater, CommandHandler, ConversationHandler, CallbackQueryHandler, RegexHandler, MessageHandler
from telegram.ext.filters import InvertedFilter, Filters
from .spreadsheets import ItemsCatalog, OrderList, DestinationList, get_credentials


class Text:
    """
    Enum of messages
    """
    CHOOSE_CATEGORY = "_Выберите категорию:_"
    CHOOSE_ITEM = "_Выберите позицию:_"
    CONFIRM_ITEM = "_Подтвердите позицию:_\n*[{}] {}*\n{}"
    CONFIRMED_ITEM = "*{}*\n{}"
    CHOOSE_COUNT = "_Укажите количество (только цифрами):_"
    SET_DEADLINE = "_Введите дату дедлайна (в формате 23.02):_"
    SET_COMMENT = "Введите комментарий к заказу _(опционально)_:"
    DONE = "Заказ №{} на *{}* {}шт успешно создан.\nДедлайн: {}\nНазначение: {}\nКомментарий: {}"
    ABORTED = "_Оформление заказа отменено_"
    PRODUCTION = "Заказ №{}\n*[{}] {} {}шт*\nСотрудник: `{}`\nДедлайн: {}\nНазначение: {}\nКомментарий: {}"
    SET_DESTINATION = "Введите поисковый запрос для выбора площадки-назначения:"
    DESTINATION_LIST = "По запросу *{}* найдено площадок: {}. Повторите поиск, если нужная площадка не найдена."


class State:
    """
    Enum of states
    """
    CHOOSE_CATEGORY = 1
    CHOOSE_ITEM = 2
    CONFIRM_ITEM = 3
    CHOOSE_COUNT = 4
    SET_DEADLINE = 5
    SET_COMMENT = 6
    SET_DESTINATION = 7


def put_order(bot, update, user_data, callback=False):
    deadline = user_data['deadline']
    count = user_data['count']
    item = ic.get(user_data['category'], user_data['item'])
    dl.update_recent(user_data['destination'])
    dst = dl.get(user_data['destination'])
    comment = user_data['comment']
    query_or_update = update.message if not callback else update.callback_query
    name = query_or_update.from_user.name
    order_id = ol.new(item, count, name, deadline, dst, comment)
    query_or_update = update if not callback else update.callback_query
    query_or_update.message.reply_text(Text.DONE.format(order_id, item[1], count, deadline, dst, comment),
                                       parse_mode=ParseMode.MARKDOWN)
    try:
        bot.send_message(text=Text.PRODUCTION.format(order_id, item[0], item[1], count, name, deadline, dst, comment),
                         chat_id=PRODUCTION_CHAT_ID, parse_mode=ParseMode.MARKDOWN)
    except Exception:
        print("Can't send message to notification chat")


def start_command(bot, update):
    """
    Initial information for user
    """
    update.message.reply_text(START_MSG)


def order_command(bot, update, user_data):
    """
    Start ordering process
    """
    message = update.message.reply_text(Text.CHOOSE_CATEGORY, reply_markup=get_category_menu(),
                                        parse_mode=ParseMode.MARKDOWN)
    user_data['keyboard_message'] = message.message_id
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
    bot.edit_message_text(text=Text.CONFIRM_ITEM.format(item[0], item[1], item[2]), reply_markup=get_confirm_menu(),
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
        del user_data['keyboard_message']
        bot.send_message(text=Text.CHOOSE_COUNT, chat_id=query.message.chat_id,
                         parse_mode=ParseMode.MARKDOWN)
        return State.CHOOSE_COUNT


def count_handler(bot, update, user_data):
    """
    Read items count
    """
    user_data['count'] = int(update.message.text)
    update.message.reply_text(text=Text.SET_DEADLINE, parse_mode=ParseMode.MARKDOWN)
    return State.SET_DEADLINE


def deadline_handler(bot, update, user_data):
    """
    Read order deadline
    """
    user_data['deadline'] = update.message.text
    message = update.message.reply_text(text=Text.SET_DESTINATION, reply_markup=get_destinations_menu(dl.get_recent()),
                                        parse_mode=ParseMode.MARKDOWN)
    if len(dl.get_recent()) > 0:
        user_data['keyboard_message'] = message.message_id
    user_data['destination_results'] = None
    return State.SET_DESTINATION


def destination_handler(bot, update, user_data):
    """
    Read query and show search results
    """
    if 'keyboard_message' in user_data:  # more beautiful solution?
        if user_data.get('destination_results', None) is None:
            text = Text.SET_DESTINATION
        else:
            text = Text.DESTINATION_LIST.format(*user_data['destination_results'])
        bot.edit_message_text(text=text, chat_id=update.message.chat_id,
                              message_id=user_data['keyboard_message'], parse_mode=ParseMode.MARKDOWN)
        del user_data['keyboard_message']

    results = dl.search(update.message.text)
    try:
        message = update.message.reply_text(text=Text.DESTINATION_LIST.format(update.message.text, len(results)),
                                            reply_markup=get_destinations_menu(results[:16]), parse_mode=ParseMode.MARKDOWN)
    except:
        print("???", results[:16])
    if len(results) > 0:
        user_data['keyboard_message'] = message.message_id


def destination_callback(bot, update, user_data):
    query = update.callback_query
    bot.answer_callback_query(query.id)  # To stop loading circles on buttons
    user_data['destination'] = query.data

    if 'keyboard_message' in user_data:  # more beautiful solution?
        if user_data.get('destination_results', None) is None:
            text = Text.SET_DESTINATION
        else:
            text = Text.DESTINATION_LIST.format(*user_data['destination_results'])
        bot.edit_message_text(text=text, chat_id=query.message.chat_id,
                              message_id=user_data['keyboard_message'], parse_mode=ParseMode.MARKDOWN)
        del user_data['keyboard_message']

    message = query.message.reply_text(text=Text.SET_COMMENT, reply_markup=get_comment_menu(),
                                        parse_mode=ParseMode.MARKDOWN)
    user_data['keyboard_message'] = message.message_id
    return State.SET_COMMENT


def comment_handler(bot, update, user_data):
    """
    Read order comment
    Put order in DB and notify in channel
    """
    user_data['comment'] = update.message.text
    put_order(bot, update, user_data)
    if 'keyboard_message' in user_data:  # more beautiful solution?
        bot.edit_message_text(text=Text.SET_COMMENT, chat_id=update.message.chat_id,
                              message_id=user_data['keyboard_message'], parse_mode=ParseMode.MARKDOWN)
        del user_data['keyboard_message']
    return ConversationHandler.END


def comment_callback(bot, update, user_data):
    """
    Read order comment
    Put order in DB and notify in channel
    """
    query = update.callback_query
    bot.answer_callback_query(query.id)  # To stop loading circles on buttons
    user_data['comment'] = ""
    put_order(bot, update, user_data, callback=True)
    if 'keyboard_message' in user_data:  # more beautiful solution?
        bot.edit_message_text(text=Text.SET_COMMENT, chat_id=query.message.chat_id,
                              message_id=user_data['keyboard_message'], parse_mode=ParseMode.MARKDOWN)
        del user_data['keyboard_message']
    return ConversationHandler.END


def abort_command(bot, update, user_data):
    """
    Abort ordering process
    """
    if 'keyboard_message' in user_data:
        bot.edit_message_text(text=Text.ABORTED, chat_id=update.message.chat_id,
                              message_id=user_data['keyboard_message'], parse_mode=ParseMode.MARKDOWN)
        del user_data['keyboard_message']
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
    dl.last_update = 0
    dl.all()
    bot.send_message(text="База успешно обновлена", chat_id=update.message.chat_id)


def error_handler(bot, update, telegram_error):
    """
    Error handler (seriously?!)
    """
    print("Error occured: ", telegram_error)


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


def get_destinations_menu(destinations):
    keyboard = []
    for i, (dst, dst_hash) in enumerate(destinations):
        button = InlineKeyboardButton(dst, callback_data=dst_hash)
        if i % 2:
            keyboard[-1].append(button)
        else:
            keyboard.append([button])
    markup = InlineKeyboardMarkup(keyboard)
    return markup


def get_comment_menu():
    keyboard = [[InlineKeyboardButton("Пропустить", callback_data="skip")]]
    markup = InlineKeyboardMarkup(keyboard)
    return markup


def init(config):
    """
    :param config: Config dictionary
    :return: Updated object
    """
    global ic, ol, dl, PRODUCTION_CHAT_ID, START_MSG
    credentials = get_credentials(config['google-credentials-path'])
    ic = ItemsCatalog(credentials, config['catalog'])
    ol = OrderList(credentials, config['orders'])
    dl = DestinationList(credentials, config['destinations'])
    PRODUCTION_CHAT_ID = config['notification-chat']
    START_MSG = config['welcome-message']

    request_kwargs = {}
    # proxy setup
    if 'proxy' in config:
        request_kwargs['proxy_url'] = config['proxy']['url']
        request_kwargs['urllib3_proxy_kwargs'] = {
            'username': config['proxy']['user'],
            'password': config['proxy']['password']
        }

    updater = Updater(config['telegram-token'], request_kwargs=request_kwargs)
    updater.dispatcher.add_handler(CommandHandler('start', start_command, filters=InvertedFilter(Filters.group)))
    # Order process
    conversation_handler = ConversationHandler(
        entry_points=[CommandHandler('order', order_command, filters=InvertedFilter(Filters.group), pass_user_data=True)],
        states={
            State.CHOOSE_CATEGORY: [CallbackQueryHandler(category_callback, pass_user_data=True)],
            State.CHOOSE_ITEM:     [CallbackQueryHandler(items_callback, pass_user_data=True)],
            State.CONFIRM_ITEM:    [CallbackQueryHandler(confirm_item_callback, pass_user_data=True)],
            State.CHOOSE_COUNT:    [RegexHandler(r"^[0-9]+$", count_handler, pass_user_data=True)],
            State.SET_DEADLINE:    [RegexHandler(r"^[0-9]{1,2}\.[0-9]{2}$", deadline_handler, pass_user_data=True)],
            State.SET_DESTINATION: [MessageHandler(Filters.text, destination_handler, pass_user_data=True),
                                    CallbackQueryHandler(destination_callback, pass_user_data=True)],
            State.SET_COMMENT:     [MessageHandler(Filters.text, comment_handler, pass_user_data=True),
                                    CallbackQueryHandler(comment_callback, pass_user_data=True)]
        },
        fallbacks=[CommandHandler('abort', abort_command, filters=InvertedFilter(Filters.group), pass_user_data=True)]
    )
    updater.dispatcher.add_handler(conversation_handler)
    updater.dispatcher.add_handler(CommandHandler('chatid', chatid_command))
    updater.dispatcher.add_handler(CommandHandler('forceupdate', forceupdate_command))

    updater.dispatcher.add_error_handler(error_handler)
    return updater
