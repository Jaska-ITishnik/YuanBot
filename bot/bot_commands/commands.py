from aiogram import Bot
from aiogram.types import BotCommand, BotCommandScopeChat
from aiogram.utils.i18n import I18n
from db import database
from config import conf
from utils import usd_uzs, usd_yuan

ADMIN_LIST = conf.bot.ADMIN_LIST.strip().split()


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
    # await database.create_all()
    # await database.drop_all()


async def on_shutdown(bot: Bot):
    # await database.drop_all()
    pass
