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
@router.callback_query(F.data == "do_confirm_booking")
async def confirm_booking(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    user = callback.from_user
    
    # Берём username если есть, иначе full_name
    if user.username:
        user_name = f"@{user.username}"
    else:
        user_name = user.full_name
    
    booking_id = await db.add_booking(
        user_id=user.id,
        user_name=user_name,
        service_id=data['service_id'],
        date=data['date'],
        time=data['time']
    )
    
    await state.clear()
    await callback.message.edit_text(
        f"✅ Запись подтверждена!\n\n"
        f"✂️ Услуга: {data['service_name']}\n"
        f"📅 Дата: {data['date']}\n"
        f"🕐 Время: {data['time']}\n\n"
        f"Ждём вас!",
        reply_markup=kb.main_menu()
    )
    
    admin_id = await db.get_setting("admin_id")
    if admin_id:
        await callback.bot.send_message(
            int(admin_id),
            f"🔔 Новая запись!\n\n"
            f"👤 Клиент: {user.full_name}\n"
            f"✂️ Услуга: {data['service_name']}\n"
            f"📅 Дата: {data['date']}\n"
            f"🕐 Время: {data['time']}",
            reply_markup=kb.admin_confirm_keyboard(booking_id, user.id)
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
    bookings = await db.get_user_bookings(callback.from_user.id)
    
    if not bookings:
        await callback.message.edit_text(
            "У вас нет активных записей.",
            reply_markup=kb.main_menu()
        )
        return
    
    await callback.message.edit_text(
        "📋 Ваши записи — выберите для деталей:",
        reply_markup=kb.my_bookings_keyboard(bookings)
    )

# Детали записи
@router.callback_query(F.data.startswith("booking_"))
async def booking_detail(callback: CallbackQuery):
    booking_id = int(callback.data.split("_")[1])
    booking = await db.get_booking_by_id(booking_id)
    
    if not booking or booking[1] != callback.from_user.id:
        await callback.answer("Запись не найдена", show_alert=True)
        return
    
    status = "✅ Подтверждена" if booking[6] == "confirmed" else "⏳ Ожидает подтверждения"
    await callback.message.edit_text(
        f"📋 Детали записи:\n\n"
        f"✂️ Услуга: {booking[3]}\n"
        f"📅 Дата: {booking[4]}\n"
        f"🕐 Время: {booking[5]}\n"
        f"Статус: {status}",
        reply_markup=kb.booking_detail_keyboard(booking_id)
    )

# Отмена записи клиентом
@router.callback_query(F.data.startswith("cancel_"))
async def cancel_booking(callback: CallbackQuery):
    booking_id = int(callback.data.split("_")[1])
    booking = await db.get_booking_by_id(booking_id)
    
    if not booking or booking[1] != callback.from_user.id:
        await callback.answer("Запись не найдена", show_alert=True)
        return
    
    await db.cancel_booking(booking_id, callback.from_user.id)
    
    # Уведомление администратору
    admin_id = await db.get_setting("admin_id")
    if admin_id:
        await callback.bot.send_message(
            int(admin_id),
            f"❌ Клиент отменил запись!\n\n"
            f"👤 Клиент: {booking[2]}\n"
            f"✂️ Услуга: {booking[3]}\n"
            f"📅 Дата: {booking[4]}\n"
            f"🕐 Время: {booking[5]}"
        )
    
    await callback.message.edit_text(
        "✅ Запись отменена.",
        reply_markup=kb.main_menu()
    )

@router.callback_query(F.data == "back_date")
async def back_date(callback: CallbackQuery, state: FSMContext):
    await state.set_state(BookingStates.choosing_date)
    await callback.message.edit_text(
        "Выберите дату:",
        reply_markup=kb.dates_keyboard()
    )

@router.callback_query(F.data == "info")
async def info(callback: CallbackQuery):
    info_text = await db.get_setting("info_text") or "Информация не добавлена."
    await callback.message.edit_text(
        f"ℹ️ Информация\n\n{info_text}",
        reply_markup=kb.main_menu()
    )