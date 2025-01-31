import asyncio
import json
import logging
import os
import sys

import asyncpg
from aiogram import Bot, Dispatcher, F
from aiogram.enums import ChatMemberStatus
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.storage.redis import RedisStorage
from aiogram.utils.i18n import FSMI18nMiddleware, I18n
from aiogram.utils.i18n import gettext as _
from aiogram.utils.keyboard import InlineKeyboardBuilder
from dotenv import load_dotenv
from redis.asyncio import Redis

from bot.bot_commands import on_startup, on_shutdown
from bot.handlers.callback_handlers import user_callback_router
from bot.handlers.message_handler import user_message_router
from config import conf

load_dotenv('.env')

TOKEN = os.getenv('BOT_TOKEN')

redis = Redis()
storage = RedisStorage(redis=redis)
dp = Dispatcher(storage=storage)

from aiogram import BaseMiddleware
from aiogram.types import Message, InlineKeyboardButton, CallbackQuery

CHAT_IDES_LIST = conf.bot.CHAT_IDES_LIST.strip().split()
CARGO_DB_PASSWORD = conf.bot.CARGO_DB_PASSWORD
CARGO_DB_HOST = conf.bot.CARGO_DB_HOST
CARGO_DB_PORT = conf.bot.CARGO_DB_PORT
CARGO_DB_NAME = conf.bot.CARGO_DB_NAME


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
            unsubscribers = []
            for channel_id in CHAT_IDES_LIST:
                member = await bot.get_chat_member(int(channel_id), user.id)
                if member.status == ChatMemberStatus.LEFT:
                    unsubscribers.append(channel_id)
            expression = not (event.message and (
                await check_old_bot_membership(
                    event.message.from_user.id)) or event.callback_query and await check_old_bot_membership(
                event.callback_query.from_user.id))
            if unsubscribers or expression:
                ikb = InlineKeyboardBuilder()
                for channel_id in unsubscribers:
                    channel = json.loads((await bot.get_chat(channel_id)).model_dump_json())
                    ikb.add(InlineKeyboardButton(
                        text=channel['title'],
                        url=channel['invite_link']
                    ))
                ikb.add(InlineKeyboardButton(text="FagCargoBot",
                                             url="https://t.me/FadCargoBot"))
                ikb.add(InlineKeyboardButton(text=_("Tekshirish✅"), callback_data="check_if_subscribed"))
                ikb.adjust(2, 1)
                if event.callback_query:
                    try:
                        await event.callback_query.message.edit_reply_markup(reply_markup=ikb.as_markup())
                    except TelegramBadRequest as e:
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


async def main() -> None:
    bot = Bot(token=TOKEN)
    i18 = I18n(path='locales', default_locale='uz', domain="messages")
    dp.update.outer_middleware.register(FSMI18nMiddleware(i18))
    dp.update.outer_middleware(JoinChannelMiddleware())
    dp.include_routers(user_message_router, user_callback_router)
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
