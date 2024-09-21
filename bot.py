import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters.command import Command
from dotenv import load_dotenv
from aiogram.utils.keyboard import InlineKeyboardBuilder  # импорт для инлайн кнопок
from aiogram.types import BotCommand  # иморт для стартового меню
from aiogram.client.default import DefaultBotProperties  # настройки редактирования бота
from aiogram.enums import ParseMode
import emoji

# Включаем логирование, чтобы не пропустить важные сообщения
logging.basicConfig(level=logging.INFO)

# Загружаем TOKEN
load_dotenv()
TOKEN = os.getenv("TOKEN")

bot = Bot(
    token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)  # Объект бота
dp = Dispatcher()  # Диспетчер


# Создаем асинхронную функцию стартового меню
async def set_main_menu(bot: Bot):
    # Создаем список с командами и их описанием для кнопки menu
    main_menu_commands = [
        BotCommand(command="/make", description="Дела"),
        BotCommand(command="/buy", description="Продукты"),
        BotCommand(command="/help", description="Справка по работе бота"),
    ]
    await bot.set_my_commands(main_menu_commands)


# Приветствие перед Start
async def set_my_description(bot: Bot):
    main_description = "Это бот для записи дел и покупок!"
    await bot.set_my_description(main_description)


# Хэндлер на команду /start
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    # генерация клавиатуры
    builder = InlineKeyboardBuilder()
    builder.button(text=emoji.emojize(":red_heart: Дела"), callback_data="make")
    builder.button(text="Продукты", callback_data="buy")
    # сообщение
    await message.answer(
        "<b>Выберите пожалуйста действие:</b> \n"
        "/help - что умеет этот бот\n"
        "/make - разобраться с делами\n"
        "/buy - запланировать покупки\n",
        reply_markup=builder.as_markup(),
    )


@dp.callback_query(F.data == "make")
async def send_random_value(callback: types.CallbackQuery):
    builder = InlineKeyboardBuilder()
    builder.button(text="Записать дело", callback_data="???")
    builder.button(text="Список дел", callback_data="buy")
    await callback.message.answer(
        "Что ж...давайте займёмся делами!\n", reply_markup=builder.as_markup()
    )


# Регистрируем асинхронные функции в диспетчере,
# Они выполняются на старте бота.
dp.startup.register(set_main_menu)
dp.startup.register(set_my_description)


# Запуск процесса поллинга новых апдейтов
async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
