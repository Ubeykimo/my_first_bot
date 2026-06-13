import asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message

# Сюда вставь свой токен
import os
TOKEN = os.getenv("TOKEN")

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Команда /start
@dp.message(F.text == "/start")
async def start(message: Message):
    await message.answer(f"Привет, {message.from_user.first_name}! 👋\nЯ твой первый бот!")

# Отвечаем на любое сообщение
@dp.message()
async def echo(message: Message):
    await message.answer(f"Ты написал: {message.text}")

async def main():
    print("Бот запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())