from aiogram import Router, F
from aiogram.enums import ParseMode
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, FSInputFile
from aiogram.utils.i18n import gettext as _

from bot.button_functions import main_menu_keyboard_buttons, admin_transaction_confirmation
from config import conf
from db import User, Transaction

user_callback_router = Router()
ADMIN = int(conf.bot.ADMIN_LIST.split()[0])


@user_callback_router.callback_query(F.data.startswith("change_language_to_"))
async def change_lang_callback_func(callback: CallbackQuery, state: FSMContext):
    lang = callback.data.split('_')[-1]
    await state.set_data({'locale': lang})
    await callback.message.delete()
    await callback.message.answer(_("Til tanlandi", locale=lang), reply_markup=main_menu_keyboard_buttons(lang))


@user_callback_router.callback_query(F.data.startswith("confirm_transaction") | F.data.startswith("reject_transaction"))
async def confirm_transaction(callback: CallbackQuery, state: FSMContext):
    current_client_telegram_id = int(callback.data.split("_")[-1])
    current_transaction_id = int(callback.data.split("_")[-2])
    transaction = await Transaction.get(id_=current_transaction_id)
    client = await User.get_by_telegram_id(callback.from_user.id)
    text = _("""
<b>📈 Tranzaksiya raqami</b>: 🔢 {obj}

<b>Mijoz:</b> {first_name}
<b>Telefon:</b> {phone_number}
<b>Yuan miqdori:</b> {cny_amount}¥
<b>UZS miqdori:</b> {uzs_amount} UZS

<b>Admin tranzaksiyani tasdiqlaysizmi👇</b>
    """).format(obj=transaction.id,
                first_name=client.first_name,
                phone_number=client.phone,
                cny_amount=transaction.cny_amount,
                uzs_amount=transaction.uzs_amount)
    await callback.message.delete()
    if callback.data.startswith("confirm_transaction"):
        await callback.message.bot.send_message(
            text=_("""✅Sizning so'rovingiz adminga yuborildi 24 soat gacha ko'rib chiqiladi😊"""),
            chat_id=callback.from_user.id)
        await callback.message.bot.send_photo(chat_id=ADMIN, photo=FSInputFile(transaction.check_image), caption=text,
                                              reply_markup=admin_transaction_confirmation(current_client_telegram_id,
                                                                                          transaction.id),
                                              parse_mode=ParseMode.MARKDOWN_V2.HTML
                                              )
    else:
        await callback.message.answer(text=_("Bekor qilindi❌"), reply_markup=main_menu_keyboard_buttons())


@user_callback_router.callback_query((F.data.startswith("admin_confirm_")) | (F.data.startswith("admin_reject_")))
async def admins_transaction_final_decision(callback: CallbackQuery, state: FSMContext):
    transaction = await Transaction.get(id_=int(callback.data.split("_")[-2]))
    current_client_telegram_id = int(callback.data.split("_")[-1])
    if callback.data.startswith("admin_confirm_"):
        await callback.message.edit_reply_markup(callback.message.caption)
        await transaction.update(transaction.id, status=Transaction.Status.COMPLETED)
        await callback.message.bot.send_message(text=_("""
Sizning sorovingiz qabul qilindi😊
To'lovlaringizni to'lovlar tarixidan kuzatishingiz mumkin👇
        """), chat_id=current_client_telegram_id)
        await state.clear()
    else:
        await callback.message.delete()
        await transaction.update(transaction.id, status=Transaction.Status.CANCELED)
        await callback.message.bot.send_message(text=_("""
Sizning sorovingiz qabul qilinmadi🥶❌
To'lovlaringizni to'lovlar tarixidan kuzatishingiz mumkin👇
                """), chat_id=current_client_telegram_id)
        await state.clear()
