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
            value = st.secrets[name]
            if value:
                return str(value)
    except Exception:
        pass

    return None


TELEGRAM_TOKEN = get_secret("TELEGRAM_TOKEN")
GEMINI_API_KEY = get_secret("GEMINI_API_KEY")


def get_model_names() -> list[str]:
    """Return the primary Gemini model followed by configured fallback models."""
    primary = get_secret("GEMINI_MODEL") or "gemini-1.5-flash"
    configured_fallbacks = get_secret("GEMINI_FALLBACK_MODELS") or "gemini-1.5-pro"
    names = [primary.strip()]
    names.extend(name.strip() for name in configured_fallbacks.split(","))
    # Keep order while removing blanks and duplicates.
    return list(dict.fromkeys(name for name in names if name))


MODEL_NAMES = get_model_names()
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)


def is_model_unavailable(error: Exception) -> bool:
    """Only fall back for model lookup/availability errors, not bad credentials or quota."""
    response = getattr(error, "response", None)
    status_code = getattr(error, "status_code", None) or getattr(response, "status_code", None)
    if status_code == 404:
        return True

    message = str(error).lower()
    return any(
        phrase in message
        for phrase in (
            "model not found",
            "model is not found",
            "not found for api version",
            "model is not supported",
            "model not supported",
        )
    )


def generate_with_fallback(prompt: str):
    """Try configured models in order, falling back only when a model is unavailable."""
    last_error = None
    for model_name in MODEL_NAMES:
        try:
            model = genai.GenerativeModel(model_name)
            return model.generate_content(prompt)
        except Exception as exc:
            if not is_model_unavailable(exc):
                raise
            last_error = exc
            print(f"Gemini model '{model_name}' is unavailable; trying the next fallback.")

    raise RuntimeError(
        "No configured Gemini model is available. Set GEMINI_MODEL and/or "
        "GEMINI_FALLBACK_MODELS to model names enabled for your API key."
    ) from last_error


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
    if bot is None or not GEMINI_API_KEY:
        return

    if message.text is None:
        return

    prompt = safe_text(message.text)
    if not prompt:
        return

    try:
        await bot.send_chat_action(chat_id=message.chat.id, action="typing")
        response = generate_with_fallback(prompt)
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

if TELEGRAM_TOKEN and GEMINI_API_KEY:
    st.success("✅ Kunci terdeteksi. Bot siap dijalankan.")
    st.caption(f"Model utama: {MODEL_NAMES[0]} · fallback tersedia: {len(MODEL_NAMES) - 1}")
    if "bot_started" not in st.session_state:
        thread = threading.Thread(target=run_bot, daemon=True)
        thread.start()
        st.session_state["bot_started"] = True
        st.write("🚀 Bot telah dimulai!")
else:
    st.warning("⚠️ Token Telegram dan/atau API key Gemini belum lengkap. Isi di Streamlit Secrets.")

st.info("Kirim pesan ke bot Anda di Telegram untuk mencoba.")
