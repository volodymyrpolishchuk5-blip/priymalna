import os
import asyncio
from aiogram import Bot

async def test():
    token = os.environ.get("BOT_TOKEN")
    if not token:
        print("Error: BOT_TOKEN is missing")
        return
    bot = Bot(token=token)
    try:
        me = await bot.get_me()
        print(f"Success: Bot @{me.username} is active")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(test())
