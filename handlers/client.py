from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from datetime import datetime, timedelta
import database as db
import keyboards as kb

router = Router()

# Состояния
class BookingStates(StatesGroup):
    choosing_service = State()
    choosing_date = State()
    choosing_time = State()
    confirming = State()

# Команда /start
@router.message(F.text == "/start")
async def start(message: Message, state: FSMContext):
    await state.clear()
    welcome = await db.get_setting("welcome_text")
    if not welcome:
        welcome = "Добро пожаловать! Выберите действие:"
    await message.answer(welcome, reply_markup=kb.main_menu())

# Записаться
@router.callback_query(F.data == "book")
async def book(callback: CallbackQuery, state: FSMContext):
    services = await db.get_services()
    if not services:
        await callback.answer("Услуги не добавлены", show_alert=True)
        return
    await state.set_state(BookingStates.choosing_service)
    await callback.message.edit_text(
        "Выберите услугу:",
        reply_markup=kb.services_keyboard(services)
    )

# Выбор услуги
@router.callback_query(F.data.startswith("service_"))
async def choose_service(callback: CallbackQuery, state: FSMContext):
    service_id = int(callback.data.split("_")[1])
    services = await db.get_services()
    service = next((s for s in services if s[0] == service_id), None)
    if not service:
        await callback.answer("Услуга не найдена", show_alert=True)
        return
    await state.update_data(
        service_id=service_id,
        service_name=service[1],
        service_price=service[2]
    )
    await state.set_state(BookingStates.choosing_date)
    await callback.message.edit_text(
        "Выберите дату:",
        reply_markup=kb.dates_keyboard()
    )

# Выбор даты
@router.callback_query(F.data.startswith("date_"))
async def choose_date(callback: CallbackQuery, state: FSMContext):
    date = callback.data.split("_")[1]
    
    # Генерируем временные слоты
    schedule = await db.get_schedule()
    if not schedule:
        await callback.answer("Расписание не настроено", show_alert=True)
        return
    
    # Берём первое расписание (потом можно улучшить)
    slot = schedule[0]
    start_time = datetime.strptime(slot[2], "%H:%M")
    end_time = datetime.strptime(slot[3], "%H:%M")
    
    times = []
    current = start_time
    while current < end_time:
        times.append(current.strftime("%H:%M"))
        current += timedelta(minutes=30)
    
    booked_times = await db.get_booked_times(date)
    
    await state.update_data(date=date, available_times=times)
    await state.set_state(BookingStates.choosing_time)
    await callback.message.edit_text(
        f"Дата: {date}\nВыберите время:",
        reply_markup=kb.times_keyboard(times, booked_times)
    )

# Занятое время
@router.callback_query(F.data == "time_booked")
async def time_booked(callback: CallbackQuery):
    await callback.answer("Это время уже занято!", show_alert=True)

# Выбор времени
@router.callback_query(F.data.startswith("time_"))
async def choose_time(callback: CallbackQuery, state: FSMContext):
    time = callback.data.replace("time_", "")
    await state.update_data(time=time)
    
    data = await state.get_data()
    await state.set_state(BookingStates.confirming)
    await callback.message.edit_text(
        f"Подтвердите запись:\n\n"
        f"📋 Услуга: {data['service_name']}\n"
        f"💰 Цена: {data['service_price']}₽\n"
        f"📅 Дата: {data['date']}\n"
        f"🕐 Время: {time}",
        reply_markup=kb.confirm_keyboard()
    )

# Подтверждение записи
@router.callback_query(F.data == "confirm_booking")
async def confirm_booking(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    user = callback.from_user
    
    await db.add_booking(
        user_id=user.id,
        user_name=user.full_name,
        service_id=data['service_id'],
        date=data['date'],
        time=data['time']
    )
    
    await state.clear()
    await callback.message.edit_text(
        f"✅ Запись подтверждена!\n\n"
        f"📋 Услуга: {data['service_name']}\n"
        f"📅 Дата: {data['date']}\n"
        f"🕐 Время: {data['time']}\n\n"
        f"Ждём вас!",
        reply_markup=kb.main_menu()
    )
    
    # Уведомление администратору
    admin_id = await db.get_setting("admin_id")
    if admin_id:
        await callback.bot.send_message(
            int(admin_id),
            f"🔔 Новая запись!\n\n"
            f"👤 Клиент: {user.full_name}\n"
            f"📋 Услуга: {data['service_name']}\n"
            f"📅 Дата: {data['date']}\n"
            f"🕐 Время: {data['time']}"
        )

# Назад в главное меню
@router.callback_query(F.data == "back_main")
async def back_main(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    welcome = await db.get_setting("welcome_text")
    if not welcome:
        welcome = "Выберите действие:"
    await callback.message.edit_text(welcome, reply_markup=kb.main_menu())

# Мои записи
@router.callback_query(F.data == "my_bookings")
async def my_bookings(callback: CallbackQuery):
    async with __import__('aiosqlite').connect("bot.db") as db_conn:
        cursor = await db_conn.execute("""
            SELECT s.name, b.date, b.time, b.status
            FROM bookings b
            JOIN services s ON b.service_id = s.id
            WHERE b.user_id = ?
            ORDER BY b.date, b.time
        """, (callback.from_user.id,))
        bookings = await cursor.fetchall()
    
    if not bookings:
        await callback.message.edit_text(
            "У вас нет записей.",
            reply_markup=kb.main_menu()
        )
        return
    
    text = "📋 Ваши записи:\n\n"
    for booking in bookings:
        status = "✅" if booking[3] == "confirmed" else "⏳"
        text += f"{status} {booking[0]}\n📅 {booking[1]} в {booking[2]}\n\n"
    
    await callback.message.edit_text(text, reply_markup=kb.main_menu())