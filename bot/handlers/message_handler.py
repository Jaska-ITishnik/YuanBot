import os
from pathlib import Path

from aiogram import Router, F, Bot
from aiogram.enums import ParseMode, ContentType
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, FSInputFile
from aiogram.utils.i18n import gettext as _, lazy_gettext as __
from redis.commands.helpers import random_string
from redis_dict import RedisDict

from bot.button_functions import main_menu_keyboard_buttons, settings_submenu, change_lang_buttons, change_rate_submenu, \
    first_confirm_transaction, credit_cards, only_back, transaction_confirmation, phone_number
from bot.states import FormGetAmountInYuan, FormGetAmountInUZS, FormPhotoState, UserInfoForm
from config import conf
from custom_humanize_price import custom_humanize
from db import User, Transaction

database = RedisDict()
user_message_router = Router()

BASE_DIR = Path(__file__).parent.parent.parent
PHOTO_PATH_HUMO = os.path.join(BASE_DIR, "media", "cards", "humo.png")
PHOTO_PATH_UZCARD = os.path.join(BASE_DIR, "media", "cards", "uzcard.jpeg")
MEDIA_DIRECTORY = os.path.join(BASE_DIR, 'media')
random_str = random_string(length=6)


async def save_photo_to_media(message, bot: Bot, state: FSMContext):
    try:
        file = await bot.get_file(message.photo[-1].file_id)
        file_name = f"{file.file_unique_id}_{random_str}.jpg"
        file_path = os.path.join(MEDIA_DIRECTORY, file_name)
        await bot.download_file(file.file_path, file_path)
        return file_path
    except Exception as e:
        await message.answer(_("Xatolik yuz berdi Imageni yuklay olmadim: {error}").format(error=str(e)))
        return None


@user_message_router.message(CommandStart())
async def start_func(message: Message, state: FSMContext):
    data = await state.get_data()
    telegram_id = message.from_user.id
    username = message.from_user.username
    user = await User.get_by_telegram_id(telegram_id)
    if not user:
        await User.create(telegram_id=telegram_id, username=username)
    await message.answer(_("Assalomu aleykum {}").format(message.from_user.first_name),
                         reply_markup=main_menu_keyboard_buttons(lang=data['locale']))


@user_message_router.message(F.text == __("🌐Ijtimoiy  tarmoqlarimiz"))
async def social_networks(message: Message, bot: Bot):
    await bot.delete_messages(chat_id=message.chat.id, message_ids=[message.message_id - 1])
    text = _("""
Telegram: {}
    """).format(conf.bot.TELEGRAM_USERNAME)
    await message.answer(text=text, reply_to_message_id=message.message_id, reply_markup=main_menu_keyboard_buttons())


@user_message_router.message(F.text == __("🛠Sozlamalar"))
async def settings_function(message: Message, bot: Bot):
    await bot.delete_messages(chat_id=message.chat.id, message_ids=[message.message_id - 1])
    await message.answer(_("Sozlamalar bo'limiga xush kelibsiz👇"), reply_markup=settings_submenu())


@user_message_router.message(F.text == __("🔍Kursni bilish"))
async def get_rate(message: Message, bot: Bot, state: FSMContext):
    data = await state.get_data()
    text = _(
        """
<b>📉 So'ngi kurs:</b>

💰1$ 👇<blockquote>{yuan}¥</blockquote>
~-~-~-~-~-~-~-~-~-~-~-~-~-~-~
💰1$ 👇<blockquote>{soum} UZS</blockquote>
        """
    ).format(yuan=custom_humanize(str(database['usd_yuan'])), soum=custom_humanize(str(database['usd_uzs'])))

    await bot.delete_messages(chat_id=message.chat.id, message_ids=[message.message_id - 1])
    await message.answer(text, ParseMode.MARKDOWN_V2.HTML, reply_markup=main_menu_keyboard_buttons(lang=data['locale']))


@user_message_router.message(F.text == __("💱Valyuta ayriboshlash(UZS-CNY)"))
async def change_rate_function(message: Message, bot: Bot, state: FSMContext):
    user_telegram_id = message.from_user.id
    user = await User.get_by_telegram_id(user_telegram_id)
    if user.first_name and user.phone:
        await bot.delete_messages(chat_id=message.chat.id, message_ids=[message.message_id - 1])
        await message.answer(text=_("Summani qaysi valyutada kiritasiz?"), reply_markup=change_rate_submenu())
    else:
        await state.set_state(UserInfoForm.first_name)
        await message.answer(text=_("""
<b>Iltimos oldin ismingizni kiriting
Masalan:</b> <i>Abror</i>
        """), parse_mode=ParseMode.MARKDOWN_V2.HTML)


@user_message_router.message(UserInfoForm.first_name, F.text.isalpha())
async def catch_first_name_function(message: Message, state: FSMContext):
    await state.update_data(first_name=message.text)
    await state.set_state(UserInfoForm.phone_number)
    await message.answer(_("""
<b>Telefon nomerni pastdagi tugma orqaliy jo'nating👇</b>
        """), reply_markup=phone_number(), parse_mode=ParseMode.MARKDOWN_V2.HTML)


@user_message_router.message(UserInfoForm.phone_number, F.content_type == ContentType.CONTACT)
async def catch_phone_number(message: Message, state: FSMContext):
    await state.update_data(phone_number=message.contact.phone_number)
    data = await state.get_data()
    user = await User.get_by_telegram_id(message.from_user.id)
    await user.update(user.id, first_name=data.get('first_name'), phone=data.get('phone_number'))
    await message.answer(_("Davom ettirishingiz mumkin👇"), reply_markup=main_menu_keyboard_buttons(lang=data['locale']))


@user_message_router.message(F.text == __("🇨🇳CNY"))
async def type_rate_function(message: Message, state: FSMContext, bot: Bot):
    await bot.delete_messages(chat_id=message.chat.id, message_ids=[message.message_id - 1])
    await state.set_state(FormGetAmountInYuan.cny_amount)
    await message.answer(text=_("Summani yuanda kiriting"))


@user_message_router.message(FormGetAmountInYuan.cny_amount, F.text != __("🔙Orqaga"), F.text != __("✅Tasdiqlash"),
                             F.text != __("🇺🇿UZS"), F.text != __("💳Humo"), F.text != __("🗃Uzcard"))
async def catch_amount_func(message: Message, state: FSMContext):
    text = _(
        """
<b>Tranzaksiya miqdori:</b>

💰1$ 👇<blockquote>{yuan}¥</blockquote>
~-~-~-~-~-~-~-~-~-~-~-~-~-~-~
💰1$ 👇<blockquote>{soum} UZS</blockquote>

~-~-~-~-~-~-~-~-~-~-~-~-~-~-~
<b>📩Qabul qilasiz:</b> <blockquote>{taken_yuan}¥</blockquote>
~-~-~-~-~-~-~-~-~-~-~-~-~-~-~
<b>📤To'laysiz:</b> <blockquote>{payment_amount} UZS</blockquote>
        """
    )
    if message.text.isdigit() and (a := int(message.text)) >= conf.bot.MIN_AMOUNT_YUAN:
        payment_amount = round(database['usd_uzs'] / database['usd_yuan'] * a, 3)
        await state.update_data(uzs_amount=payment_amount)
        await state.update_data(cny_amount=int(message.text))
        text = text.format(taken_yuan=custom_humanize(str(a)),
                           yuan=custom_humanize(str(database['usd_yuan'])),
                           soum=custom_humanize(str(database['usd_uzs'])),
                           payment_amount=custom_humanize(str(payment_amount)))
        await message.answer(text=text, parse_mode=ParseMode.MARKDOWN_V2.HTML, reply_markup=first_confirm_transaction())
    else:
        if len(message.text.split('.')) == 2 and (
                a := int(message.text.split('.')[0]) + int(message.text.split('.')[1]) / int(
                    f"10" * len(message.text.split('.')[1]))) >= conf.bot.MIN_AMOUNT_YUAN:
            payment_amount = round(database['usd_uzs'] / database['usd_yuan'] * a, 3)
            await state.update_data(uzs_amount=payment_amount)
            await state.update_data(cny_amount=a)
            text = text.format(taken_yuan=custom_humanize(str(a)),
                               yuan=custom_humanize(str(database['usd_yuan'])),
                               soum=custom_humanize(str(database['usd_uzs'])),
                               payment_amount=custom_humanize(str(payment_amount)))
            await message.answer(text=text, parse_mode=ParseMode.MARKDOWN_V2.HTML,
                                 reply_markup=first_confirm_transaction())
        else:
            await message.answer(text=_(
                """
<b>Iltimos yaroqliy qiymatni kiriting👇:</b>

<b>📌Ko'rinishi masalan:</b> <blockquote>10 yoki 10.5</blockquote>

<b>📉Minimal qiymat yuanda:</b> <blockquote>{min_yuan}¥</blockquote>
                """).format(min_yuan=conf.bot.MIN_AMOUNT_YUAN
                            ), parse_mode=ParseMode.MARKDOWN_V2.HTML)


@user_message_router.message(F.text == __("🇺🇿UZS"))
async def type_rate_function(message: Message, state: FSMContext, bot: Bot):
    await bot.delete_messages(chat_id=message.chat.id, message_ids=[message.message_id - 1])
    await state.set_state(FormGetAmountInUZS.uzs_amount)
    await message.answer(text=_("Summani so'mda kiriting"))


@user_message_router.message(FormGetAmountInUZS.uzs_amount, F.text != __("🔙Orqaga"), F.text != __("✅Tasdiqlash"),
                             F.text != __("🇺🇿UZS"), F.text != __("💳Humo"), F.text != __("🗃Uzcard"))
async def catch_amount_func(message: Message, state: FSMContext):
    text = _(
        """
<b>Tranzaksiya miqdori:</b>

💰1$ 👇<blockquote>{yuan}¥</blockquote>
~-~-~-~-~-~-~-~-~-~-~-~-~-~-~
💰1$ 👇<blockquote>{soum} UZS</blockquote>

~-~-~-~-~-~-~-~-~-~-~-~-~-~-~
<b>📩Qabul qilasiz:</b> <blockquote>{taken_yuan}¥</blockquote>
~-~-~-~-~-~-~-~-~-~-~-~-~-~-~
<b>📤To'laysiz:</b> <blockquote>{payment_amount} UZS</blockquote>
        """
    )
    if message.text.isdigit() and (a := int(message.text)) >= conf.bot.MIN_AMOUNT_UZS:
        taken_yuan = round(database['usd_yuan'] * a / database['usd_uzs'], 3)
        await state.update_data(uzs_amount=a)
        await state.update_data(cny_amount=taken_yuan)
        text = text.format(taken_yuan=custom_humanize(str(taken_yuan)),
                           yuan=custom_humanize(str(database['usd_yuan'])),
                           soum=custom_humanize(str(database['usd_uzs'])),
                           payment_amount=custom_humanize(str(a)))
        await message.answer(text=text, parse_mode=ParseMode.MARKDOWN_V2.HTML, reply_markup=first_confirm_transaction())
    else:
        if len(message.text.split('.')) == 2 and (
                a := int(message.text.split('.')[0]) + int(message.text.split('.')[1]) / int(
                    f"10" * len(message.text.split('.')[1]))) >= conf.bot.MIN_AMOUNT_UZS:
            taken_yuan = round(database['usd_yuan'] * a / database['usd_uzs'], 3)
            await state.update_data(uzs_amount=a)
            await state.update_data(cny_amount=taken_yuan)
            text = text.format(taken_yuan=custom_humanize(str(taken_yuan)),
                               yuan=custom_humanize(str(database['usd_yuan'])),
                               soum=custom_humanize(str(database['usd_uzs'])),
                               payment_amount=custom_humanize(str(a)))
            await message.answer(text=text, parse_mode=ParseMode.MARKDOWN_V2.HTML,
                                 reply_markup=first_confirm_transaction())
        else:
            await message.answer(text=_(
                """
<b>Iltimos yaroqliy qiymatni kiriting👇:</b>

<b>📌Ko'rinishi masalan:</b> <blockquote>30000 yoki 50000</blockquote>

<b>📉Minimal qiymat so'mda:</b> <blockquote>{min_som} USD</blockquote>
                """).format(min_som=conf.bot.MIN_AMOUNT_UZS
                            ), parse_mode=ParseMode.MARKDOWN_V2.HTML)


@user_message_router.message(F.text == __("✅Tasdiqlash"))
async def confirm_function(message: Message, state: FSMContext):
    data = await state.get_data()
    text = _("""
To'lov mablag'i: <b>{payment_amount} UZS</b>
Kartalardan birini tanlang👇
    """).format(payment_amount=custom_humanize(str(data.get('uzs_amount'))))
    await message.answer(text=text, parse_mode=ParseMode.MARKDOWN_V2.HTML, reply_markup=credit_cards())


@user_message_router.message((F.text == __("💳Humo")) | (F.text == __("🗃Uzcard")))
async def catch_humo_card(message: Message, state: FSMContext):
    current_card_image = None
    data = await state.get_data()
    await state.set_state(FormPhotoState.screenshot)
    caption_text = _("""
<b>💰Mablag'</b>: {payment_amount}
<b>To'lov uchun karta👇</b>
<code>{card_number}</code>
<blockquote>Palonchiyev Pistonchi1</blockquote>

⚠❗️Diqqat to'lov qilganingizdan keyin chekni screenshotini yuboring🖼
    """)
    if message.text == __("🗃Uzcard"):
        caption_text = caption_text.format(payment_amount=custom_humanize(str(data.get('uzs_amount'))),
                                           card_number=conf.bot.ADMIN_UZCARD_CARD_NUMBER)
        current_card_image = PHOTO_PATH_UZCARD
    if message.text == __("💳Humo"):
        caption_text = caption_text.format(payment_amount=custom_humanize(str(data.get('uzs_amount'))),
                                           card_number=conf.bot.ADMIN_HUMO_CARD_NUMBER)
        current_card_image = PHOTO_PATH_HUMO
    await message.answer_photo(photo=FSInputFile(current_card_image), caption=caption_text,
                               parse_mode=ParseMode.MARKDOWN_V2.HTML, reply_markup=only_back())


@user_message_router.message(FormPhotoState.screenshot, F.content_type == ContentType.PHOTO)
async def take_screenshot(message: Message, state: FSMContext, bot: Bot):
    await state.update_data(screenshot=(await save_photo_to_media(message, bot, state)))
    await state.set_state(FormPhotoState.alipay_photo)
    await message.answer(text=_("AliPay summani olish uchun QR kodni rasmini yuboring"))


@user_message_router.message(FormPhotoState.alipay_photo, F.content_type == ContentType.PHOTO)
async def take_alipyqr(message: Message, bot: Bot, state: FSMContext):
    await state.update_data(alipay_photo=(await save_photo_to_media(message, bot, state)))
    data = await state.get_data()
    user = await User.get_by_telegram_id(message.from_user.id)
    transaction_obj = await Transaction.create(
        user_id=user.id,
        check_image=data.get('screenshot'),
        card_image=data.get('alipay_photo'),
        cny_course=custom_humanize(str(database['usd_yuan'])),
        uzs_course=custom_humanize(str(database['usd_uzs'])),
        cny_amount=custom_humanize(str(data.get('cny_amount'))),
        uzs_amount=custom_humanize(str(data.get('uzs_amount')))
    )
    text = _("""
<b>📈 Tranzaksiya raqami</b>: 🔢 {obj}

~-~-~-~-~-~-~-~-~-~-~-~-~-~-~
<b>📤To'laysiz:</b> <blockquote>{payment_amount} UZS</blockquote>

<b>Barcha jarayonlar to'griligini tasdiqlang!</b>
    """).format(payment_amount=custom_humanize(str(data.get('uzs_amount'))), obj=transaction_obj.id)
    await message.answer_photo(photo=FSInputFile(transaction_obj.check_image), caption=text,
                               parse_mode=ParseMode.MARKDOWN_V2.HTML,
                               reply_markup=transaction_confirmation(message.from_user.id, transaction_obj.id))


@user_message_router.message(F.text == __("💸Tranzaksiyalar tarixi"))
async def transaction_history_function(message: Message):
    user = await User.get_by_telegram_id(message.from_user.id)
    user_transactions = await Transaction.get_transactions_by_user(user_id=user.id)
    exists_transaction = await Transaction.get_transaction_by_user(user_id=user.id)
    if exists_transaction:
        for transaction in user_transactions:
            text = _("""
<b>🔢 Tranzaksiya raqami: </b> {transaction_number}
<b>Holati:</b> {transaction_status}
<b>Yuan:</b> {amount_yuan}¥
<b>UZS:</b> {amount_uzs} UZS
<b>📆Sanasi:</b> {transaction_date}
<b>⌛Vaqti:</b> {transaction_time}
            """).format(
                transaction_number=transaction.id,
                transaction_status=transaction.status.value,
                amount_yuan=transaction.cny_amount,
                amount_uzs=transaction.uzs_amount,
                transaction_date=f"{transaction.updated_at.date()}",
                transaction_time=f"{str(transaction.updated_at.time().hour).zfill(2)} : {str(transaction.updated_at.time().minute).zfill(2)}"
            )
            await message.answer(text=text, parse_mode=ParseMode.MARKDOWN_V2.HTML)
    else:
        await message.answer("⚠ Sizda hali tranzaksiyalar mavjud emas")


@user_message_router.message(F.text == __("🔙Orqaga"))
async def back_function(message: Message, bot: Bot, state: FSMContext):
    data = await state.get_data()
    await bot.delete_messages(chat_id=message.chat.id, message_ids=[message.message_id - 1])
    await message.answer(_("Siz asosiy menyudasiz 👇 birini tanlang"),
                         reply_markup=main_menu_keyboard_buttons(lang=data['locale']))


@user_message_router.message(F.text == __("🇺🇿 ♻️ 🇷🇺 Tilni almashtirish"))
async def change_lang(message: Message, bot: Bot):
    await bot.delete_messages(chat_id=message.chat.id, message_ids=[message.message_id - 1])
    await message.answer(_("Tillardan birini tanlang👇"), reply_markup=change_lang_buttons())
