import os
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
import google.generativeai as genai


# Mengambil API Key dari Environment Variables Render
TOKEN = os.getenv("TELEGRAM_TOKEN")
AI_KEY = os.getenv("GEMINI_API_KEY")


# Inisialisasi AI (Menggunakan genai format, bisa untuk gemini)
genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')


bot = Bot(token=TOKEN)
dp = Dispatcher()

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer("Halo! Saya bot AI Anda. Silakan kirim pesan apa saja!")

@dp.message()
async def handle_message(message: types.Message):
    # Mengirim pesan user ke AI
    response = model.generate_content(message.text)
    await message.answer(response.text)


async def main():
    print("Bot sedang berjalan...")
    await dp.start_polling(None)

if __name__ == "__main__":
    asyncio.run(main())
