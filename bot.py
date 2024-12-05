from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ConversationHandler, CallbackContext
from telegram.ext import filters

# ID авторизованных пользователей
AUTHORIZED_USERS = {282198872}  # Ваш ID

# Определяем этапы диалога
CHOOSING, PHOTO, TEXT, CONFIRM = range(4)

# Функция старта
async def start(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    if user_id not in AUTHORIZED_USERS:
        await update.message.reply_text("Вы не авторизованы.")
        return

    await update.message.reply_text(
        "Выберите тип публикации:",
        reply_markup=InlineKeyboardMarkup([  # Встроенная разметка клавиатуры
            [InlineKeyboardButton("Создать публикацию", callback_data='create')],
            [InlineKeyboardButton("Запланировать публикацию", callback_data='schedule')]
        ])
    )
    return CHOOSING

# Выбор опции
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

# Обработка фото
async def photo(update: Update, context: CallbackContext):
    if update.message.photo:
        await update.message.reply_text(
            "Теперь напишите или вставьте текст публикации (или пропустите):"
        )
        return TEXT
    else:
        await update.message.reply_text("Пожалуйста, отправьте картинку.")
        return PHOTO

# Обработка текста
async def text(update: Update, context: CallbackContext):
    user_text = update.message.text
    context.user_data['text'] = user_text  # Сохраняем текст публикации

    await update.message.reply_text(
        f"Подтвердите публикацию: \n\n{user_text}",
        reply_markup=InlineKeyboardMarkup([  # Встроенная разметка клавиатуры
            [InlineKeyboardButton("Отправить", callback_data='send')],
            [InlineKeyboardButton("Отменить", callback_data='cancel')]
        ])
    )
    return CONFIRM

# Отправка поста
async def send_post(update: Update, context: CallbackContext):
    user_data = context.user_data
    text = user_data.get('text', '')

    # Чтение дополнительного текста из файла
    try:
        with open('additional_text.txt', 'r') as file:
            additional_text = file.read()
    except FileNotFoundError:
        await update.callback_query.edit_message_text("Ошибка: файл дополнительного текста не найден.")
        return ConversationHandler.END

    # Отправляем сообщение в канал
    channel_id = "@precoinmarket_channel"  # Ваш канал
    await context.bot.send_message(
        channel_id,
        text + "\n\n" + additional_text,
        parse_mode="Markdown"
    )
    await update.callback_query.edit_message_text("Публикация успешна!")
    return ConversationHandler.END

# Отмена публикации
async def cancel(update: Update, context: CallbackContext):
    await update.callback_query.edit_message_text("Публикация отменена.")
    return ConversationHandler.END

# Функция для обработки кнопок "Отправить" и "Отменить"
async def confirm_button(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()

    if query.data == 'send':
        await send_post(update, context)
    elif query.data == 'cancel':
        await cancel(update, context)
    else:
        await query.edit_message_text("Неизвестная команда.")

# Главная функция
def main():
    # Подключаем бота
    application = Application.builder().token("7728310907:AAFNSOGBWupK6RCXuf0YRA26ex69hTycS5I").build()

    # Обработчики
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            CHOOSING: [CallbackQueryHandler(choose_option)],
            PHOTO: [MessageHandler(filters.PHOTO, photo), MessageHandler(filters.TEXT, photo)],  # Обрабатываем фото и текст
            TEXT: [MessageHandler(filters.TEXT & ~filters.COMMAND, text)],
            CONFIRM: [CallbackQueryHandler(confirm_button, pattern='send'),
                      CallbackQueryHandler(confirm_button, pattern='cancel')],
        },
        fallbacks=[],
    )

    application.add_handler(conv_handler)
    application.run_polling()

if __name__ == '__main__':
    main()
