import os
import asyncio
import threading
import streamlit as st
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
import google.generativeai as genai

# --- KONFIGURASI ---
# Streamlit mengambil Secrets secara otomatis dari st.secrets
TOKEN=st.sec...EN")
GEMINI_KEY=st.sec...EY")

# Konfigurasi Gemini AI
if GEMINI_KEY:
    genai.configure(api_key=GEMINI_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')

# Konfigurasi Bot Telegram
bot = Bot(token=TOKEN) if TOKEN else None
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

# Fungsi untuk menjalankan bot di background agar tidak membekukan website
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

# --- TAMPILAN WEBSITE ---
st.set_page_config(page_title="My AI Bot Status", page_icon="🤖")
st.title("🤖 Bot AI Telegram Status")

if TOKEN and GEMINI_KEY:
    st.success("✅ API Keys terdeteksi! Bot sedang mencoba berjalan di latar belakang.")
    
    # Menjalankan bot di background hanya satu kali
    if 'bot_started' not in st.session_state:
        thread = threading.Thread(target=run_bot, daemon=True)
        thread.start()
        st.session_state['bot_started'] = True
        st.write("🚀 Bot telah dimulai di latar belakang!")
else:
    st.error("❌ API Keys belum diatur di Settings > Secrets!")

st.info("Buka Telegram Anda dan kirim pesan ke bot untuk mencoba!")
