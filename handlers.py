from aiogram import Router, F, types
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
import logging
from database import Database

router = Router(name="main_router")
logger = logging.getLogger('bot_logger')
db = Database()


class TaskStates(StatesGroup):
    waiting_for_task = State()
    waiting_for_importance = State()
    waiting_for_task_id = State()


def get_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Добавить задачу", callback_data="todo"),
                InlineKeyboardButton(text="Список задач", callback_data="list")
            ],
            [
                InlineKeyboardButton(text="Все задачи", callback_data="listall"),
                InlineKeyboardButton(text="Выполнить задачу", callback_data="retask")
            ],
            [
                InlineKeyboardButton(text="Помощь", callback_data="help")
            ]
        ]
    )


def get_importance_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Очень важная", callback_data="high")],
            [InlineKeyboardButton(text="Средней важности", callback_data="medium")],
            [InlineKeyboardButton(text="Не очень важная", callback_data="low")]
        ]
    )


@router.message(Command("start"))
async def cmd_start(message: types.Message):
    logger.info(f"User {message.from_user.id} started the bot")
    await message.answer(
        "👋 Привет! Я бот-планировщик задач.\n"
        "Я помогу вам организовать ваши задачи и следить за их выполнением.\n"
        "Используйте команду /help для получения списка всех команд.",
        reply_markup=get_keyboard()
    )


@router.message(Command("help"))
async def cmd_help(message: types.Message):
    logger.info(f"User {message.from_user.id} requested help")
    await message.answer(
        "📝 Доступные команды:\n"
        "/todo - Добавить новую задачу\n"
        "/list - Показать список невыполненных задач\n"
        "/listall - Показать все задачи\n"
        "/retask - Отметить задачу как выполненную",
        reply_markup=get_keyboard()
    )


@router.callback_query(F.data == "todo")
async def callback_todo(callback: CallbackQuery, state: FSMContext):
    logger.info(f"User {callback.from_user.id} initiated task creation")
    await callback.message.answer("Введите текст задачи:")
    await state.set_state(TaskStates.waiting_for_task)
    await callback.answer()


@router.message(StateFilter(TaskStates.waiting_for_task))
async def process_task_text(message: types.Message, state: FSMContext):
    await state.update_data(task_text=message.text)
    await message.answer(
        "Выберите важность задачи:",
        reply_markup=get_importance_keyboard()
    )
    await state.set_state(TaskStates.waiting_for_importance)


@router.callback_query(StateFilter(TaskStates.waiting_for_importance))
async def process_importance(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    task_text = data["task_text"]
    importance = callback.data

    await db.add_task(task_text, importance)
    logger.info(f"User {callback.from_user.id} added task: {task_text} with importance: {importance}")
    await callback.message.answer("Задача успешно добавлена!", reply_markup=get_keyboard())
    await state.clear()
    await callback.answer()


@router.callback_query(F.data == "list")
async def callback_list(callback: CallbackQuery):
    logger.info(f"User {callback.from_user.id} requested tasks list")
    tasks = await db.get_tasks(completed=False)
    if not tasks:
        await callback.message.answer("У вас нет активных задач!")
        return

    response = "📋 Ваши активные задачи:\n\n"
    for task in tasks:
        response += f"ID: {task[0]}\n"
        response += f"Задача: {task[1]}\n"
        response += f"Создана: {task[2]}\n"
        response += f"Важность: {task[3]}\n\n"

    await callback.message.answer(response, reply_markup=get_keyboard())
    await callback.answer()


@router.callback_query(F.data == "listall")
async def callback_listall(callback: CallbackQuery):
    logger.info(f"User {callback.from_user.id} requested all tasks")
    tasks = await db.get_all_tasks()
    if not tasks:
        await callback.message.answer("База задач пуста!")
        return

    response = "📋 Все задачи:\n\n"
    for task in tasks:
        status = "✅ Выполнено" if task[4] else "❌ Не выполнено"
        response += f"ID: {task[0]}\n"
        response += f"Задача: {task[1]}\n"
        response += f"Создана: {task[2]}\n"
        response += f"Важность: {task[3]}\n"
        response += f"Статус: {status}\n\n"

    await callback.message.answer(response, reply_markup=get_keyboard())
    await callback.answer()


@router.callback_query(F.data == "retask")
async def callback_retask(callback: CallbackQuery, state: FSMContext):
    logger.info(f"User {callback.from_user.id} trying to complete task")
    await callback.message.answer("Введите ID задачи, которую хотите отметить как выполненную:")
    await state.set_state(TaskStates.waiting_for_task_id)
    await callback.answer()


@router.message(StateFilter(TaskStates.waiting_for_task_id))
async def process_task_completion(message: types.Message, state: FSMContext):
    try:
        task_id = int(message.text)
        await db.complete_task(task_id)
        logger.info(f"User {message.from_user.id} completed task {task_id}")
        await message.answer("Задача отмечена как выполненная!", reply_markup=get_keyboard())
    except ValueError:
        await message.answer("Пожалуйста, введите корректный ID задачи!")
    finally:
        await state.clear()


@router.callback_query(F.data == "help")
async def callback_help(callback: CallbackQuery):
    logger.info(f"User {callback.from_user.id} requested help via button")
    await callback.message.answer(
        "📝 Доступные команды:\n"
        "/todo - Добавить новую задачу\n"
        "/list - Показать список невыполненных задач\n"
        "/listall - Показать все задачи\n"
        "/retask - Отметить задачу как выполненную",
        reply_markup=get_keyboard()
    )
    await callback.answer()


@router.message(Command("todo"))
async def cmd_todo(message: types.Message, state: FSMContext):
    logger.info(f"User {message.from_user.id} started creating new task via command")
    await message.answer("Введите текст задачи:")
    await state.set_state(TaskStates.waiting_for_task)


@router.message(Command("list"))
async def cmd_list(message: types.Message):
    logger.info(f"User {message.from_user.id} requested tasks list via command")
    tasks = await db.get_tasks(completed=False)
    if not tasks:
        await message.answer("У вас нет активных задач!", reply_markup=get_keyboard())
        return

    response = "📋 Ваши активные задачи:\n\n"
    for task in tasks:
        response += f"ID: {task[0]}\n"
        response += f"Задача: {task[1]}\n"
        response += f"Создана: {task[2]}\n"
        response += f"Важность: {task[3]}\n\n"

    await message.answer(response, reply_markup=get_keyboard())


@router.message(Command("listall"))
async def cmd_listall(message: types.Message):
    logger.info(f"User {message.from_user.id} requested all tasks via command")
    tasks = await db.get_all_tasks()
    if not tasks:
        await message.answer("База задач пуста!", reply_markup=get_keyboard())
        return

    response = "📋 Все задачи:\n\n"
    for task in tasks:
        status = "✅ Выполнено" if task[4] else "❌ Не выполнено"
        response += f"ID: {task[0]}\n"
        response += f"Задача: {task[1]}\n"
        response += f"Создана: {task[2]}\n"
        response += f"Важность: {task[3]}\n"
        response += f"Статус: {status}\n\n"

    await message.answer(response, reply_markup=get_keyboard())


@router.message(Command("retask"))
async def cmd_retask(message: types.Message, state: FSMContext):
    logger.info(f"User {message.from_user.id} trying to complete task via command")
    await message.answer("Введите ID задачи, которую хотите отметить как выполненную:")
    await state.set_state(TaskStates.waiting_for_task_id)

# Остальные обработчики аналогично обновляются с использованием CallbackQuery
# и добавлением логирования
