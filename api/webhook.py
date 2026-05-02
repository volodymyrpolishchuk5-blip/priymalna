import json
import os
import sys
import logging

# Add project root to path so we can import lib.db
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from lib import db

from http.server import BaseHTTPRequestHandler
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart, CommandObject, Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, WebAppInfo
from aiogram.webhook.aiohttp_server import SimpleRequestHandler
import asyncio

BOT_TOKEN = os.environ.get("BOT_TOKEN")
WEBAPP_URL = os.environ.get("WEBAPP_URL")  # e.g. https://your-app.vercel.app

# Remove global bot initialization
dp = Dispatcher()

# ===================== HANDLERS =====================

@dp.message(CommandStart())
async def start_command(message: types.Message, command: CommandObject, bot: Bot):
    args = command.args
    if args:
        # Client flow: deep-linked to a specific tenant
        tenant_id = args
        tenant = db.get_tenant_by_id(tenant_id)
        if not tenant:
            await message.answer("❌ Бізнес не знайдено. Перевірте посилання.")
            return
        client_url = f"{WEBAPP_URL}/index.html?tenant={tenant_id}"
        markup = ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(
                text=f"📅 Записатися: {tenant['business_name']}",
                web_app=WebAppInfo(url=client_url)
            )]],
            resize_keyboard=True
        )
        await message.answer(
            f"👋 Вітаємо у **{tenant['business_name']}**!\n\n"
            "Натисніть кнопку нижче, щоб обрати послугу та час:",
            reply_markup=markup, parse_mode="Markdown"
        )
    else:
        # Owner flow
        owner_id = message.from_user.id
        tenant = db.get_tenant_by_owner(owner_id)
        if tenant:
            tenant_id = tenant["id"]
            admin_url = f"{WEBAPP_URL}/admin.html?tenant={tenant_id}&admin=1"
            bot_info = await bot.get_me()
            client_link = f"https://t.me/{bot_info.username}?start={tenant_id}"
            markup = ReplyKeyboardMarkup(
                keyboard=[[KeyboardButton(
                    text="🔐 Кабінет адміністратора",
                    web_app=WebAppInfo(url=admin_url)
                )]],
                resize_keyboard=True
            )
            await message.answer(
                f"🏢 **Ваш бізнес:** {tenant['business_name']}\n\n"
                f"🔗 **Посилання для клієнтів:**\n`{client_link}`\n\n"
                "Надішліть це посилання своїм клієнтам, щоб вони могли записатися.",
                reply_markup=markup, parse_mode="Markdown"
            )
        else:
            await message.answer(
                "👋 Вітаємо! Ви можете створити власний кабінет для записів клієнтів.\n\n"
                "Щоб зареєструвати бізнес, просто **напишіть його назву** у цей чат.\n"
                "Наприклад: `Студія краси Beauty`",
                parse_mode="Markdown"
            )

@dp.message(F.text & ~F.text.startswith("/"))
async def handle_registration(message: types.Message):
    owner_id = message.from_user.id
    existing = db.get_tenant_by_owner(owner_id)
    if not existing:
        business_name = message.text
        if len(business_name) < 3:
            await message.answer("⚠️ Назва бізнесу занадто коротка. Спробуйте ще раз.")
            return
        db.create_tenant(owner_id, business_name)
        await message.answer(
            f"✅ Бізнес **{business_name}** успішно зареєстровано!\n\n"
            "Тепер натисніть /start, щоб отримати посилання для клієнтів та увійти в кабінет.",
            parse_mode="Markdown"
        )

@dp.message(F.web_app_data)
async def handle_webapp_data(message: types.Message, bot: Bot):
    try:
        data = json.loads(message.web_app_data.data)
        action = data.get("action")
        tenant_id = data.get("tenant_id")

        if not tenant_id:
            await message.answer("⚠️ Помилка: tenant_id не вказано.")
            return

        if action == "add_service":
            db.add_service(tenant_id, data.get("name"), int(data.get("price", 0)), int(data.get("duration", 60)))
            await message.answer(f"✅ Послугу **{data.get('name')}** додано!", parse_mode="Markdown")

        elif action == "delete_service":
            db.delete_service(int(data.get("service_id")), tenant_id)
            await message.answer("❌ Послугу видалено.")

        elif action == "add_master":
            db.add_master(
                tenant_id, 
                data.get("name"), 
                data.get("specialty"), 
                data.get("telegram_id"),
                int(data.get("commission_rate", 50))
            )
            await message.answer(f"✅ Майстра **{data.get('name')}** додано!", parse_mode="Markdown")

        elif action == "delete_master":
            db.delete_master(int(data.get("master_id")), tenant_id)
            await message.answer("❌ Майстра видалено.")

        elif action in ("complete_booking", "cancel_booking"):
            status = "виконано" if action == "complete_booking" else "скасовано"
            db.update_appointment_status(int(data.get("appt_id")), tenant_id, status)
            await message.answer(f"📋 Запис позначено як {status}.")

        elif action == "new_booking":
            master_id = data.get("master_id")
            phone = data["phone"]
            name = data["name"]
            
            # Find or create client
            client = db.get_client_by_phone(tenant_id, phone)
            if client:
                client_id = client["id"]
            else:
                client_id = db.create_client(tenant_id, name, phone)

            # Get service price for snapshot
            service_name = data["service"]
            services = db.get_services_by_tenant(tenant_id)
            price = 0
            for s in services:
                if s["name"] == service_name:
                    price = s["price"]
                    break

            appt_id = db.add_appointment(
                tenant_id, int(master_id) if master_id else None, client_id,
                name, phone, service_name, price, data["date"], data["time"]
            )
            await message.answer(
                f"✅ **Запис прийнято!**\n\n"
                f"👤 Клієнт: {data['name']}\n"
                f"📞 Телефон: {data['phone']}\n"
                f"💅 Послуга: {data['service']}\n"
                f"📅 Дата: {data['date']} о {data['time']}",
                parse_mode="Markdown"
            )
            # Notify owner
            tenant = db.get_tenant_by_id(tenant_id)
            if tenant:
                owner_msg = (
                    f"🔔 **Новий запис!**\n\n"
                    f"👤 Клієнт: {data['name']}\n"
                    f"📞 Телефон: {data['phone']}\n"
                    f"💅 Послуга: {data['service']}\n"
                    f"📅 Дата: {data['date']} о {data['time']}"
                )
                try:
                    await bot.send_message(chat_id=tenant["owner_telegram_id"], text=owner_msg, parse_mode="Markdown")
                except Exception as e:
                    logging.error(f"Error notifying owner: {e}")
            # Notify master
            if master_id:
                master = db.get_master_by_id(int(master_id))
                if master and master.get("telegram_id"):
                    master_tg = master["telegram_id"]
                    if str(master_tg) != str(tenant["owner_telegram_id"]):
                        try:
                            await bot.send_message(
                                chat_id=master_tg,
                                text=f"🔔 **Новий запис до вас!**\n\n"
                                     f"👤 {data['name']} ({data['phone']})\n"
                                     f"💅 {data['service']}\n"
                                     f"📅 {data['date']} о {data['time']}",
                                parse_mode="Markdown"
                            )
                        except Exception as e:
                            logging.error(f"Error notifying master: {e}")

    except Exception as e:
        logging.error(f"Webhook handler error: {e}")
        await message.answer("⚠️ Помилка при обробці даних.")

# ===================== VERCEL HANDLER =====================

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length)

            async def process():
                if not BOT_TOKEN:
                    logging.error("BOT_TOKEN is missing!")
                    return
                # Initialize bot inside the current event loop
                bot = Bot(token=BOT_TOKEN)
                try:
                    update = types.Update.model_validate_json(body)
                    await dp.feed_update(bot=bot, update=update)
                except Exception as e:
                    logging.error(f"Error feeding update: {e}")
                    raise e
                finally:
                    await bot.session.close()

            asyncio.run(process())
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"ok")
        except Exception as e:
            import traceback
            err_msg = f"Webhook Error: {str(e)}\n{traceback.format_exc()}"
            logging.error(err_msg)
            self.send_response(200) # Still return 200 to Telegram to stop retries, but we logged it
            self.end_headers()
            self.wfile.write(err_msg.encode("utf-8"))

    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Webhook is active")
