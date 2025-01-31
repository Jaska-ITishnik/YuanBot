from aiogram.types import InlineKeyboardButton
from aiogram.utils.i18n import gettext as _
from aiogram.utils.keyboard import InlineKeyboardBuilder


def change_lang_buttons():
    ikb = InlineKeyboardBuilder()
    buttons = [
        InlineKeyboardButton(text=_("🇺🇿UZ"), callback_data="change_language_to_uz"),
        InlineKeyboardButton(text=_("🇷🇺RU"), callback_data="change_language_to_ru")
    ]
    ikb.add(*buttons)
    return ikb.as_markup()


def transaction_confirmation(current_client, current_transaction):
    ikb = InlineKeyboardBuilder()
    buttons = [
        InlineKeyboardButton(text=_("✅Tasdiqlaysizmi"),
                             callback_data=f"confirm_transaction_{current_transaction}_{current_client}"),
        InlineKeyboardButton(text=_("❌Inkor qilish"),
                             callback_data=f"reject_transaction_{current_transaction}_{current_client}"),
    ]
    ikb.add(*buttons)
    return ikb.as_markup()


def admin_transaction_confirmation(current_client, current_transaction):
    ikb = InlineKeyboardBuilder()
    buttons = [
        InlineKeyboardButton(text=_("✅Ha"),
                             callback_data=f"admin_confirm_transaction_{current_transaction}_{current_client}"),
        InlineKeyboardButton(text=_("❌Yo'q"),
                             callback_data=f"admin_reject_transaction_{current_transaction}_{current_client}")
    ]
    ikb.add(*buttons)
    return ikb.as_markup()
