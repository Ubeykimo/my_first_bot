import aiosqlite

DB_PATH = "bot.db"

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        # Услуги
        await db.execute("""
            CREATE TABLE IF NOT EXISTS services (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                price INTEGER NOT NULL,
                duration INTEGER NOT NULL
            )
        """)
        # Расписание
        await db.execute("""
            CREATE TABLE IF NOT EXISTS schedule (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                day_of_week INTEGER NOT NULL,
                start_time TEXT NOT NULL,
                end_time TEXT NOT NULL
            )
        """)
        # Записи
        await db.execute("""
            CREATE TABLE IF NOT EXISTS bookings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                user_name TEXT,
                service_id INTEGER NOT NULL,
                date TEXT NOT NULL,
                time TEXT NOT NULL,
                status TEXT DEFAULT 'pending'
            )
        """)
        # Настройки
        await db.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
        """)
        await db.commit()

# ═══ УСЛУГИ ═══
async def get_services():
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT * FROM services")
        return await cursor.fetchall()

async def add_service(name, price, duration):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO services (name, price, duration) VALUES (?, ?, ?)",
            (name, price, duration)
        )
        await db.commit()

async def delete_service(service_id):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM services WHERE id = ?", (service_id,))
        await db.commit()

# ═══ РАСПИСАНИЕ ═══
async def get_schedule():
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT * FROM schedule")
        return await cursor.fetchall()

async def add_schedule(day_of_week, start_time, end_time):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO schedule (day_of_week, start_time, end_time) VALUES (?, ?, ?)",
            (day_of_week, start_time, end_time)
        )
        await db.commit()

async def delete_schedule(schedule_id):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM schedule WHERE id = ?", (schedule_id,))
        await db.commit()

# ═══ ЗАПИСИ ═══
async def get_bookings():
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("""
            SELECT b.id, b.user_name, s.name, b.date, b.time, b.status
            FROM bookings b
            JOIN services s ON b.service_id = s.id
            ORDER BY b.date, b.time
        """)
        return await cursor.fetchall()

async def get_booked_times(date):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT time FROM bookings WHERE date = ? AND status != 'cancelled'",
            (date,)
        )
        rows = await cursor.fetchall()
        return [row[0] for row in rows]

async def add_booking(user_id, user_name, service_id, date, time):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO bookings (user_id, user_name, service_id, date, time) VALUES (?, ?, ?, ?, ?)",
            (user_id, user_name, service_id, date, time)
        )
        await db.commit()

# ═══ НАСТРОЙКИ ═══
async def get_setting(key):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT value FROM settings WHERE key = ?", (key,)
        )
        row = await cursor.fetchone()
        return row[0] if row else None

async def set_setting(key, value):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
            (key, value)
        )
        await db.commit()