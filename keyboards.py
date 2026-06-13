from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

# Главное меню клиента
def main_menu():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📅 Записаться", callback_data="book")],
        [InlineKeyboardButton(text="📋 Мои записи", callback_data="my_bookings")],
        [InlineKeyboardButton(text="ℹ️ Информация", callback_data="info")]
    ])
    return keyboard

# Список услуг
def services_keyboard(services):
    buttons = []
    for service in services:
        # service = (id, name, price, duration)
        buttons.append([InlineKeyboardButton(
            text=f"{service[1]} — {service[2]}₽ ({service[3]} мин)",
            callback_data=f"service_{service[0]}"
        )])
    buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data="back_main")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# Выбор даты (7 дней вперёд)
def dates_keyboard():
    from datetime import datetime, timedelta
    buttons = []
    today = datetime.now()
    for i in range(7):
        date = today + timedelta(days=i)
        day_str = date.strftime("%d.%m.%Y")
        day_name = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"][date.weekday()]
        buttons.append([InlineKeyboardButton(
            text=f"{day_name} {day_str}",
            callback_data=f"date_{day_str}"
        )])
    buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data="book")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# Выбор времени
def times_keyboard(times, booked_times):
    buttons = []
    row = []
    for time in times:
        if time in booked_times:
            row.append(InlineKeyboardButton(
                text=f"❌ {time}",
                callback_data="time_booked"
            ))
        else:
            row.append(InlineKeyboardButton(
                text=f"✅ {time}",
                callback_data=f"time_{time}"
            ))
        if len(row) == 3:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data="back_date")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# Подтверждение записи
def confirm_keyboard():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Подтвердить", callback_data="do_confirm_booking")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="back_main")]
    ])
    return keyboard

# Панель администратора
def admin_menu():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📋 Все записи", callback_data="admin_bookings")],
        [InlineKeyboardButton(text="📊 Статистика", callback_data="admin_stats")],
        [InlineKeyboardButton(text="✂️ Услуги", callback_data="admin_services")],
        [InlineKeyboardButton(text="🕐 Расписание", callback_data="admin_schedule")],
        [InlineKeyboardButton(text="⚙️ Настройки", callback_data="admin_settings")]
    ])
    return keyboard

# Управление услугами
def admin_services_keyboard(services):
    buttons = []
    for service in services:
        buttons.append([InlineKeyboardButton(
            text=f"🗑 {service[1]} — {service[2]}₽",
            callback_data=f"del_service_{service[0]}"
        )])
    buttons.append([InlineKeyboardButton(text="➕ Добавить услугу", callback_data="add_service")])
    buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data="admin_menu")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# Управление расписанием
def admin_schedule_keyboard(schedule):
    days = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
    buttons = []
    for slot in schedule:
        buttons.append([InlineKeyboardButton(
            text=f"🗑 {days[slot[1]]} {slot[2]}-{slot[3]}",
            callback_data=f"del_schedule_{slot[0]}"
        )])
    buttons.append([InlineKeyboardButton(text="➕ Добавить день", callback_data="add_schedule")])
    buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data="admin_menu")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)
    
# Кнопки для записей клиента
def my_bookings_keyboard(bookings):
    buttons = []
    for booking in bookings:
        # booking = (id, name, date, time, status)
        status = "✅" if booking[4] == "confirmed" else "⏳"
        buttons.append([InlineKeyboardButton(
            text=f"{status} {booking[1]} — {booking[2]} {booking[3]}",
            callback_data=f"booking_{booking[0]}"
        )])
    buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data="back_main")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# Детали записи клиента
def booking_detail_keyboard(booking_id):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Отменить запись", callback_data=f"cancel_{booking_id}")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="my_bookings")]
    ])
    return keyboard

# Кнопки подтверждения для админа
def admin_confirm_keyboard(booking_id, user_id):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Подтвердить", callback_data=f"confirm_{booking_id}_{user_id}")],
        [InlineKeyboardButton(text="❌ Отклонить", callback_data=f"reject_{booking_id}_{user_id}")]
    ])
    return keyboard
    
def settings_keyboard():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👋 Изменить приветствие", callback_data="edit_welcome")],
        [InlineKeyboardButton(text="ℹ️ Изменить информацию", callback_data="edit_info")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="admin_menu")]
    ])
    return keyboard