from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import database as db
import keyboards as kb

router = Router()

# Состояния администратора
class AdminStates(StatesGroup):
    adding_service_name = State()
    adding_service_price = State()
    adding_service_duration = State()
    adding_schedule_day = State()
    adding_schedule_start = State()
    adding_schedule_end = State()
    editing_welcome = State()

# Команда /admin
@router.message(F.text == "/admin")
async def admin_panel(message: Message, state: FSMContext):
    await state.clear()
    admin_id = await db.get_setting("admin_id")
    
    # Если админ не установлен — первый кто написал становится админом
    if not admin_id:
        await db.set_setting("admin_id", str(message.from_user.id))
        admin_id = str(message.from_user.id)
    
    if str(message.from_user.id) != admin_id:
        await message.answer("❌ У вас нет доступа")
        return
    
    await message.answer("👨‍💼 Панель администратора", reply_markup=kb.admin_menu())

# Меню админа
@router.callback_query(F.data == "admin_menu")
async def admin_menu(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(
        "👨‍💼 Панель администратора",
        reply_markup=kb.admin_menu()
    )

# Все записи
@router.callback_query(F.data == "admin_bookings")
async def admin_bookings(callback: CallbackQuery):
    bookings = await db.get_bookings()
    if not bookings:
        await callback.message.edit_text(
            "Записей нет.",
            reply_markup=kb.admin_menu()
        )
        return
    
    text = "📋 Все записи:\n\n"
    for booking in bookings:
        text += (
            f"👤 {booking[1]}\n"
            f"✂️ {booking[2]}\n"
            f"📅 {booking[3]} в {booking[4]}\n"
            f"Статус: {booking[5]}\n\n"
        )
    
    await callback.message.edit_text(text, reply_markup=kb.admin_menu())

# Управление услугами
@router.callback_query(F.data == "admin_services")
async def admin_services(callback: CallbackQuery):
    services = await db.get_services()
    await callback.message.edit_text(
        "✂️ Управление услугами:",
        reply_markup=kb.admin_services_keyboard(services)
    )

# Удалить услугу
@router.callback_query(F.data.startswith("del_service_"))
async def delete_service(callback: CallbackQuery):
    service_id = int(callback.data.split("_")[2])
    await db.delete_service(service_id)
    services = await db.get_services()
    await callback.message.edit_text(
        "✂️ Услуга удалена. Управление услугами:",
        reply_markup=kb.admin_services_keyboard(services)
    )

# Добавить услугу — шаг 1
@router.callback_query(F.data == "add_service")
async def add_service_start(callback: CallbackQuery, state: FSMContext):
    await state.set_state(AdminStates.adding_service_name)
    await callback.message.edit_text("Введите название услуги:")

# Добавить услугу — шаг 2
@router.message(AdminStates.adding_service_name)
async def add_service_name(message: Message, state: FSMContext):
    await state.update_data(service_name=message.text)
    await state.set_state(AdminStates.adding_service_price)
    await message.answer("Введите цену услуги (только цифры):")

# Добавить услугу — шаг 3
@router.message(AdminStates.adding_service_price)
async def add_service_price(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("Введите только цифры!")
        return
    await state.update_data(service_price=int(message.text))
    await state.set_state(AdminStates.adding_service_duration)
    await message.answer("Введите длительность в минутах (например 30 или 60):")

# Добавить услугу — шаг 4
@router.message(AdminStates.adding_service_duration)
async def add_service_duration(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("Введите только цифры!")
        return
    data = await state.get_data()
    await db.add_service(data['service_name'], data['service_price'], int(message.text))
    await state.clear()
    services = await db.get_services()
    await message.answer(
        f"✅ Услуга '{data['service_name']}' добавлена!",
        reply_markup=kb.admin_services_keyboard(services)
    )

# Управление расписанием
@router.callback_query(F.data == "admin_schedule")
async def admin_schedule(callback: CallbackQuery):
    schedule = await db.get_schedule()
    await callback.message.edit_text(
        "🕐 Управление расписанием:",
        reply_markup=kb.admin_schedule_keyboard(schedule)
    )

# Удалить расписание
@router.callback_query(F.data.startswith("del_schedule_"))
async def delete_schedule(callback: CallbackQuery):
    schedule_id = int(callback.data.split("_")[2])
    await db.delete_schedule(schedule_id)
    schedule = await db.get_schedule()
    await callback.message.edit_text(
        "🕐 День удалён. Управление расписанием:",
        reply_markup=kb.admin_schedule_keyboard(schedule)
    )

# Добавить расписание — шаг 1
@router.callback_query(F.data == "add_schedule")
async def add_schedule_start(callback: CallbackQuery, state: FSMContext):
    await state.set_state(AdminStates.adding_schedule_day)
    await callback.message.edit_text(
        "Введите день недели цифрой:\n"
        "0 = Пн, 1 = Вт, 2 = Ср, 3 = Чт, 4 = Пт, 5 = Сб, 6 = Вс"
    )

# Добавить расписание — шаг 2
@router.message(AdminStates.adding_schedule_day)
async def add_schedule_day(message: Message, state: FSMContext):
    if not message.text.isdigit() or int(message.text) > 6:
        await message.answer("Введите цифру от 0 до 6!")
        return
    await state.update_data(schedule_day=int(message.text))
    await state.set_state(AdminStates.adding_schedule_start)
    await message.answer("Введите время начала работы (например 09:00):")

# Добавить расписание — шаг 3
@router.message(AdminStates.adding_schedule_start)
async def add_schedule_start_time(message: Message, state: FSMContext):
    await state.update_data(schedule_start=message.text)
    await state.set_state(AdminStates.adding_schedule_end)
    await message.answer("Введите время конца работы (например 18:00):")

# Добавить расписание — шаг 4
@router.message(AdminStates.adding_schedule_end)
async def add_schedule_end_time(message: Message, state: FSMContext):
    data = await state.get_data()
    days = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
    await db.add_schedule(data['schedule_day'], data['schedule_start'], message.text)
    await state.clear()
    schedule = await db.get_schedule()
    await message.answer(
        f"✅ Добавлено: {days[data['schedule_day']]} {data['schedule_start']}-{message.text}",
        reply_markup=kb.admin_schedule_keyboard(schedule)
    )

# Настройки
@router.callback_query(F.data == "admin_settings")
async def admin_settings(callback: CallbackQuery, state: FSMContext):
    await state.set_state(AdminStates.editing_welcome)
    welcome = await db.get_setting("welcome_text") or "Не задано"
    await callback.message.edit_text(
        f"⚙️ Текущее приветствие:\n{welcome}\n\nВведите новый текст приветствия:"
    )

# Сохранить приветствие
@router.message(AdminStates.editing_welcome)
async def save_welcome(message: Message, state: FSMContext):
    await db.set_setting("welcome_text", message.text)
    await state.clear()
    await message.answer(
        "✅ Приветствие обновлено!",
        reply_markup=kb.admin_menu()
    )
    
# Подтверждение записи администратором
@router.callback_query(F.data.startswith("confirm_"))
async def confirm_booking_admin(callback: CallbackQuery):
    parts = callback.data.split("_")
    booking_id = int(parts[1])
    user_id = int(parts[2])
    
    booking = await db.get_booking_by_id(booking_id)
    if not booking:
        await callback.answer("Запись не найдена", show_alert=True)
        return
    
    await db.confirm_booking(booking_id)
    
    # Уведомление клиенту
    await callback.bot.send_message(
        user_id,
        f"✅ Ваша запись подтверждена!\n\n"
        f"✂️ Услуга: {booking[3]}\n"
        f"📅 Дата: {booking[4]}\n"
        f"🕐 Время: {booking[5]}\n\n"
        f"Ждём вас!"
    )
    
    await callback.message.edit_text(
        f"✅ Запись подтверждена!\n\n"
        f"👤 Клиент: {booking[2]}\n"
        f"✂️ Услуга: {booking[3]}\n"
        f"📅 {booking[4]} в {booking[5]}"
    )

# Отклонение записи администратором
@router.callback_query(F.data.startswith("reject_"))
async def reject_booking_admin(callback: CallbackQuery):
    parts = callback.data.split("_")
    booking_id = int(parts[1])
    user_id = int(parts[2])
    
    booking = await db.get_booking_by_id(booking_id)
    if not booking:
        await callback.answer("Запись не найдена", show_alert=True)
        return
    
    await db.reject_booking(booking_id)
    
    # Уведомление клиенту
    await callback.bot.send_message(
        user_id,
        f"❌ Ваша запись отклонена.\n\n"
        f"✂️ Услуга: {booking[3]}\n"
        f"📅 Дата: {booking[4]}\n"
        f"🕐 Время: {booking[5]}\n\n"
        f"Пожалуйста, выберите другое время."
    )
    
    await callback.message.edit_text(
        f"❌ Запись отклонена.\n\n"
        f"👤 Клиент: {booking[2]}\n"
        f"✂️ Услуга: {booking[3]}\n"
        f"📅 {booking[4]} в {booking[5]}"
    )