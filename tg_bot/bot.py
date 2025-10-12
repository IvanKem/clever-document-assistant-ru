import asyncio
import aiohttp
import base64
from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.types import Message, BufferedInputFile
from aiogram.enums import ContentType, ParseMode
from aiogram.filters import Command
import logging

# Настройки
BOT_TOKEN = "YOUR_BOT_TOKEN"
MODEL_API_URL = 'YOUR_DATASPHERE_API_ENDPOINT'

# Инициализация
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

# Хранилище пользовательских данных в памяти
user_data = {}

# Логирование
logging.basicConfig(level=logging.INFO)


# Обработчик команды /start
@dp.message(Command("start"))
async def start_handler(message: Message):
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


@dp.message(Command("help"))
async def cmd_help(message: Message):
    help_text = """
        <b>Инструкция по использованию:</b>
        
        1. <b>Отправьте файл</b> - изображение (jpg, png) или PDF
        2. <b>Дождитесь обработки</b> - я извлеку текст через OCR
        3. <b>Задайте вопрос</b> - напишите что вас интересует в документе
        4. <b>Получите ответ</b> - AI проанализирует содержимое
        
        <b>Поддерживаемые форматы:</b>
        • Изображения: JPG, PNG, JPEG, BMP, TIFF
        • Видео: MP4, AVI, MOV, WEBM
        • Документы: PDF
        
    """
    await message.answer(help_text)


# Обработчик всех сообщений
@dp.message(F.content_type.in_({ContentType.TEXT, ContentType.PHOTO, ContentType.VIDEO, ContentType.DOCUMENT}))
async def handle_message(message: Message):
    user_id = message.from_user.id

    # Инициализация данных пользователя
    if user_id not in user_data:
        user_data[user_id] = {"texts": [], "files": []}

    # Обработка текста
    if message.text and not message.text.startswith('/'):
        user_data[user_id]["texts"].append(message.text)
        await message.answer("Текст сохранен. Добавьте файлы или отправьте /ask для запроса")

    # Обработка файлов
    elif not message.text:  # Только если это не текстовое сообщение с командой
        file_data, file_type = None, None

        if message.photo:
            file_id = message.photo[-1].file_id
            file_data, file_type = await download_file(file_id)
        elif message.video:
            file_id = message.video.file_id
            file_data, file_type = await download_file(file_id)
        elif message.document:
            file_id = message.document.file_id
            file_data, file_type = await download_file(file_id)

        if file_data and file_type:
            # Конвертируем в base64 для API
            file_base64 = base64.b64encode(file_data).decode('utf-8')
            user_data[user_id]["files"].append({
                "data": file_base64,
                "type": file_type
            })
            await message.answer(f"Файл ({file_type}) сохранен. Добавьте текст или отправьте /ask для запроса")
            print(len(user_data[user_id]["files"]))
            print(len(user_data[user_id]["texts"]))


# Очистка данных пользователя
@dp.message(Command("restart"))
async def clear_handler(message: Message):
    user_id = message.from_user.id
    user_data[user_id] = {"texts": [], "files": []}
    await message.answer("Данные очищены")


# Скачивание файла из Telegram
async def download_file(file_id: str) -> tuple[bytes, str] | tuple[None, None]:
    try:
        file = await bot.get_file(file_id)
        file_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file.file_path}"

        async with aiohttp.ClientSession() as session:
            async with session.get(file_url) as response:
                file_data = await response.read()

                # Определяем тип файла
                file_extension = file.file_path.split('.')[-1].lower()
                if file_extension in ['jpg', 'jpeg', 'png', 'gif']:
                    file_type = "image"
                elif file_extension in ['mp4', 'avi', 'mov', 'webm']:
                    file_type = "video"
                elif file_extension == 'pdf':
                    file_type = "pdf"
                else:
                    file_type = "unknown"

                return file_data, file_type

    except Exception as e:
        logging.error(f"Error downloading file: {e}")
        return None, None


# Обработка запроса к модели
@dp.message(Command("ask"))
async def ask_handler(message: Message):
    user_id = message.from_user.id

    if user_id not in user_data or (not user_data[user_id]["texts"] and not user_data[user_id]["files"]):
        await message.answer("Нет данных для запроса. Сначала отправьте текст или файлы.")
        return

    await process_query(message, user_id)


# Обработка запроса к модели
async def process_query(message: Message, user_id: int):
    await message.answer("Обрабатываю запрос...")

    # Формируем данные для API
    api_data = {
        "texts": user_data[user_id]["texts"],
        "files": user_data[user_id]["files"]
    }

    async with aiohttp.ClientSession() as session:
        response = await query_model(session, api_data)
        await send_response(message, response)

    # Очищаем данные после ответа
    user_data[user_id] = {"texts": [], "files": []}


# Запрос к модели на DataSphere
async def query_model(session: aiohttp.ClientSession, data: dict) -> dict:
    try:
        async with session.post(MODEL_API_URL, json=data) as response:
            return await response.json()
    except Exception as e:
        logging.error(f"API error: {e}")
        return {"text": "Ошибка запроса к модели"}


# Отправка ответа пользователю
async def send_response(message: Message, response_data: dict):
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
        except Exception as e:
            logging.error(f"Error decoding image: {e}")
            await message.answer(text_response)
    else:
        await message.answer(text_response)


# Главная функция запуска бота
async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
