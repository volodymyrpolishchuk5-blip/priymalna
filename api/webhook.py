import json
import os
import sys
import logging
import asyncio
from http.server import BaseHTTPRequestHandler

# Fix path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from lib import db

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart, CommandObject
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, WebAppInfo

BOT_TOKEN = os.environ.get("BOT_TOKEN")
WEBAPP_URL = os.environ.get("WEBAPP_URL")

dp = Dispatcher()

@dp.message(CommandStart())
async def start_handler(message: types.Message, command: CommandObject):
    owner_id = message.from_user.id
    args = command.args
    
    if args:
        # Client flow
        tenant_id = args
        tenant = db.get_tenant_by_id(tenant_id)
        if not tenant:
            await message.answer("❌ Бізнес не знайдено.")
            return
        
        url = f"{WEBAPP_URL}/index.html?tenant={tenant_id}"
        markup = ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text=f"📅 Запис: {tenant['business_name']}", web_app=WebAppInfo(url=url))]],
            resize_keyboard=True
        )
        await message.answer(f"Вітаємо у {tenant['business_name']}!", reply_markup=markup)
    else:
        # Owner flow
        tenant = db.get_tenant_by_owner(owner_id)
        if tenant:
            url = f"{WEBAPP_URL}/admin.html?tenant={tenant['id']}&admin=1"
            markup = ReplyKeyboardMarkup(
                keyboard=[[KeyboardButton(text="🔐 Кабінет адміністратора", web_app=WebAppInfo(url=url))]],
                resize_keyboard=True
            )
            await message.answer(f"🏢 Ваш бізнес: {tenant['business_name']}\nКлієнтське посилання: t.me/{(await message.bot.get_me()).username}?start={tenant['id']}", reply_markup=markup)
        else:
            await message.answer("👋 Напишіть назву вашого бізнесу для реєстрації.")

@dp.message(F.text & ~F.text.startswith("/"))
async def reg_handler(message: types.Message):
    owner_id = message.from_user.id
    if not db.get_tenant_by_owner(owner_id):
        db.create_tenant(owner_id, message.text)
        await message.answer(f"✅ Бізнес {message.text} створено! Натисніть /start")

@dp.message(F.web_app_data)
async def web_data_handler(message: types.Message, bot: Bot):
    try:
        data = json.loads(message.web_app_data.data)
        action = data.get("action")
        tenant_id = data.get("tenant_id")
        
        if action == "new_booking":
            # Simplified booking handler for testing
            phone = data["phone"]
            name = data["name"]
            client = db.get_client_by_phone(tenant_id, phone) or {}
            client_id = client.get("id") or db.create_client(tenant_id, name, phone)
            
            db.add_appointment(tenant_id, data.get("master_id"), client_id, name, phone, data["service"], 0, data["date"], data["time"])
            await message.answer(f"✅ Запис {data['date']} {data['time']} прийнято!")
            
            # Notify owner
            tenant = db.get_tenant_by_id(tenant_id)
            if tenant:
                await bot.send_message(tenant["owner_telegram_id"], f"🔔 Новий запис: {name} {data['service']}")
    except Exception as e:
        logging.error(e)
        await message.answer("⚠️ Помилка")

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length)
        
        async def main():
            bot = Bot(token=BOT_TOKEN)
            try:
                update = types.Update.model_validate_json(body)
                await dp.feed_update(bot, update)
            finally:
                await bot.session.close()
        
        try:
            asyncio.run(main())
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"ok")
        except Exception as e:
            import traceback
            err = f"RUNTIME ERROR: {str(e)}\n{traceback.format_exc()}"
            logging.error(err)
            self.send_response(200)
            self.end_headers()
            self.wfile.write(err.encode("utf-8"))

    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"active")
