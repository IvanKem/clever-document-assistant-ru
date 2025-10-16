import asyncio
import aiohttp
import base64
from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.types import Message, BufferedInputFile, ErrorEvent
from aiogram.enums import ContentType, ParseMode
from aiogram.filters import Command
from decouple import config
import logging
import traceback

# Настройки
BOT_TOKEN = config('BOT_TOKEN')
MODEL_API_URL = config('MODEL_API_URL')

# Инициализация
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

# Хранилище пользовательских данных в памяти
user_data = {}

# Логирование
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Обработчик команды /start
@dp.message(Command("start"))
async def start_handler(message: Message):
    try:
        logger.info(f"🚀 /start от пользователя {message.from_user.id}")
        welcome_text = """
🤖 <b>Добро пожаловать в бот для обработки документов!</b>

Я могу:
• 📷 Обрабатывать изображения через OCR
• 📄 Извлекать текст из PDF файлов
• 🧠 Анализировать контент с помощью AI

<b>Как работать:</b>
1. Отправьте мне изображение или PDF файл
2. Я извлеку из него текст
3. Задайте вопрос о содержимом документа
4. Получите интеллектуальный ответ!

Просто отправьте файл чтобы начать!
        """
        await message.answer(welcome_text)
        logger.info(f"✅ /start успешно обработан для {message.from_user.id}")
    except Exception as e:
        logger.error(f"❌ Ошибка в /start: {e}\n{traceback.format_exc()}")
        await message.answer("Произошла ошибка при обработке команды /start")


@dp.message(Command("help"))
async def cmd_help(message: Message):
    try:
        logger.info(f"🆘 /help от пользователя {message.from_user.id}")
        help_text = """
<b>Инструкция по использованию:</b>

1. <b>Отправьте файл</b> - изображение (jpg, png) или PDF
2. <b>Дождитесь обработки</b> - я извелку текст через OCR
3. <b>Задайте вопрос</b> - напишите что вас интересует в документе
4. <b>Получите ответ</b> - AI проанализирует содержимое

<b>Поддерживаемые форматы:</b>
• Изображения: JPG, PNG, JPEG, BMP, TIFF
• Видео: MP4, AVI, MOV, WEBM
• Документы: PDF
        """
        await message.answer(help_text)
        logger.info(f"✅ /help успешно обработан для {message.from_user.id}")
    except Exception as e:
        logger.error(f"❌ Ошибка в /help: {e}\n{traceback.format_exc()}")
        await message.answer("Произошла ошибка при обработке команды /help")


# Обработчик команды /restart
@dp.message(Command("restart"))
async def clear_handler(message: Message):
    user_id = message.from_user.id
    logger.info(f"🔄 /restart от пользователя {user_id}")

    try:
        if user_id in user_data:
            old_files_count = len(user_data[user_id]["files"])
            old_texts_count = len(user_data[user_id]["texts"])
            user_data[user_id] = {"texts": [], "files": []}
            logger.info(f"✅ Данные очищены для {user_id}: было {old_files_count} файлов, {old_texts_count} текстов")
            await message.answer("✅ Данные успешно очищены")
        else:
            user_data[user_id] = {"texts": [], "files": []}
            logger.info(f"✅ Инициализированы новые данные для {user_id}")
            await message.answer("✅ Данные инициализированы")

    except Exception as e:
        logger.error(f"❌ Ошибка в /restart: {e}\n{traceback.format_exc()}")
        await message.answer("❌ Произошла ошибка при очистке данных")


# Обработчик команды /ask
@dp.message(Command("ask"))
async def ask_handler(message: Message):
    user_id = message.from_user.id
    logger.info(f"❓ /ask от пользователя {user_id}")

    try:
        # Детальная проверка состояния данных
        if user_id not in user_data:
            logger.warning(f"⚠️ Пользователь {user_id} не имеет данных")
            await message.answer("❌ Нет данных для запроса. Сначала отправьте текст или файлы.")
            return

        files_count = len(user_data[user_id]["files"])
        texts_count = len(user_data[user_id]["texts"])

        logger.debug(f"📊 Данные пользователя {user_id}: {files_count} файлов, {texts_count} текстов")

        if files_count == 0 and texts_count == 0:
            logger.warning(f"⚠️ Пользователь {user_id} имеет пустые данные")
            await message.answer("❌ Нет данных для запроса. Сначала отправьте текст или файлы.")
            return

        logger.info(f"🚀 Начинаем обработку запроса для {user_id}")
        await process_query(message, user_id)

    except Exception as e:
        logger.error(f"❌ Ошибка в /ask: {e}\n{traceback.format_exc()}")
        await message.answer("❌ Произошла ошибка при обработке запроса")


# Скачивание файла из Telegram
async def download_file(file_id: str) -> tuple[bytes, str, str] | tuple[None, None, None]:
    try:
        logger.debug(f"📥 Скачивание файла {file_id}")
        file = await bot.get_file(file_id)
        file_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file.file_path}"

        async with aiohttp.ClientSession() as session:
            async with session.get(file_url) as response:
                if response.status != 200:
                    logger.error(f"❌ Ошибка скачивания файла: статус {response.status}")
                    return None, None, None

                file_data = await response.read()
                logger.debug(f"✅ Файл скачан, размер: {len(file_data)} байт")

                # Определяем тип файла
                file_extension = file.file_path.split('.')[-1].lower() if '.' in file.file_path else ''
                file_name = os.path.basename(file.file_path) if file.file_path else f"file_{file_id}.{file_extension}"

                if file_extension in ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'tiff', 'tif']:
                    file_type = "image"
                elif file_extension == 'pdf':
                    file_type = "pdf"
                else:
                    file_type = "document"

                logger.debug(f"📄 Тип файла определен как: {file_type}")
                return file_data, file_type, file_name

    except Exception as ex:
        logger.error(f"Error downloading file: {ex}\n{traceback.format_exc()}")
        return None, None, None


# Обработчик только для файлов (без текста)
@dp.message(
    F.content_type.in_({
        ContentType.PHOTO,
        ContentType.DOCUMENT
    })
)
async def handle_files(message: Message):
    user_id = message.from_user.id
    logger.debug(f"📎 Получен файл от {user_id}: тип={message.content_type}")

    try:
        # Инициализация данных пользователя
        if user_id not in user_data:
            user_data[user_id] = {"texts": [], "files": []}

        file_data, file_type, file_name = None, None, None

        if message.photo:
            file_id = message.photo[-1].file_id
            file_data, file_type, file_name = await download_file(file_id)
        elif message.document:
            file_id = message.document.file_id
            file_data, file_type, file_name = await download_file(file_id)

        if file_data and file_type:
            # Проверяем поддерживаемые форматы файлов
            if file_type not in ["image", "pdf"]:
                await message.answer(f"❌ Формат файла {file_name} не поддерживается. Отправьте изображение или PDF.")
                logger.warning(f"⚠️ Неподдерживаемый формат файла от {user_id}: {file_type}")
                return

            # Сохраняем информацию о файле
            user_data[user_id]["files"].append({
                "name": file_name,
                "type": file_type,
                "data": base64.b64encode(file_data).decode('utf-8')
            })
            await message.answer(f"✅ Файл ({file_type}) сохранен. Добавьте текст или отправьте /ask для запроса")
            logger.debug(f"💾 Файл сохранен для {user_id}, всего файлов: {len(user_data[user_id]['files'])}")
        else:
            await message.answer("❌ Не удалось обработать файл")
            logger.error(f"❌ Ошибка обработки файла от {user_id}")

    except Exception as ex:
        logger.error(f"❌ Ошибка в handle_files: {ex}\n{traceback.format_exc()}")
        await message.answer("❌ Произошла ошибка при обработке файла")


# Обработчик неподдерживаемых типов сообщений
@dp.message()
async def handle_unsupported_types(message: Message):
    user_id = message.from_user.id
    content_type = message.content_type

    logger.warning(f"⚠️ Получено неподдерживаемое сообщение от {user_id}: тип={content_type}")

    # Определяем тип контента для понятного сообщения пользователю
    content_type_names = {
        ContentType.VIDEO: "видео",
        ContentType.VOICE: "голосовые сообщения",
        ContentType.VIDEO_NOTE: "кружочки",
        ContentType.STICKER: "стикеры",
        ContentType.AUDIO: "аудиофайлы",
        ContentType.ANIMATION: "GIF-анимации",
        ContentType.CONTACT: "контакты",
        ContentType.LOCATION: "геолокации",
        ContentType.POLL: "опросы",
        ContentType.DICE: "кости",
    }

    content_name = content_type_names.get(content_type, "этот тип сообщений")

    unsupported_text = f"""❌ Извините, но {content_name} не поддерживаются."""

    await message.answer(unsupported_text)
    logger.debug(f"⚠️ Уведомление о неподдерживаемом формате отправлено {user_id}")



# Обработка запроса к модели
async def process_query(message: Message, user_id: int):
    try:
        logger.debug(f"🔧 process_query начат для {user_id}")
        await message.answer("⏳ Обрабатываю запрос...")

        # Формируем данные для API
        api_data = {
            "texts": user_data[user_id]["texts"],
            "files": user_data[user_id]["files"]
        }

        logger.debug(f"📦 Данные для API: {len(api_data['texts'])} текстов, {len(api_data['files'])} файлов")

        async with aiohttp.ClientSession() as session:
            logger.debug("🌐 Отправка запроса к модели")
            response = await query_model(session, api_data)
            logger.debug(f"✅ Получен ответ от модели: {response}")
            await send_response(message, response)

        # Очищаем данные после ответа
        user_data[user_id] = {"texts": [], "files": []}
        logger.info(f"🎉 Запрос успешно обработан для {user_id}, данные очищены")

    except Exception as e:
        logger.error(f"❌ Ошибка в process_query: {e}\n{traceback.format_exc()}")
        await message.answer("❌ Произошла ошибка при обработке запроса к модели")


# Запрос к модели на DataSphere
async def query_model(session: aiohttp.ClientSession, data: dict) -> dict:
    try:
        logger.debug(
            f"🌐 Запрос к {MODEL_API_URL} с данными: {len(data.get('texts', []))} текстов, {len(data.get('files', []))} файлов")

        async with session.post(MODEL_API_URL, json=data) as response:
            response_text = await response.text()
            logger.debug(f"📨 Ответ API: статус {response.status}, тело: {response_text[:500]}...")

            if response.status != 200:
                logger.error(f"❌ Ошибка API: статус {response.status}")
                return {"text": f"❌ Ошибка сервера: статус {response.status}"}

            return await response.json()
    except Exception as e:
        logger.error(f"❌ API error: {e}\n{traceback.format_exc()}")
        return {"text": "❌ Ошибка запроса к модели"}


# Отправка ответа пользователю
async def send_response(message: Message, response_data: dict):
    try:
        logger.debug(f"📤 Отправка ответа: {response_data}")
        text_response = response_data.get("text", "")
        image_data = response_data.get("image")

        if image_data:
            # Декодируем base64 изображение
            if isinstance(image_data, str) and image_data.startswith('data:image'):
                image_data = image_data.split(',')[1]

            try:
                image_bytes = base64.b64decode(image_data)
                image_file = BufferedInputFile(image_bytes, filename="response.png")
                await message.answer_photo(photo=image_file, caption=text_response)
                logger.debug("✅ Ответ отправлен как фото")
            except Exception as e:
                logger.error(f"❌ Error decoding image: {e}\n{traceback.format_exc()}")
                await message.answer(text_response + "\n\n⚠️ Не удалось отобразить изображение")
        else:
            await message.answer(text_response)
            logger.debug("✅ Ответ отправлен как текст")

    except Exception as e:
        logger.error(f"❌ Ошибка в send_response: {e}\n{traceback.format_exc()}")
        await message.answer("❌ Произошла ошибка при отправке ответа")


# Глобальный обработчик ошибок для aiogram 3.x
@dp.error()
async def error_handler(event: ErrorEvent):
    logger.error(f"💥 Глобальная ошибка: {event.exception}\n{traceback.format_exc()}")
    return True


# Функция для проверки работы бота
async def test_bot():
    logger.info("🧪 Запуск тестовой функции")
    try:
        me = await bot.get_me()
        logger.info(f"🤖 Бот @{me.username} успешно инициализирован")
        return True
    except Exception as e:
        logger.error(f"❌ Ошибка инициализации бота: {e}")
        return False


# Главная функция запуска бота
async def main():
    logger.info("🚀 Бот запускается...")

    # Проверяем работу бота
    if not await test_bot():
        logger.error("❌ Не удалось инициализировать бота")
        return

    logger.info("✅ Бот успешно инициализирован, начинаем пуллинг...")

    try:
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"💥 Критическая ошибка при пуллинге: {e}\n{traceback.format_exc()}")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("⏹️ Бот остановлен пользователем")
    except Exception as e:
        logger.error(f"💥 Критическая ошибка: {e}\n{traceback.format_exc()}")
