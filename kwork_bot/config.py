import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL", 3600))
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///kwork_bot.db")

KWORK_URL = "https://kwork.ru/projects?c=11&view=0&sort=new"
