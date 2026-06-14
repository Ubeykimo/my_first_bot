import asyncio
import os
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
import database as db
from handlers import client, admin

TOKEN = os.getenv("TOKEN")

bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())

async def send_reminders(bot):
    while True:
        try:
            async with __import__('aiosqlite').connect("bot.db") as db_conn:
                now = datetime.now()
                reminder_time = now + timedelta(hours=1)
                date_str = reminder_time.strftime("%d.%m.%Y")
                time_str = reminder_time.strftime("%H:%M")
                
                cursor = await db_conn.execute("""
                    SELECT b.user_id, b.user_name, s.name, b.date, b.time
                    FROM bookings b
                    JOIN services s ON b.service_id = s.id
                    WHERE b.date = ? AND b.time = ? 
                    AND b.status = 'confirmed'
                    AND b.reminded = 0
                """, (date_str, time_str))
                bookings = await cursor.fetchall()
                
                for booking in bookings:
                    try:
                        await bot.send_message(
                            booking[0],
                            f"⏰ Напоминание!\n\n"
                            f"Через час у вас запись:\n"
                            f"✂️ {booking[2]}\n"
                            f"📅 {booking[3]} в {booking[4]}"
                        )
                        await db_conn.execute(
                            "UPDATE bookings SET reminded = 1 WHERE user_id = ? AND date = ? AND time = ?",
                            (booking[0], booking[3], booking[4])
                        )
                        await db_conn.commit()
                    except Exception:
                        pass
        except Exception as e:
            print(f"Ошибка напоминания: {e}")
        
        await asyncio.sleep(1800)

async def main():
    await db.init_db()
    
    dp.include_router(admin.router)
    dp.include_router(client.router)
    
    print("Бот запущен!")
    
    asyncio.create_task(send_reminders(bot))
    
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())