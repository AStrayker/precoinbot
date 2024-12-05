import logging
from telegram import Update, InputMediaPhoto
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler, CallbackContext, CallbackQueryHandler
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

# Включаем логирование для отладки
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Состояния диалога
CHOOSE_ACTION, ADD_IMAGE, ADD_TEXT, CONFIRM = range(4)

# Хранилище данных
user_data = {}

# Текст из отдельного файла (например, "additional_text.txt")
with open('additional_text.txt', 'r') as file:
    additional_text = file.read()

# Стартовая команда
def start(update: Update, context: CallbackContext):
    update.message.reply_text("Привет! Выберите тип публикации:", reply_markup=main_menu())

# Главное меню
def main_menu():
    keyboard = [
        [InlineKeyboardButton("Создать публикацию", callback_data='create_post')]
    ]
    return InlineKeyboardMarkup(keyboard)

# Обработчик команды "Создать публикацию"
def choose_action(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()

    user_data[query.from_user.id] = {}  # Инициализируем пустой словарь для данных пользователя

    # Переход к следующему шагу
    query.edit_message_text("Прикрепите или вставьте картинку:", reply_markup=skip_or_upload_image())

# Кнопки для загрузки картинки или пропуска
def skip_or_upload_image():
    keyboard = [
        [InlineKeyboardButton("Пропустить", callback_data='skip_image')]
    ]
    return InlineKeyboardMarkup(keyboard)

# Обработка прикрепления картинки или пропуска
def handle_image(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()

    if query.data == 'skip_image':
        user_data[query.from_user.id]['image'] = None
    else:
        user_data[query.from_user.id]['image'] = update.message.photo[-1].file_id

    query.edit_message_text("Напишите, вставьте или перешлите текст публикации:", reply_markup=skip_or_insert_text())

# Кнопки для вставки текста или пропуска
def skip_or_insert_text():
    keyboard = [
        [InlineKeyboardButton("Пропустить", callback_data='skip_text')]
    ]
    return InlineKeyboardMarkup(keyboard)

# Обработка текста или пропуска
def handle_text(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()

    if query.data == 'skip_text':
        user_data[query.from_user.id]['text'] = None
    else:
        user_data[query.from_user.id]['text'] = update.message.text

    # Отправляем на подтверждение
    send_confirmation(update, context)

# Отправка на подтверждение
def send_confirmation(update: Update, context: CallbackContext):
    user_id = update.callback_query.from_user.id
    post_data = user_data[user_id]

    text = post_data.get('text', 'Нет текста')
    image = post_data.get('image', None)

    # Формируем сообщение для подтверждения
    message = f"Публикация:\nТекст: {text}"

    if image:
        message += "\n(с изображением)"

    keyboard = [
        [InlineKeyboardButton("Отправить", callback_data='send_post')],
        [InlineKeyboardButton("Отменить", callback_data='cancel_post')]
    ]

    update.callback_query.edit_message_text(message, reply_markup=InlineKeyboardMarkup(keyboard))

# Отправка публикации в канал
def send_post(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()

    user_id = query.from_user.id
    post_data = user_data[user_id]

    text = post_data.get('text', 'Нет текста')
    image = post_data.get('image', None)

    # Отправка публикации в канал
    if image:
        context.bot.send_photo(chat_id='@precoinmarket_channel', photo=image, caption=text + '\n\n' + additional_text)
    else:
        context.bot.send_message(chat_id='@precoinmarket_channel', text=text + '\n\n' + additional_text)

    query.edit_message_text("Публикация успешно отправлена!")

    # Возвращаем в начало
    query.message.reply_text("Привет! Выберите тип публикации:", reply_markup=main_menu())

# Отмена публикации
def cancel_post(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()

    query.edit_message_text("Публикация отменена!")
    query.message.reply_text("Привет! Выберите тип публикации:", reply_markup=main_menu())

# Функция ошибки
def error(update: Update, context: CallbackContext):
    logger.warning(f"Update {update} caused error {context.error}")

# Основная функция
def main():
    # Замените 'YOUR_TOKEN' на токен вашего бота
    updater = Updater("7728310907:AAFNSOGBWupK6RCXuf0YRA26ex69hTycS5I", use_context=True)

    dp = updater.dispatcher

    # Регистрируем обработчики
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            CHOOSE_ACTION: [CallbackQueryHandler(choose_action, pattern='^create_post$')],
            ADD_IMAGE: [MessageHandler(Filters.photo, handle_image), CallbackQueryHandler(handle_image, pattern='^skip_image$')],
            ADD_TEXT: [MessageHandler(Filters.text & ~Filters.command, handle_text), CallbackQueryHandler(handle_text, pattern='^skip_text$')],
            CONFIRM: [CallbackQueryHandler(send_post, pattern='^send_post$'), CallbackQueryHandler(cancel_post, pattern='^cancel_post$')]
        },
        fallbacks=[CommandHandler('start', start)],
    )

    dp.add_handler(conv_handler)
    dp.add_error_handler(error)

    # Запускаем бота
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
