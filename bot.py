import os
from telegram import Update, InputMediaPhoto, ParseMode
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler, ConversationHandler, CallbackContext

# ID авторизованных пользователей
AUTHORIZED_USERS = set()  # сюда будут добавляться ID авторизованных пользователей, например, {123456789}

# Определяем этапы диалога
CHOOSING, PHOTO, TEXT, CONFIRM = range(4)

def start(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    if user_id not in AUTHORIZED_USERS:
        update.message.reply_text("Вы не авторизованы.")
        return

    update.message.reply_text(
        "Выберите тип публикации:",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("Создать публикацию", callback_data='create')],
            [InlineKeyboardButton("Запланировать публикацию", callback_data='schedule')],
        ])
    )
    return CHOOSING

def choose_option(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()

    choice = query.data
    if choice == 'create':
        query.edit_message_text("Прикрепите или вставьте картинку:")
        return PHOTO
    elif choice == 'schedule':
        query.edit_message_text("Запланированная публикация еще не реализована.")
        return ConversationHandler.END

def photo(update: Update, context: CallbackContext):
    update.message.reply_text(
        "Теперь напишите или вставьте текст публикации (или пропустите):"
    )
    return TEXT

def text(update: Update, context: CallbackContext):
    user_text = update.message.text
    context.user_data['text'] = user_text

    update.message.reply_text("Подтвердите публикацию: \n\n" + user_text,
                              reply_markup=InlineKeyboardMarkup([
                                  [InlineKeyboardButton("Отправить", callback_data='send')],
                                  [InlineKeyboardButton("Отменить", callback_data='cancel')]
                              ]))
    return CONFIRM

def send_post(update: Update, context: CallbackContext):
    user_data = context.user_data
    text = user_data.get('text', '')
    
    # Текст из файла
    with open('additional_text.txt', 'r') as file:
        additional_text = file.read()

    # Здесь отправляется сообщение в канал
    channel_id = "@@precoinmarket_channel"
    context.bot.send_message(
        channel_id,
        text + "\n\n" + additional_text,
        parse_mode=ParseMode.MARKDOWN
    )
    update.callback_query.edit_message_text("Публикация успешна!")
    return ConversationHandler.END

def cancel(update: Update, context: CallbackContext):
    update.callback_query.edit_message_text("Публикация отменена.")
    return ConversationHandler.END

def main():
    updater = Updater("7728310907:AAFNSOGBWupK6RCXuf0YRA26ex69hTycS5I", use_context=True)

    dispatcher = updater.dispatcher
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            CHOOSING: [CallbackQueryHandler(choose_option)],
            PHOTO: [MessageHandler(Filters.photo | Filters.text, photo)],
            TEXT: [MessageHandler(Filters.text & ~Filters.command, text)],
            CONFIRM: [CallbackQueryHandler(send_post, pattern='send'),
                      CallbackQueryHandler(cancel, pattern='cancel')],
        },
        fallbacks=[],
    )

    dispatcher.add_handler(conv_handler)
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
