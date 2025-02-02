import asyncio
import json
import logging
import os
import sys

import asyncpg
import uvicorn
from aiogram import BaseMiddleware, Bot
from aiogram import Dispatcher, F
from aiogram.enums import ChatMemberStatus
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.redis import RedisStorage
from aiogram.types import BotCommand, BotCommandScopeChat
from aiogram.types import Message, InlineKeyboardButton, CallbackQuery
from aiogram.utils.i18n import FSMI18nMiddleware
from aiogram.utils.i18n import I18n
from aiogram.utils.i18n import gettext as _
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web
from dotenv import load_dotenv
from redis.asyncio import Redis

from bot.handlers.callback_handlers import user_callback_router
from bot.handlers.message_handler import user_message_router
from config import conf
from db import database
from utils import usd_uzs, usd_yuan
from web import app

load_dotenv('.env')

TOKEN = os.getenv('BOT_TOKEN')

redis = Redis()
storage = RedisStorage(redis=redis)
dp = Dispatcher(storage=storage)

CHAT_IDES_LIST = conf.bot.CHAT_IDES_LIST.strip().split()
CARGO_DB_PASSWORD = conf.bot.CARGO_DB_PASSWORD
CARGO_DB_HOST = conf.bot.CARGO_DB_HOST
CARGO_DB_PORT = conf.bot.CARGO_DB_PORT
CARGO_DB_NAME = conf.bot.CARGO_DB_NAME
ADMIN_LIST = conf.bot.ADMIN_LIST.strip().split()

WEB_SERVER_HOST = "127.0.0.1"
WEB_SERVER_PORT = 8080  # Changed from 80 to 8080
WEBHOOK_PATH = "/webhook"
BASE_WEBHOOK_URL = "https://yuanbot.jaska-itishnik.uz"


# BASE_WEBHOOK_URL = "https://f4a9-178-218-201-17.ngrok-free.app"


async def check_old_bot_membership(tg_id: int) -> bool:
    conn = await asyncpg.connect(
        f"postgresql://postgres:{CARGO_DB_PASSWORD}@{CARGO_DB_HOST}:{CARGO_DB_PORT}/{CARGO_DB_NAME}"
    )
    result = await conn.fetchrow("SELECT * FROM users WHERE tg_id = $1", tg_id)
    await conn.close()
    return bool(result)


class JoinChannelMiddleware(BaseMiddleware):
    async def __call__(self, handler, event: Message, data):
        if event.callback_query and event.callback_query.data == 'check_if_subscribed' or event.message:

            if event.message:
                user = event.message.from_user
            else:
                user = event.callback_query.from_user

            bot: Bot = data['bot']
            state: FSMContext = data['state']
            user_data = await state.get_data()

            if "old_bot_member" not in user_data.keys():
                old_bot_member = await check_old_bot_membership(user.id)
                await state.update_data(old_bot_member=old_bot_member)
            else:
                old_bot_member = user_data["old_bot_member"]

            unsubscribers = []
            for channel_id in CHAT_IDES_LIST:
                member = await bot.get_chat_member(int(channel_id), user.id)
                if member.status == ChatMemberStatus.LEFT:
                    unsubscribers.append(channel_id)

            if unsubscribers or old_bot_member:
                ikb = InlineKeyboardBuilder()
                for channel_id in unsubscribers:
                    channel = json.loads((await bot.get_chat(channel_id)).model_dump_json())
                    ikb.add(InlineKeyboardButton(
                        text=channel['title'],
                        url=channel['invite_link']
                    ))
                if old_bot_member:
                    ikb.add(InlineKeyboardButton(text="FagCargoBot",
                                                 url="https://t.me/FadCargoBot"))
                ikb.add(InlineKeyboardButton(text=_("Tekshirish✅"), callback_data="check_if_subscribed"))
                ikb.adjust(2, 1)
                if event.callback_query:
                    try:
                        await event.callback_query.message.edit_reply_markup(reply_markup=ikb.as_markup())
                    except TelegramBadRequest:
                        await event.callback_query.answer(_("Hali a'zo bo'lmadingiz🤨"), show_alert=True)
                else:
                    await event.message.answer(_("Oldin kanallarga a'zo bo'ling👇"), reply_markup=ikb.as_markup())
                return
            else:
                if event.callback_query:
                    await event.callback_query.message.edit_text(_('Muvofaqiyatliy☺ qayta /start ni bosing'))
        return await handler(event, data)


@dp.callback_query(F.text == "check_if_subscribed")
async def handle_check_if_subscribed(callback_query: CallbackQuery):
    await callback_query.answer("Tekshirish bosildi ✅")


async def start_uvicorn():
    """Runs the Starlette Admin panel in a separate task."""
    config = uvicorn.Config(app, host="0.0.0.0", port=8080, log_level="info")
    server = uvicorn.Server(config)
    await server.serve()


async def on_startup(bot: Bot):
    usd_uzs()
    usd_yuan()

    i18n = I18n(path='locales', default_locale='uz')
    _ = i18n.gettext
    for ADMIN_CHAT_ID in ADMIN_LIST:
        admin_commands = [
            BotCommand(command='start', description=_('🛫Botni ishga tushirish'))
        ]
        await bot.set_my_commands(commands=admin_commands, scope=BotCommandScopeChat(chat_id=int(ADMIN_CHAT_ID)))

    await database.create_all()

    try:
        current_webhook = await bot.get_webhook_info()
        expected_webhook_url = f"{BASE_WEBHOOK_URL}{WEBHOOK_PATH}"

        if current_webhook.url != expected_webhook_url:
            logging.info("Setting webhook...")
            await bot.set_webhook(expected_webhook_url)
        else:
            logging.info("Webhook already set.")
    except Exception as e:
        logging.error(f"Failed to set webhook: {e}")

    # ✅ Start Uvicorn in the background
    asyncio.create_task(start_uvicorn())


async def on_shutdown(bot: Bot):
    # await database.drop_all()
    pass


def main() -> None:
    i18 = I18n(path='locales', default_locale='uz', domain="messages")
    dp.update.outer_middleware.register(FSMI18nMiddleware(i18))
    dp.update.outer_middleware(JoinChannelMiddleware())
    dp.include_routers(user_message_router, user_callback_router)
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)
    bot = Bot(TOKEN)
    app = web.Application()

    webhook_requests_handler = SimpleRequestHandler(
        dispatcher=dp,
        bot=bot,
    )
    webhook_requests_handler.register(app, path=WEBHOOK_PATH)

    setup_application(app, dp, bot=bot)

    web.run_app(app, host=WEB_SERVER_HOST, port=WEB_SERVER_PORT)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    main()
