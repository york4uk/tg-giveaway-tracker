import asyncio
import os
import re
from datetime import datetime
from pyrogram import Client, filters
from pyrogram.types import Message

# ⚙️ Получаем переменные окружения от Railway (через Secrets)
API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")
OWNER_ID = int(os.getenv("OWNER_ID"))
SESSION_NAME = os.getenv("SESSION_NAME", "my_account")  # по умолчанию
SESSION_STRING = os.getenv("SESSION_STRING")  # для авторизации без ввода номера

# 🔑 Ключевые слова для поиска розыгрышей
DEFAULT_KEYWORDS = {
    "розыгрыш", "конкурс", "giveaway", "выиграй", "подарок", "разыгрываем",
    "участие", "победитель", "репост", "подписка", "дарим", "бесплатно",
    "акция", "приз", "лот", "лотерея", "промо", "промокод"
}

# 🚫 Игнорируемые чаты (по ID)
IGNORED_CHATS = set()

# 🧩 Пользовательские ключевые слова (можно расширять командами)
USER_KEYWORDS = set(DEFAULT_KEYWORDS)

# 🤖 Инициализация клиента Pyrogram
if SESSION_STRING:
    app = Client(SESSION_NAME, api_id=API_ID, api_hash=API_HASH, session_string=SESSION_STRING)
else:
    app = Client(SESSION_NAME, api_id=API_ID, api_hash=API_HASH)

# 🔍 Функция: проверить, содержит ли текст признаки розыгрыша
def is_giveaway(text: str) -> bool:
    if not text:
        return False
    text_lower = text.lower()
    for keyword in USER_KEYWORDS:
        if keyword in text_lower:
            return True
    return False

# 🔗 Функция: получить кликабельную ссылку на сообщение
def get_message_link(chat_id: int, message_id: int) -> str:
    try:
        chat = app.get_chat(chat_id)
        if chat.username:
            return f"https://t.me/{chat.username}/{message_id}"
        else:
            return f"tg://openmessage?chat_id={chat_id}&message_id={message_id}"
    except Exception:
        return f"tg://openmessage?chat_id={chat_id}&message_id={message_id}"

# 👂 Обработчик всех текстовых сообщений в группах
@app.on_message(filters.text & filters.group)
async def monitor_chats(client: Client, message: Message):
    chat_id = message.chat.id

    # Игнорировать, если чат в чёрном списке
    if chat_id in IGNORED_CHATS:
        return

    # Проверить, пост ли это с розыгрышем
    if is_giveaway(message.text or ""):
        chat_title = message.chat.title or "Без названия"
        message_link = get_message_link(chat_id, message.id)
        detected_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 📩 Формируем уведомление
        alert_text = (
            f"🎁 **Обнаружен розыгрыш!**\n\n"
            f"**Чат:** {chat_title} (`{chat_id}`)\n"
            f"**Дата/время:** {detected_time}\n"
            f"**Ссылка:** {message_link}\n\n"
            f"**Текст сообщения:**\n{message.text[:1000]}"
        )

        try:
            await client.send_message(OWNER_ID, alert_text, disable_web_page_preview=True)
            print(f"[+] Уведомление отправлено о розыгрыше в {chat_title}")
        except Exception as e:
            print(f"[-] Ошибка отправки уведомления: {e}")

# ➕ Команда: добавить ключевое слово
@app.on_message(filters.command("add_keyword", prefixes=".") & filters.user(OWNER_ID))
async def add_keyword(client: Client, message: Message):
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.reply("❌ Использование: `.add_keyword <слово>`")
        return

    keyword = args[1].strip().lower()
    if keyword in USER_KEYWORDS:
        await message.reply(f"⚠️ Слово `{keyword}` уже в списке.")
        return

    USER_KEYWORDS.add(keyword)
    await message.reply(f"✅ Ключевое слово `{keyword}` добавлено.")

# ➖ Команда: удалить ключевое слово
@app.on_message(filters.command("remove_keyword", prefixes=".") & filters.user(OWNER_ID))
async def remove_keyword(client: Client, message: Message):
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.reply("❌ Использование: `.remove_keyword <слово>`")
        return

    keyword = args[1].strip().lower()
    if keyword not in USER_KEYWORDS:
        await message.reply(f"⚠️ Слово `{keyword}` не найдено в списке.")
        return

    USER_KEYWORDS.remove(keyword)
    await message.reply(f"✅ Ключевое слово `{keyword}` удалено.")

# 📋 Команда: показать все ключевые слова
@app.on_message(filters.command("list_keywords", prefixes=".") & filters.user(OWNER_ID))
async def list_keywords(client: Client, message: Message):
    keywords = "\n".join(sorted(USER_KEYWORDS))
    await message.reply(f"📋 **Текущие ключевые слова:**\n```\n{keywords}\n```")

# 🚫 Команда: игнорировать чат (по ID или username, или ответом)
@app.on_message(filters.command("ignore_chat", prefixes=".") & filters.user(OWNER_ID))
async def ignore_chat(client: Client, message: Message):
    if message.reply_to_message:
        chat_id = message.reply_to_message.chat.id
    else:
        args = message.text.split(maxsplit=1)
        if len(args) < 2:
            await message.reply("❌ Использование: `.ignore_chat <@username или ID>` или ответом на сообщение")
            return
        target = args[1].strip()
        try:
            chat = await client.get_chat(target)
            chat_id = chat.id
        except Exception as e:
            await message.reply(f"❌ Не удалось найти чат: {e}")
            return

    IGNORED_CHATS.add(chat_id)
    await message.reply(f"✅ Чат `{chat_id}` добавлен в игнор-лист.")

# 📋 Команда: показать игнорируемые чаты
@app.on_message(filters.command("list_ignored", prefixes=".") & filters.user(OWNER_ID))
async def list_ignored(client: Client, message: Message):
    if not IGNORED_CHATS:
        await message.reply("📋 Игнор-лист пуст.")
        return

    ignored_list = "\n".join(map(str, IGNORED_CHATS))
    await message.reply(f"📋 **Игнорируемые чаты (ID):**\n```\n{ignored_list}\n```")

# ✅ Команда: убрать чат из игнора
@app.on_message(filters.command("unignore_chat", prefixes=".") & filters.user(OWNER_ID))
async def unignore_chat(client: Client, message: Message):
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.reply("❌ Использование: `.unignore_chat <chat_id>`")
        return

    try:
        chat_id = int(args[1].strip())
    except ValueError:
        await message.reply("❌ Неверный ID чата.")
        return

    if chat_id not in IGNORED_CHATS:
        await message.reply(f"⚠️ Чат `{chat_id}` не в игнор-листе.")
        return

    IGNORED_CHATS.remove(chat_id)
    await message.reply(f"✅ Чат `{chat_id}` удалён из игнор-листа.")

# ▶️ Запуск бота
if __name__ == "__main__":
    print("🚀 Giveaway Tracker запускается...")
    app.start()  # Запускаем клиент вручную, чтобы отправить сообщение
    try:
        app.send_message(OWNER_ID, "✅ Бот успешно запущен и готов отслеживать розыгрыши!")
        print("[TEST] ✅ Стартовое сообщение отправлено.")
    except Exception as e:
        print(f"[TEST] ❌ Ошибка отправки стартового сообщения: {e}")
    app.run()  # Теперь запускаем основной цикл
