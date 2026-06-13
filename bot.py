import asyncio
import os
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
import database as db
from handlers import client, admin

TOKEN = os.getenv("TOKEN", "8967616858:AAGHgXsuVj6vf1biiQTRlhTZ_TZ8ApHf6mk")

bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())

async def main():
    # Инициализируем базу данных
    await db.init_db()
    
    # Подключаем роутеры
    dp.include_router(admin.router)
    dp.include_router(client.router)
    
    print("Бот запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())