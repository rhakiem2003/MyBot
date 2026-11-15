import os
import asyncio
import threading
import streamlit as st
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
import google.generativeai as genai


def get_secret(name: str):
    value = os.getenv(name)
    if value:
        return value

    try:
        if hasattr(st, "secrets") and name in st.secrets:
            v = st.secrets[name]
            if v:
                return str(v)
    except Exception:
        pass

    return None


TELEGRAM_TOKEN = get_secret("TELEGRAM_TOKEN")
GEMINI_API_KEY = get_secret("GEMINI_API_KEY")

model = None
if GEMINI_API_KEY:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel("gemini-1.5-flash")
    except Exception as exc:
        print(f"Gemini config error: {exc}")

bot = Bot(token=TELEGRAM_TOKEN) if TELEGRAM_TOKEN else None
dp = Dispatcher()


def safe_text(value: str | None, max_len: int = 2000) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    if len(text) > max_len:
        text = text[:max_len]
    return text


@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer("Halo! Saya bot AI yang aman. Kirim pertanyaan Anda.")


@dp.message()
async def handle_message(message: types.Message):
    if bot is None or model is None:
        return

    if message.text is None:
        return

    prompt = safe_text(message.text)
    if not prompt:
        return

    try:
        await bot.send_chat_action(chat_id=message.chat.id, action="typing")
        response = model.generate_content(prompt)
        answer = getattr(response, "text", "")
        if not answer:
            answer = "Saya tidak bisa menjawab saat ini."
        await message.answer(safe_text(answer))
    except Exception as exc:
        print(f"Bot runtime error: {exc}")
        await message.answer("Maaf, terjadi kesalahan server. Silakan coba lagi nanti.")


def run_bot():
    if bot is None:
        return

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    async def start():
        try:
            await bot.delete_webhook(drop_pending_updates=True)
            await dp.start_polling(bot, allowed_updates=["message"])
        except Exception as exc:
            print(f"Polling error: {exc}")

    loop.run_until_complete(start())


st.set_page_config(page_title="My AI Bot", page_icon="🤖")
st.title("🤖 Bot AI Telegram")

if TELEGRAM_TOKEN and GEMINI_API_KEY and model:
    st.success("✅ Kunci terdeteksi. Bot siap dijalankan.")
    if "bot_started" not in st.session_state:
        thread = threading.Thread(target=run_bot, daemon=True)
        thread.start()
        st.session_state["bot_started"] = True
        st.write("🚀 Bot telah dimulai!")
else:
    st.warning("⚠️ Token Telegram dan/atau API key Gemini belum lengkap. Isi di Streamlit Secrets.")

st.info("Kirim pesan ke bot Anda di Telegram untuk mencoba.")
