from aiogram.types import KeyboardButton
from aiogram.utils.i18n import gettext as _
from aiogram.utils.keyboard import ReplyKeyboardBuilder

from config import conf

ADMIN_LIST = list(map(int, conf.bot.ADMIN_LIST.strip().split()))


def main_menu_keyboard_buttons(message, lang: str = None):
    btn = ReplyKeyboardBuilder()
    buttons = [
        KeyboardButton(text=_("💱Valyuta ayriboshlash(UZS-CNY)", locale=lang)),
        KeyboardButton(text=_("🔍Kursni bilish", locale=lang)),
        KeyboardButton(text=_("🌐Ijtimoiy  tarmoqlarimiz", locale=lang)),
        KeyboardButton(text=_("💸Tranzaksiyalar tarixi", locale=lang)),
        KeyboardButton(text=_("🛠Sozlamalar", locale=lang))
    ]
    if message.from_user.id in ADMIN_LIST:
        buttons.insert(0, KeyboardButton(text=_("📨Xabar yuborish"), locale=lang))
        btn.add(*buttons)
        btn.adjust(1, 2, repeat=True)
    else:
        btn.add(*buttons)
        btn.adjust(1, 2, 2)
    return btn.as_markup(resize_keyboard=True, one_time_keyboard=True)


def settings_submenu():
    btn = ReplyKeyboardBuilder()
    buttons = [
        KeyboardButton(text=_("🇺🇿 ♻️ 🇷🇺 Tilni almashtirish")),
        KeyboardButton(text=_("🔙Orqaga"))
    ]
    btn.add(*buttons)
    btn.adjust(1, repeat=True)
    return btn.as_markup(resize_keyboard=True)


def change_rate_submenu():
    btn = ReplyKeyboardBuilder()
    buttons = [
        KeyboardButton(text=_("🇨🇳CNY")),
        KeyboardButton(text=_("🇺🇿UZS")),
        KeyboardButton(text=_("🔙Orqaga"))
    ]
    btn.add(*buttons)
    btn.adjust(2, 1)
    return btn.as_markup(resize_keyboard=True)


def first_confirm_transaction():
    btn = ReplyKeyboardBuilder()
    buttons = [
        KeyboardButton(text=_("✅Tasdiqlash")),
        KeyboardButton(text=_("🔙Orqaga"))
    ]
    btn.add(*buttons)
    btn.adjust(1, repeat=True)
    return btn.as_markup(resize_keyboard=True)


def credit_cards():
    btn = ReplyKeyboardBuilder()
    buttons = [
        KeyboardButton(text=_("💳Humo")),
        KeyboardButton(text=_("🗃Uzcard")),
        KeyboardButton(text=_("🔙Orqaga"))
    ]
    btn.add(*buttons)
    btn.adjust(2, 1)
    return btn.as_markup(resize_keyboard=True)


def only_back():
    btn = ReplyKeyboardBuilder()
    btn.add(KeyboardButton(text=_("🔙Orqaga")))
    return btn.as_markup(resize_keyboard=True)


def phone_number():
    btn = ReplyKeyboardBuilder()
    return btn.add(KeyboardButton(text=_("📞Telefon"), request_contact=True)).as_markup(resize_keyboard=True)
