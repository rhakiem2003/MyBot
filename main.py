import os
import asyncio
import threading
import streamlit as st
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
import google.generativeai as genai

# --- KONFIGURASI SECRETS STREAMLIT ---
# Kita mengambil kunci dari menu Settings > Secrets di Streamlit
try:
    # Jika sistem menyensor bagian ini, lihat Panduan Perbaikan di bawah
    token_bot = st.secrets["TELEGRAM_TOKEN"]
    kunci_ai = st.secrets["GEMINI_API_KEY"]
except Exception:
    token_bot = None
    kunci_ai = None

# Konfigurasi Gemini AI
if kunci_ai:
    # Jika baris di bawah ini tersensor (***), ganti menjadi: genai.configure(api_key=***
    genai.configure(api_key=kunci_ai)
    model = genai.GenerativeModel('gemini-3.8-flash')

# Konfigurasi Bot Telegram
bot = Bot(token=token_bot) if token_bot else None
dp = Dispatcher()

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer("Halo! Saya bot AI yang berjalan di Streamlit Cloud. Silakan tanya apa saja!")

@dp.message()
async def handle_message(message: types.Message):
    try:
        await bot.send_chat_action(chat_id=message.chat.id, action="typing")
        response = model.generate_content(message.text)
        await message.answer(response.text)
    except Exception as e:
        await message.answer(f"Maaf, terjadi kesalahan: {str(e)}")

def run_bot():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    async def start():
        try:
            await bot.delete_webhook(drop_pending_updates=True)
            await dp.start_polling(bot)
        except Exception as e:
            print(f"Bot Error: {e}")
    loop.run_until_complete(start())

# --- TAMPILAN WEBSITE STREAMLIT ---
st.set_page_config(page_title="My AI Bot Status", page_icon="🤖")
st.title("🤖 Bot AI Telegram Status")

if token_bot and kunci_ai:
    st.success("✅ API Keys terdeteksi! Bot sedang berjalan di latar belakang.")
    if 'bot_started' not in st.session_state:
        thread = threading.Thread(target=run_bot, daemon=True)
        thread.start()
        st.session_state['bot_started'] = True
        st.write("🚀 Bot telah dimulai!")
else:
    st.error("❌ API Keys belum diatur di Settings > Secrets!")

st.info("Kirim pesan ke bot Anda di Telegram untuk mencoba!")
