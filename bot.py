from telegram import Update, InputMediaPhoto
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ConversationHandler, CallbackContext
from telegram.ext import filters  # В новой версии Filters теперь импортируются так

# ID авторизованных пользователей
AUTHORIZED_USERS = set()  # сюда будут добавляться ID авторизованных пользователей, например, {123456789}

# Определяем этапы диалога
CHOOSING, PHOTO, TEXT, CONFIRM = range(4)

async def start(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    if user_id not in AUTHORIZED_USERS:
        await update.message.reply_text("Вы не авторизованы.")
        return

    await update.message.reply_text(
        "Выберите тип публикации:",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("Создать публикацию", callback_data='create')],
            [InlineKeyboardButton("Запланировать публикацию", callback_data='schedule')],
        ])
    )
    return CHOOSING

async def choose_option(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()

    choice = query.data
    if choice == 'create':
        await query.edit_message_text("Прикрепите или вставьте картинку:")
        return PHOTO
    elif choice == 'schedule':
        await query.edit_message_text("Запланированная публикация еще не реализована.")
        return ConversationHandler.END

async def photo(update: Update, context: CallbackContext):
    await update.message.reply_text(
        "Теперь напишите или вставьте текст публикации (или пропустите):"
    )
    return TEXT

async def text(update: Update, context: CallbackContext):
    user_text = update.message.text
    context.user_data['text'] = user_text

    await update.message.reply_text("Подтвердите публикацию: \n\n" + user_text,
                              reply_markup=InlineKeyboardMarkup([
                                  [InlineKeyboardButton("Отправить", callback_data='send')],
                                  [InlineKeyboardButton("Отменить", callback_data='cancel')]
                              ]))
    return CONFIRM

async def send_post(update: Update, context: CallbackContext):
    user_data = context.user_data
    text = user_data.get('text', '')
    
    # Текст из файла
    with open('additional_text.txt', 'r') as file:
        additional_text = file.read()

    # Здесь отправляется сообщение в канал
    channel_id = "@PreCoinMarket"
    await context.bot.send_message(
        channel_id,
        text + "\n\n" + additional_text,
        parse_mode="Markdown"
    )
    await update.callback_query.edit_message_text("Публикация успешна!")
    return ConversationHandler.END

async def cancel(update: Update, context: CallbackContext):
    await update.callback_query.edit_message_text("Публикация отменена.")
    return ConversationHandler.END

def main():
    application = Application.builder().token("7728310907:AAFNSOGBWupK6RCXuf0YRA26ex69hTycS5I").build()

    # Обработчики
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            CHOOSING: [CallbackQueryHandler(choose_option)],
            PHOTO: [MessageHandler(filters.PHOTO | filters.TEXT, photo)],  # Применяем новый способ импорта фильтров
            TEXT: [MessageHandler(filters.TEXT & ~filters.COMMAND, text)],
            CONFIRM: [CallbackQueryHandler(send_post, pattern='send'),
                      CallbackQueryHandler(cancel, pattern='cancel')],
        },
        fallbacks=[],
    )

    application.add_handler(conv_handler)
    application.run_polling()

if __name__ == '__main__':
    main()
