import logging
from telegram import Update, InputMediaPhoto, ParseMode
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler, CallbackQueryHandler, CallbackContext
from telegram.ext import PicklePersistence

# Логирование
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

# Состояния
START, CREATE_POST, ADD_IMAGE, ADD_TEXT, REVIEW_POST = range(5)

# Список администраторов
ADMIN_FILE = 'Admin.txt'

def check_admin(user_id):
    with open(ADMIN_FILE, 'r') as f:
        admins = f.read().splitlines()
    return str(user_id) in admins

# Начало диалога
def start(update: Update, context: CallbackContext) -> int:
    user_id = update.message.from_user.id
    if not check_admin(user_id):
        update.message.reply_text('Вы не авторизованы для использования этого бота.')
        return ConversationHandler.END
    
    update.message.reply_text('Добро пожаловать! Выберите действие:',
                              reply_markup=ReplyKeyboardMarkup([['Создать публикацию', 'Запланировать публикацию']], one_time_keyboard=True))
    return CREATE_POST

# Создание публикации
def create_post(update: Update, context: CallbackContext) -> int:
    update.message.reply_text('Прикрепите или вставьте картинку:')
    return ADD_IMAGE

# Пропустить изображение
def skip_image(update: Update, context: CallbackContext) -> int:
    context.user_data['image'] = None  # Нет изображения
    return add_text(update, context)

# Добавление текста
def add_text(update: Update, context: CallbackContext) -> int:
    update.message.reply_text('Напишите, вставьте или перешлите текст публикации:')
    return ADD_TEXT

# Пропустить текст
def skip_text(update: Update, context: CallbackContext) -> int:
    context.user_data['text'] = None  # Нет текста
    return review_post(update, context)

# Подтверждение публикации
def review_post(update: Update, context: CallbackContext) -> int:
    image = context.user_data.get('image')
    text = context.user_data.get('text', '')
    
    # Подключаем текст из файла репозитория
    with open('footer.txt', 'r') as f:
        footer_text = f.read()

    if image:
        update.message.reply_photo(photo=image, caption=text + footer_text, reply_markup=ReplyKeyboardMarkup([['Отправить', 'Отменить']], one_time_keyboard=True))
    else:
        update.message.reply_text(text + footer_text, reply_markup=ReplyKeyboardMarkup([['Отправить', 'Отменить']], one_time_keyboard=True))
    
    return REVIEW_POST

# Отправка поста
def send_post(update: Update, context: CallbackContext) -> int:
    channel_id = '@precoinmarket_channel'  # Ваш канал
    image = context.user_data.get('image')
    text = context.user_data.get('text', '')
    
    with open('footer.txt', 'r') as f:
        footer_text = f.read()

    if image:
        context.bot.send_photo(chat_id=channel_id, photo=image, caption=text + footer_text)
    else:
        context.bot.send_message(chat_id=channel_id, text=text + footer_text)

    update.message.reply_text('Публикация отправлена!')
    return start(update, context)

# Отмена
def cancel(update: Update, context: CallbackContext) -> int:
    update.message.reply_text('Публикация отменена. Начинаем заново.')
    return start(update, context)

def main():
    persistence = PicklePersistence('bot_data')  # Сохранение состояния

    updater = Updater("7728310907:AAFNSOGBWupK6RCXuf0YRA26ex69hTycS5I", persistence=persistence, use_context=True)
    
    dp = updater.dispatcher

    # Раздел для обработки команд и состояния
    conversation_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            CREATE_POST: [MessageHandler(Filters.text & ~Filters.command, create_post)],
            ADD_IMAGE: [MessageHandler(Filters.photo, skip_image)],
            ADD_TEXT: [MessageHandler(Filters.text & ~Filters.command, add_text)],
            REVIEW_POST: [
                CallbackQueryHandler(send_post, pattern='^Отправить$'),
                CallbackQueryHandler(cancel, pattern='^Отменить$'),
            ],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )
    
    dp.add_handler(conversation_handler)

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
