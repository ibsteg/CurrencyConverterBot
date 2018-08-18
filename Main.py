import json
import requests
from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, ConversationHandler, MessageHandler, Filters


TOKEN = 'BOT_TOKEN'
PB_API = 'https://api.privatbank.ua/p24api/pubinfo?exchange&json&coursid=11'

updater = Updater(token=TOKEN)
dispatcher = updater.dispatcher

result = requests.get(PB_API)
json_data = json.loads(result.text)

CURRENCY, ACTION, ADDITIONAL, RESULT = range(4)


def findItem(criterion: str)->dict:
    """
    Get field from json according to criterion currency information
    :param criterion: string with criterion for finding info about currency in database
    :return each: json(dict) with necessary info about currency
    """

    for each in json_data:
        if each['ccy'] == criterion:
            return each


def start(bot, update):
    """
    Function of /start command
    :param bot: current bot object
    :param update: incoming update
    :return CURRENCY: pointer to next function to form dialog with user
    """

    keyboard = [
        [InlineKeyboardButton(u"Begin \U000023E9", callback_data='start')],
    ]
    markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text(u"Hi! \U0001F44B I can give you information about current exchange rates of UAH."
                              " Also, I can help you with convert operations.", reply_markup=markup)

    return CURRENCY


def currencyChose(bot, update):
    """
    Forming of message with buttons to choose currency
    :param bot: current bot object
    :param update: incoming update
    :return ACTION: pointer to next function to form dialog with user
    """

    global item
    item = []

    query = update.callback_query
    keyboard = [
        [InlineKeyboardButton("EUR", callback_data='EUR'),
         InlineKeyboardButton("USD", callback_data='USD'),
         InlineKeyboardButton("RUR", callback_data="RUR")],
    ]
    markup = InlineKeyboardMarkup(keyboard)

    bot.edit_message_text(
        chat_id=query.message.chat_id,
        message_id=query.message.message_id,
        text="Choose currency:")

    bot.edit_message_reply_markup(
        chat_id=query.message.chat_id,
        message_id=query.message.message_id,
        reply_markup=markup
    )

    return ACTION


def actionChose(bot, update):
    """
    Forming of message with buttons to choose action
    :param bot: current bot object
    :param update: incoming update
    :return ADDITIONAL: pointer to next function to form dialog with user
    """

    query = update.callback_query
    item.append(query.data)

    keyboard = [
        [InlineKeyboardButton("Buy", callback_data='Buy'),
         InlineKeyboardButton("Sale", callback_data='Sale')],
        [InlineKeyboardButton("Check current course", callback_data='Course')]
    ]

    markup = InlineKeyboardMarkup(keyboard)

    bot.edit_message_text(
        chat_id=query.message.chat_id,
        message_id=query.message.message_id,
        text="What do you want to do?"
    )

    bot.edit_message_reply_markup(
        chat_id=query.message.chat_id,
        message_id=query.message.message_id,
        reply_markup=markup
    )
    return ADDITIONAL


def additionalInfo(bot, update):
    """
    Forming of message with course info or with buttons to enter amount
    :param bot: current bot object
    :param update: incoming update
    :return CURRENCY, RESULT: pointer to next function to form dialog with user
    """

    query = update.callback_query
    item.append(query.data)

    text = ''

    global currency
    currency = findItem(item[0])

    if item[1] == 'Course':
        text += u'\U0001F4B5	' + currency['base_ccy'] + u' \U000027A1 ' + currency['ccy'] + '\n'
        text += 'Buy: ' + currency['buy'] + '\n' + 'Sale: ' + currency['sale']

        keyboard = [[InlineKeyboardButton("Back to beginning", callback_data='Back')]]
        markup = InlineKeyboardMarkup(keyboard)

        bot.edit_message_text(
            chat_id=query.message.chat_id,
            message_id=query.message.message_id,
            text=text)

        bot.edit_message_reply_markup(
            chat_id=query.message.chat_id,
            message_id=query.message.message_id,
            reply_markup=markup
        )

        return CURRENCY

    elif item[1] in ['Buy', 'Sale']:
        text += "Enter the amount to calculate the exchange:"

        bot.edit_message_text(
            chat_id=query.message.chat_id,
            message_id=query.message.message_id,
            text=text)

    return RESULT


def textMessage(bot, update):
    """
    Forming of message with calculated exchange
    :param bot: current bot object
    :param update: incoming update
    :return CURRENCY: pointer to next function to form dialog with user
    """

    global num
    query = update.message.text

    try:
        num = float(query)
    except:
        bot.send_message(chat_id=update.message.chat_id,
                         text=u'Wrong format: Please, enter number. \n'
                         u'\U000026A0 Fractional number must have . as separator!')

    keyboard = [[InlineKeyboardButton("Back to beginning", callback_data='Back')]]
    markup = InlineKeyboardMarkup(keyboard)

    if len(item) > 0:
        text = ''
        if item[1] == 'Buy':
            text += "To buy %.2f %s you need " % (num, item[0])
            text += str(float(currency['sale']) * num) + ' ' + currency['base_ccy']

            bot.send_message(
                chat_id=update.message.chat_id,
                text=text)

        elif item[1] == 'Sale':

            text += "You can sell %.2f %s for " % (num, item[0])
            text += str(float(currency['buy']) * num) + ' ' + currency['base_ccy']

            bot.send_message(
                chat_id=update.message.chat_id,
                text=text)

        bot.send_message(
            chat_id=update.message.chat_id,
            text='Do you wanna go back?',
            reply_markup=markup
        )

    return CURRENCY


conversation_handler = ConversationHandler(
    entry_points=[CommandHandler('start', start)],
    states={
        CURRENCY: [CallbackQueryHandler(currencyChose)],
        ACTION: [CallbackQueryHandler(actionChose)],
        ADDITIONAL: [CallbackQueryHandler(additionalInfo)],
        RESULT: [MessageHandler(Filters.text, textMessage)]
    },
    fallbacks=[CommandHandler('start', start)]
)

updater.dispatcher.add_handler(conversation_handler)
updater.start_polling()
updater.idle()
