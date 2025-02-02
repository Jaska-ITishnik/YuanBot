import os
from dataclasses import dataclass, asdict

from dotenv import load_dotenv

load_dotenv()


@dataclass
class BaseConfig:
    def asdict(self):
        return asdict(self)


@dataclass
class DatabaseConfig(BaseConfig):
    """Database connection variables"""

    NAME: str = os.getenv('DB_NAME')
    USER: str = os.getenv('DB_USER')
    PASS: str = os.getenv('DB_PASS')
    HOST: str = os.getenv('DB_HOST')
    PORT: str = os.getenv('DB_PORT')

    @property
    def db_url(self):
        return f"postgresql+asyncpg://{self.USER}:{self.PASS}@{self.HOST}:{self.PORT}/{self.NAME}"


@dataclass
class BotConfig(BaseConfig):
    """Bot configuration"""
    BOT_TOKEN: str = os.getenv('BOT_TOKEN')
    ADMIN_LIST: str = os.getenv('ADMIN_LIST')
    CHAT_IDES_LIST: str = os.getenv('CHAT_IDES_LIST')
    TELEGRAM_USERNAME: str = os.getenv('TELEGRAM_USERNAME')
    MIN_AMOUNT_YUAN: int = int(os.getenv('MIN_AMOUNT_YUAN'))
    MIN_AMOUNT_UZS: int = int(os.getenv('MIN_AMOUNT_UZS'))
    ADMIN_HUMO_CARD_NUMBER: str = os.getenv('ADMIN_HUMO_CARD_NUMBER')
    ADMIN_UZCARD_CARD_NUMBER: str = os.getenv('ADMIN_UZCARD_CARD_NUMBER')
    CARGO_DB_PASSWORD: int = os.getenv("CARGO_DB_PASSWORD")
    CARGO_DB_HOST: str = os.getenv("CARGO_DB_HOST")
    CARGO_DB_PORT: int = os.getenv("CARGO_DB_PORT")
    CARGO_DB_NAME: str = os.getenv("CARGO_DB_NAME")
    # WEB_SERVER_HOST: str = os.getenv('WEB_SERVER_HOST')
    # WEB_SERVER_PORT: int = int(os.getenv('WEB_SERVER_PORT', 8080))
    # WEBHOOK_PATH = "/webhook"
    WEBHOOK_SECRET = os.getenv('WEBHOOK_SECRET')
    # BASE_WEBHOOK_URL = os.getenv('BASE_WEBHOOK_URL')


@dataclass
class WebConfig(BaseConfig):
    """Web configuration"""
    SECRET_KEY: str = os.getenv('SECRET_KEY')
    USERNAME: str = os.getenv('ADMIN_USERNAME')
    PASSWD: str = os.getenv('ADMIN_PASSWORD')


@dataclass
class Configuration:
    """All in one configuration's class"""
    db = DatabaseConfig()
    bot = BotConfig()
    web = WebConfig()


conf = Configuration()

# import logging
# import sys
#
# from aiogram import Dispatcher, Bot
# from aiogram.client.default import DefaultBotProperties
# from aiogram.enums import ParseMode
# from aiogram.types import BotCommand
# from aiogram.utils.i18n import I18n, FSMI18nMiddleware
# from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
# from aiohttp import web
#
# from bot.config import TOKEN
# from bot.utils.starter import router
# from db import database
#
# dp = Dispatcher()
# WEB_SERVER_HOST = "127.0.0.1"
# WEB_SERVER_PORT = 8080  # Changed from 80 to 8080
# WEBHOOK_PATH = "/webhook"
# BASE_WEBHOOK_URL = "https://jasur.fil.uz"
#
#
# async def on_startup(bot: Bot):
#     logging.info("Starting up...")
#     # Initialize database
#     await database.create_all()
#
#     # Set bot commands
#     command_list = [
#         BotCommand(command='start', description='Start the bot 🪡'),
#         BotCommand(command='help', description='Help 🔓'),
#         BotCommand(command='language', description='Change language 🔄')
#     ]
#     await bot.set_my_commands(command_list)
#
#     # Check current webhook status
#     try:
#         current_webhook = await bot.get_webhook_info()
#         expected_webhook_url = f"{BASE_WEBHOOK_URL}{WEBHOOK_PATH}"
#
#         if current_webhook.url != expected_webhook_url:
#             logging.info("Setting webhook...")
#             await bot.set_webhook(expected_webhook_url)
#         else:
#             logging.info("Webhook already set.")
#     except Exception as e:
#         logging.error(f"Failed to set webhook: {e}")
#
#
# async def on_shutdown(bot: Bot):
#     await database.drop_all()
#     await bot.delete_my_commands()
#
#
# def main() -> None:
#     i18n = I18n(path="locales")
#     dp.update.outer_middleware.register(FSMI18nMiddleware(i18n))
#     dp.startup.register(on_startup)
#     dp.shutdown.register(on_shutdown)
#
#     dp.include_router(router)
#     dp.startup.register(on_startup)
#     bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
#     app = web.Application()
#
#     webhook_requests_handler = SimpleRequestHandler(
#         dispatcher=dp,
#         bot=bot,
#     )
#     webhook_requests_handler.register(app, path=WEBHOOK_PATH)
#
#     setup_application(app, dp, bot=bot)
#
#     web.run_app(app, host=WEB_SERVER_HOST, port=WEB_SERVER_PORT)
#
#
# if __name__ == "__main__":
#     logging.basicConfig(level=logging.INFO, stream=sys.stdout)
#     main()
