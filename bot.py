import asyncio
import os
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand
from database import Database
from handlers import router
from utils.logger import setup_logger

# Инициализация логгера
logger = setup_logger()

# Загрузка переменных окружения
load_dotenv()
TOKEN = os.getenv('BOT_TOKEN')

# Инициализация бота и диспетчера
bot = Bot(token=TOKEN)
dp = Dispatcher()
db = Database()

# Регистрация роутера
dp.include_router(router)

# Настройка команд бота
async def set_commands(bot: Bot):
    commands = [
        BotCommand(command="start", description="Запустить бота"),
        BotCommand(command="help", description="Показать справку"),
        BotCommand(command="todo", description="Добавить задачу"),
        BotCommand(command="list", description="Показать текущие задачи"),
        BotCommand(command="listall", description="Показать все задачи"),
        BotCommand(command="retask", description="Отметить задачу выполненной"),
        BotCommand(command="reminder", description="Установить напоминание для задачи")
    ]
    await bot.set_my_commands(commands)

# Запуск бота
async def main():
    logger.info("Bot started")
    try:
        # Установка команд в меню
        await set_commands(bot)
        await db.init()
        # Удаляем незавершенные обновления
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    except Exception as e:
        logger.error(f"Error occurred: {e}")
    finally:
        await bot.session.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped") 