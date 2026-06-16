import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from kwork_bot.config import BOT_TOKEN, CHAT_ID, CHECK_INTERVAL, KWORK_URL
from kwork_bot.database import Database
from kwork_bot.parser import KworkParser
import datetime

from aiogram.client.default import DefaultBotProperties

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher()
db = Database()
parser = KworkParser()
scheduler = AsyncIOScheduler()

def format_order_message(order, status="🆕 <b>НОВЫЙ ЗАКАЗ НА KWORK</b>"):
    # Decorative separator
    line = "⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯"
    
    # Budget formatting with emphasis
    budget_main = f"💎 <b>{order['budget']}</b>"
    budget_info = ""
    if order['budget_limit'] != "Не указан":
        budget_info = f"\n╚ <i>Допустимый предел: {order['budget_limit']}</i>"

    return (
        f"{status}\n"
        f"{line}\n\n"
        f"📌 <b>ЗАГОЛОВОК:</b>\n"
        f"<b><u>{order['title']}</u></b>\n\n"
        f"📝 <b>ОПИСАНИЕ:</b>\n"
        f"<blockquote>{order['description']}</blockquote>\n\n"
        f"💰 <b>БЮДЖЕТ:</b>\n"
        f"{budget_main}{budget_info}\n\n"
        f"⚙️ <b>ДЕТАЛИ:</b>\n"
        f"🕒 Осталось: <code>{order['time_left']}</code>\n"
        f"🤝 Откликов: <code>{order['offers_count']}</code>\n\n"
        f"🔗 <a href='{order['url']}'><b>ОТКРЫТЬ ПРОЕКТ НА БИРЖЕ</b></a>\n"
        f"{line}"
    )

async def check_for_updates():
    logger.info("Starting scheduled check...")
    html = await parser.get_page_content(KWORK_URL)
    orders = parser.parse_orders(html)
    
    if not orders:
        logger.warning("No orders found or error during parsing.")
        return

    # Kwork orders are New -> Old (Top -> Bottom).
    # To have them appear in Telegram in chronological order (Oldest first, Newest at the bottom),
    # we process the list in reverse.
    logger.info(f"Found {len(orders)} orders on page. Processing...")

    new_count = 0
    updated_count = 0

    # Collect orders to be sent
    to_send = []
    for order in reversed(orders):
        existing_order = db.get_order(order['id'])
        
        if not existing_order:
            to_send.append((order, "new"))
            new_count += 1
        else:
            changed = False
            # Only track budget changes. Tracking offers_count causes too much spam.
            if (order['budget'] != existing_order[3] or 
                order['budget_limit'] != existing_order[4]):
                changed = True
            
            if changed:
                to_send.append((order, "updated"))
                updated_count += 1

    if to_send:
        for i, (order, type) in enumerate(to_send):
            db.save_order(order)
            status = "🆕 <b>НОВЫЙ ЗАКАЗ НА KWORK</b>" if type == "new" else "🔄 <b>ОБНОВЛЕНО НА KWORK</b>"
            msg = format_order_message(order, status=status)
            try:
                await bot.send_message(CHAT_ID, msg)
                await asyncio.sleep(0.8) 
            except Exception as e:
                logger.error(f"Error sending message: {e}")

        # Batch end marker
        footer = (
            f"✅ <b>Поиск завершен!</b>\n"
            f"✨ Найдено новых: <code>{new_count}</code>\n"
            f"🔄 Обновлено: <code>{updated_count}</code>\n"
            f"⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯"
        )
        await bot.send_message(CHAT_ID, footer)
    else:
        logger.info("No new or updated orders found.")

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "👋 Привет! Я бот для парсинга заказов с Kwork (Разработка и IT).\n\n"
        "🔍 Я проверяю новые заказы каждый час и присылаю уведомления.\n\n"
        "Команды:\n"
        "/check — ручная проверка новых заказов\n"
        "/last — показать последние 5 найденных заказов\n"
        "/settings — текущие настройки\n"
        "/clear — очистить историю заказов"
    )

@dp.message(Command("check"))
async def cmd_check(message: types.Message):
    await message.answer("🔄 Проверяю новые заказы...")
    await check_for_updates()
    await message.answer("✅ Проверка завершена.")

@dp.message(Command("last"))
async def cmd_last(message: types.Message):
    orders = db.get_last_orders(5)
    if not orders:
        await message.answer("📭 В базе пока нет заказов.")
        return
    
    for o in orders:
        # Convert tuple back to dict for formatter
        order_dict = {
            'title': o[1],
            'description': o[2],
            'budget': o[3],
            'budget_limit': o[4],
            'time_left': o[5],
            'offers_count': o[6],
            'url': o[7]
        }
        await message.answer(format_order_message(order_dict, status="📋 Последний найденный заказ"))

@dp.message(Command("settings"))
async def cmd_settings(message: types.Message):
    await message.answer(
        f"⚙️ Текущие настройки:\n\n"
        f"⏱ Интервал проверки: {CHECK_INTERVAL} сек.\n"
        f"🆔 ID получателя: {CHAT_ID}\n"
        f"🔗 URL: {KWORK_URL}"
    )

@dp.message(Command("clear"))
async def cmd_clear(message: types.Message):
    db.clear_history()
    await message.answer("🧹 История заказов очищена.")

from aiogram.types import BotCommand

async def set_commands(bot: Bot):
    commands = [
        BotCommand(command="start", description="Запустить бота и показать справку"),
        BotCommand(command="check", description="Ручная проверка новых заказов"),
        BotCommand(command="last", description="Показать последние 5 заказов из базы"),
        BotCommand(command="settings", description="Показать текущие настройки"),
        BotCommand(command="clear", description="Очистить историю заказов"),
    ]
    await bot.set_my_commands(commands)

async def main():
    # Set command hints in Telegram menu
    await set_commands(bot)
    
    # Run first check on startup
    await check_for_updates()
    
    # Setup scheduler
    scheduler.add_job(check_for_updates, 'interval', seconds=CHECK_INTERVAL)
    scheduler.start()
    
    # Start polling
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped.")
