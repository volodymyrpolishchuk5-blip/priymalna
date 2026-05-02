import asyncio
import json
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart, CommandObject, Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.types.web_app_info import WebAppInfo
import database as db
import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
WEBAPP_URL = os.getenv("WEBAPP_URL")

if not TOKEN:
    raise ValueError("Не знайдено BOT_TOKEN у файлі .env!")
if not WEBAPP_URL:
    raise ValueError("Не знайдено WEBAPP_URL у файлі .env!")

bot = Bot(token=TOKEN)
dp = Dispatcher()

@dp.message(CommandStart())
async def start_command(message: types.Message, command: CommandObject):
    args = command.args
    
    if args:
        # Client flow: deeply linked to a specific tenant
        tenant_id = args
        tenant = db.get_tenant_by_id(tenant_id)
        if not tenant:
            await message.answer("❌ Бізнес не знайдено. Перевірте посилання.")
            return
            
        client_url = f"{WEBAPP_URL}?tenant={tenant_id}"
        
        markup = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text=f"💅 Записатися: {tenant[2]}", web_app=WebAppInfo(url=client_url))]
            ],
            resize_keyboard=True
        )
        await message.answer(
            f"👋 Вітаємо у **{tenant[2]}**!\n\n"
            "Натисніть кнопку нижче, щоб обрати послугу та час:",
            reply_markup=markup, parse_mode="Markdown"
        )
    else:
        # Admin flow
        owner_id = message.from_user.id
        tenant = db.get_tenant_by_owner(owner_id)
        
        if tenant:
            tenant_id = tenant[0]
            admin_url = WEBAPP_URL.replace("index.html", f"admin.html?tenant={tenant_id}&admin=1")
            
            bot_info = await bot.get_me()
            bot_username = bot_info.username
            client_link = f"https://t.me/{bot_username}?start={tenant_id}"
            
            markup = ReplyKeyboardMarkup(
                keyboard=[
                    [KeyboardButton(text="🔐 Кабінет адміністратора", web_app=WebAppInfo(url=admin_url))]
                ],
                resize_keyboard=True
            )
            await message.answer(
                f"🏢 **Ваш бізнес:** {tenant[2]}\n\n"
                f"🔗 **Посилання для клієнтів:**\n`{client_link}`\n\n"
                "Надішліть це посилання своїм клієнтам, щоб вони могли записатися. Кнопка 'Кабінет' нижче — тільки для вас.",
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
    
    # Реєструємо тільки якщо користувач ще не має бізнесу
    if not existing:
        business_name = message.text
        if len(business_name) < 3:
            await message.answer("⚠️ Назва бізнесу занадто коротка. Спробуйте ще раз.")
            return
            
        tenant_id = db.create_tenant(owner_id, business_name)
        await message.answer(
            f"✅ Бізнес **{business_name}** успішно зареєстровано!\n\n"
            "Тепер натисніть /start, щоб отримати посилання для клієнтів та увійти в кабінет.",
            parse_mode="Markdown"
        )

@dp.message(Command("register"))
async def register_command(message: types.Message, command: CommandObject):
    business_name = command.args
    if not business_name:
        await message.answer("⚠️ Будь ласка, вкажіть назву бізнесу. Наприклад: `/register Моя Студія`", parse_mode="Markdown")
        return
        
    owner_id = message.from_user.id
    existing = db.get_tenant_by_owner(owner_id)
    if existing:
        await message.answer("❌ Ви вже зареєстрували бізнес! Натисніть /start щоб перейти в кабінет.")
        return
        
    tenant_id = db.create_tenant(owner_id, business_name)
    await message.answer(f"✅ Бізнес **{business_name}** успішно зареєстровано!\n\nНатисніть /start щоб отримати посилання для клієнтів та увійти в кабінет.", parse_mode="Markdown")

@dp.message(F.web_app_data)
async def handle_webapp_data(message: types.Message):
    try:
        data = json.loads(message.web_app_data.data)
        action = data.get("action")
        tenant_id = data.get("tenant_id")
        
        if not tenant_id:
            await message.answer("⚠️ Помилка: tenant_id не вказано.")
            return

        if action == "add_service":
            db.add_service(tenant_id, data.get("name"), data.get("price"), data.get("duration", 60))
            await message.answer(f"✅ Послугу **{data.get('name')}** додано!")

        elif action == "delete_service":
            db.delete_service(data.get("service_id"), tenant_id)
            await message.answer("❌ Послугу видалено.")
            
        elif action == "add_master":
            db.add_master(tenant_id, data.get("name"), data.get("specialty"), data.get("telegram_id"))
            await message.answer(f"✅ Майстра **{data.get('name')}** додано!")

        elif action == "delete_master":
            db.delete_master(data.get("master_id"), tenant_id)
            await message.answer("❌ Майстра видалено.")

        elif action == "complete_booking" or action == "cancel_booking":
            status = "виконано" if action == "complete_booking" else "скасовано"
            db.update_appointment_status(data.get("appt_id"), tenant_id, status)
            await message.answer(f"📋 Запис позначено як {status}.")

        elif action == "new_booking":
            master_id = data.get('master_id')
            appt_id = db.add_appointment(
                tenant_id, master_id, data['name'], data['phone'], 
                data['service'], data['date'], data['time']
            )
            
            client_msg = (
                f"✅ **Запис прийнято!**\n\n"
                f"👤 Клієнт: {data['name']}\n"
                f"📞 Телефон: {data['phone']}\n"
                f"💅 Послуга: {data['service']}\n"
                f"📅 Дата: {data['date']} о {data['time']}"
            )
            await message.answer(client_msg, parse_mode="Markdown")
            
            # Notify owner
            tenant = db.get_tenant_by_id(tenant_id)
            if tenant and tenant[1]:
                owner_id = tenant[1]
                admin_msg = (
                    f"🔔 **Новий запис!**\n\n"
                    f"👤 Клієнт: {data['name']}\n"
                    f"📞 Телефон: {data['phone']}\n"
                    f"💅 Послуга: {data['service']}\n"
                    f"📅 Дата: {data['date']} о {data['time']}"
                )
                try:
                    await bot.send_message(chat_id=owner_id, text=admin_msg, parse_mode="Markdown")
                except Exception as e:
                    logging.error(f"Error sending to admin: {e}")
            
            # Notify master if has telegram_id
            if master_id:
                master = db.get_master_by_id(master_id)
                if master and master[4]: # telegram_id
                    master_tg_id = master[4]
                    master_msg = (
                        f"🔔 **Новий запис до вас!**\n\n"
                        f"👤 Клієнт: {data['name']}\n"
                        f"📞 Телефон: {data['phone']}\n"
                        f"💅 Послуга: {data['service']}\n"
                        f"📅 Дата: {data['date']} о {data['time']}"
                    )
                    try:
                        if str(master_tg_id) != str(owner_id):
                            await bot.send_message(chat_id=master_tg_id, text=master_msg, parse_mode="Markdown")
                    except Exception as e:
                        logging.error(f"Error sending to master: {e}")

    except Exception as e:
        logging.error(f"Error: {e}")
        await message.answer("⚠️ Помилка при обробці даних.")

async def main():
    logging.basicConfig(level=logging.INFO)
    db.init_db()
    print("Бот запущено!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())