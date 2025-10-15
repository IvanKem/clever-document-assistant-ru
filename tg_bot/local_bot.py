import asyncio
import base64
import logging
import os
import traceback
from typing import Dict, Any
import aiohttp
from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ContentType, ParseMode
from aiogram.filters import Command
from aiogram.types import Message, ErrorEvent
from decouple import config

# Настройки
BOT_TOKEN = config("BOT_TOKEN")
MODEL_API_URL = config("LOCAL_MODEL_API_URL")

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
• 📷 Обрабатывать изображения и видео через OCR
• 📄 Извлекать текст из PDF файлов
• 🧠 Анализировать контент с помощью AI

<b>Как работать:</b>
1. Отправьте мне изображение или PDF файл
2. Я извлеку из него текст
3. Задайте вопрос о содержимом документов
4. Получите ответ!

<b>Доступные команды:</b>
1. /start - начало работы с ботом
2. /help - справка по работе с ботом
3. /restart - Сброс всех данных
4. /ask - Отправка запроса к модели
        """
        await message.answer(welcome_text)
        logger.info(f"✅ /start успешно обработан для {message.from_user.id}")
    except Exception as e:
        logger.error(f"❌ Ошибка в /start: {e}\n{traceback.format_exc()}")
        await message.answer("Произошла ошибка при обработке команды /start")


# Справочная команда /help
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
        await process_query_local_api(message, user_id)

    except Exception as e:
        logger.error(f"❌ Ошибка в /ask: {e}\n{traceback.format_exc()}")
        await message.answer("❌ Произошла ошибка при обработке запроса")


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

    except Exception as e:
        logger.error(f"❌ Ошибка в handle_files: {e}\n{traceback.format_exc()}")
        await message.answer("❌ Произошла ошибка при обработке файла")


# Обработчик текста (кроме команд)
@dp.message(F.content_type == ContentType.TEXT)
async def handle_text(message: Message):
    user_id = message.from_user.id

    # Пропускаем команды - они обрабатываются отдельно
    if message.text.startswith('/'):
        logger.debug(f"⚡ Команда {message.text} передана другому обработчику")
        return

    logger.debug(f"📝 Получен текст от {user_id}: {message.text[:50]}...")

    try:
        # Инициализация данных пользователя
        if user_id not in user_data:
            user_data[user_id] = {"texts": [], "files": []}

        user_data[user_id]["texts"].append(message.text)
        await message.answer("✅ Текст сохранен. Добавьте файлы или отправьте /ask для запроса")
        logger.debug(f"💾 Текст сохранен для {user_id}, всего текстов: {len(user_data[user_id]['texts'])}")

    except Exception as e:
        logger.error(f"❌ Ошибка в handle_text: {e}\n{traceback.format_exc()}")
        await message.answer("❌ Произошла ошибка при обработке текста")


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

    except Exception as e:
        logger.error(f"Error downloading file: {e}\n{traceback.format_exc()}")
        return None, None, None


# Обработка запроса к локальной модели
async def process_query_local_api(message: Message, user_id: int):
    try:
        logger.debug(f"process_query начат для {user_id}")
        await message.answer("⏳ Обрабатываю запрос...")

        # Формируем данные для API
        api_data = {
            "texts": user_data[user_id]["texts"],
            "files": user_data[user_id]["files"],
            "temperature": 0.7,
            "max_tokens": 2000
        }

        logger.debug(f"📦 Данные для API: {len(api_data['texts'])} текстов, {len(api_data['files'])} файлов")

        async with aiohttp.ClientSession() as session:
            response = await query_model_local_api(session, api_data)
            await send_response(message, response)

        # Очищаем данные после ответа
        user_data[user_id] = {"texts": [], "files": []}
        logger.info(f"🎉 Запрос успешно обработан для {user_id}, данные очищены")

    except Exception as e:
        logger.error(f"❌ Ошибка в process_query: {e}\n{traceback.format_exc()}")
        await message.answer("❌ Произошла ошибка при обработке запроса к модели")


async def prepare_prompt(data: Dict[str, Any]) -> str:
    texts = data.get("texts", [])
    files = data.get("files", [])

    parts = []

    # Добавляем тексты
    if texts:
        if len(texts) == 1:
            parts.append(texts[0])
        else:
            for i, text in enumerate(texts, 1):
                parts.append(f"Текст {i}:\n{text}")

    # Добавляем информацию о файлах
    if files:
        files_info = ["Приложенные файлы:"]
        for i, file_info in enumerate(files, 1):
            files_info.append(f"{i}. {file_info['name']} ({file_info['type']})")
            # Можно добавить базовую информацию о содержимом файла
            if file_info['type'] == 'image':
                files_info.append(f"   [Изображение, размер: {len(base64.b64decode(file_info['data']))} байт]")
            elif file_info['type'] == 'pdf':
                files_info.append(f"   [PDF документ, размер: {len(base64.b64decode(file_info['data']))} байт]")
        parts.append("\n".join(files_info))

    return "\n\n".join(parts)


async def query_model_local_api(session: aiohttp.ClientSession, data: dict) -> dict:
    """
    Улучшенная функция запроса к локальной модели с обработкой ошибок
    """
    try:
        logger.debug(f"🌐 Запрос к LM Studio API")

        # Формируем промпт из текстов и информации о файлах
        user_content = await prepare_prompt(data)

        # Подготавливаем данные для LM Studio API
        api_data = {
            "model": "local-model",
            "messages": [
                {
                    "role": "user",
                    "content": user_content
                }
            ],
            "temperature": data.get("temperature", 0.7),
            "max_tokens": data.get("max_tokens", 1000),
            "stream": False
        }

        logger.debug(f"📤 Отправка запроса к {MODEL_API_URL}")

        # Увеличиваем таймаут для стабильности
        timeout = aiohttp.ClientTimeout(total=120)

        async with session.post(
                MODEL_API_URL,
                json=api_data,
                timeout=timeout
        ) as response:

            if response.status != 200:
                error_text = await response.text()
                logger.error(f"❌ Ошибка API: статус {response.status}, ответ: {error_text}")
                return {"text": f"❌ Ошибка сервера: статус {response.status}"}

            result = await response.json()
            logger.debug(f"✅ Получен ответ от API")

            # Извлекаем текстовый ответ из структуры LM Studio
            if "choices" in result and len(result["choices"]) > 0:
                assistant_message = result["choices"][0].get("message", {})
                response_text = assistant_message.get("content", "Пустой ответ от модели")

                return {
                    "text": response_text,
                    "full_response": result,
                    "usage": result.get("usage", {})
                }
            else:
                logger.warning("⚠️ Неожиданный формат ответа от LM Studio")
                return {"text": "Не удалось получить ответ от модели"}

    except asyncio.TimeoutError:
        logger.error("⏰ Таймаут запроса к модели")
        return {"text": "⏰ Таймаут при запросе к модели. Попробуйте позже."}
    except aiohttp.ClientConnectorError:
        logger.error("🔌 Ошибка подключения к LM Studio")
        return {"text": "🔌 Не удалось подключиться к модели. Убедитесь, что LM Studio запущен."}
    except Exception as e:
        logger.error(f"❌ Ошибка в query_model_local_api: {e}\n{traceback.format_exc()}")
        return {"text": f"❌ Ошибка при запросе к модели: {str(e)}"}


# Отправка ответа пользователю
async def send_response(message: Message, response_data: dict):
    try:
        text_response = response_data.get("text", "")

        # Обрезаем слишком длинные ответы для Telegram
        if len(text_response) > 4000:
            text_response = text_response[:4000] + "\n\n... (сообщение обрезано)"

        await message.answer(text_response)
        logger.debug("✅ Ответ отправлен пользователю")

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

        # Проверяем доступность LM Studio
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(MODEL_API_URL.replace('/v1/chat/completions', '/v1/models'),
                                       timeout=10) as response:
                    if response.status == 200:
                        logger.info("✅ LM Studio доступен")
                    else:
                        logger.warning(f"⚠️ LM Studio отвечает с кодом {response.status}")
            except Exception as e:
                logger.warning(f"⚠️ LM Studio недоступен: {e}")

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
