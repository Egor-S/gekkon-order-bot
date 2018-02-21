from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, ConversationHandler, CallbackQueryHandler, RegexHandler
from spreadsheets import ItemsCatalog, get_credentials  # TODO add .


class State:
    """
    Enum of states
    """
    CHOOSE_CATEGORY = 1
    CHOOSE_ITEM = 2
    CONFIRM_ITEM = 3
    CHOOSE_COUNT = 4
    CONFIRM_COUNT = 5


def start_command(bot, update):
    """
    Initial information for user
    """
    update.message.reply_text("Для начала оформления заявки отправьте /order")


def order_command(bot, update):
    """
    Start ordering process
    """
    update.message.reply_text("Выберите категорию", reply_markup=get_category_menu())
    return State.CHOOSE_CATEGORY


def category_callback(bot, update, user_data):
    """
    Choose category and show available items
    """
    query = update.callback_query
    user_data['category'] = int(query.data)
    bot.edit_message_text(text="Выберите позицию", reply_markup=get_items_menu(user_data['category']),
                          chat_id=query.message.chat_id, message_id=query.message.message_id)
    return State.CHOOSE_ITEM


def items_callback(bot, update, user_data):
    """
    Choose item and show description
    """
    query = update.callback_query
    if 'back' in query.data.lower():
        del user_data['category']
        bot.edit_message_text(text="Выберите категорию", reply_markup=get_category_menu(),
                              chat_id=query.message.chat_id, message_id=query.message.message_id)
        return State.CHOOSE_CATEGORY
    user_data['item'] = int(query.data)
    bot.edit_message_text(text="Тут будет описание", reply_markup=get_confirm_menu(),
                          chat_id=query.message.chat_id, message_id=query.message.message_id)
    return State.CONFIRM_ITEM


def confirm_item_callback(bot, update, user_data):
    """
    Confirm or reject item
    """
    query = update.callback_query
    if 'back' in query.data.lower():
        del user_data['item']
        bot.edit_message_text(text="Выберите позицию", reply_markup=get_items_menu(user_data['category']),
                              chat_id=query.message.chat_id, message_id=query.message.message_id)
        return State.CHOOSE_ITEM
    else:
        bot.edit_message_text(text="Тут будет описание[2]",
                              chat_id=query.message.chat_id, message_id=query.message.message_id)
        bot.send_message(text="Укажите количество", chat_id=query.message.chat_id)
        return State.CHOOSE_COUNT


def count_handler(bot, update, user_data):
    """
    Put order in DB and notify in channel
    """
    # TODO finish ordering process
    update.message.reply_text("Заказ №*** успешно размещен")
    return ConversationHandler.END


def abort_command(bot, update):
    """
    Abort ordering process
    """
    update.message.reply_text("Заказ прерван")
    return ConversationHandler.END


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
    keyboard = [
        [
            InlineKeyboardButton("Отдельные товары", callback_data="1"),
            InlineKeyboardButton("Обеспечение курсов", callback_data="2")
        ],
        [
            InlineKeyboardButton("Комплекты для обеспечения курсов", callback_data="3")
        ]
    ]
    markup = InlineKeyboardMarkup(keyboard)
    return markup


def get_items_menu(category):
    """
    :param category: Category id
    :return: InlineKeyboardMarkup
    """
    subcatalog = items_catalog.get_category(category)
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


# TODO TESTING VERSION
items_catalog = ItemsCatalog(get_credentials(r"..\google_service.json"),
                             "1s8wkQgta6EqCC9UF8zDrom6YRzN3KYzDLugg4uL-vqA")  # TODO testing
updater = Updater(get_token(r"C:\Users\Egor\PycharmProjects\GekkonBot\telegram.secret"))  # TODO testing

updater.dispatcher.add_handler(CommandHandler('start', start_command))
conversation_handler = ConversationHandler(
    entry_points=[CommandHandler('order', order_command)],
    states={
        State.CHOOSE_CATEGORY: [CallbackQueryHandler(category_callback, pass_user_data=True)],
        State.CHOOSE_ITEM: [CallbackQueryHandler(items_callback, pass_user_data=True)],
        State.CONFIRM_ITEM: [CallbackQueryHandler(confirm_item_callback, pass_user_data=True)],
        State.CHOOSE_COUNT: [RegexHandler(r"^[0-9]+$", count_handler, pass_user_data=True)]
    },
    fallbacks=[CommandHandler('abort', abort_command)]
)
updater.dispatcher.add_handler(conversation_handler)

print("Let's go!")
updater.start_polling()
updater.idle()
