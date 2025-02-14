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
from bot.filters import IsAdmin
from bot.states import FormGetAmountInYuan, FormGetAmountInUZS, FormPhotoState, UserInfoForm, AdminSendMessage
from config import conf
from custom_humanize_price import custom_humanize
from db import User, Transaction, AdminCreditCard
from db.models import AdditionAmountForCourse

database = RedisDict()
user_message_router = Router()

ADMIN_LIST = [int(id) for id in conf.bot.ADMIN_LIST.strip().split()]
BASE_DIR = Path(__file__).parent.parent.parent
PHOTO_PATH_HUMO = os.path.join(BASE_DIR, "media", "cards", "humo.png")
PHOTO_PATH_UZCARD = os.path.join(BASE_DIR, "media", "cards", "uzcard.jpeg")
PHOTO_PATH_VISA = os.path.join(BASE_DIR, "media", "cards", "visa.jpg")
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
        await User.create(telegram_id=telegram_id, username=f"https://t.me/{username}")
    await message.answer(_("Assalomu aleykum {}").format(message.from_user.first_name),
                         reply_markup=main_menu_keyboard_buttons(message, lang=data['locale']))


@user_message_router.message(IsAdmin(list(ADMIN_LIST)), F.text == __("📨Xabar yuborish"))
async def admin_catch_function(message: Message, state: FSMContext):
    msg_construction = _("""
<b>Siz yuboraolasiz👇:</b>
<blockquote>📺Video & 📤Habar</blockquote>

<blockquote>🔗Har xil linklar</blockquote>

<blockquote>📍Lokatsiyalar</blockquote>

<blockquote>🖼Rasm & 📤Habar</blockquote>

<blockquote>🎤Ovozliy xabarlar</blockquote>

<blockquote>📂Fayllar & 📤Habar</blockquote>

<b>Yuborishingiz mumkin✍️ 👇👇👇</b>
    """)
    await message.answer(_("Assalomu aleykum ADMIN🦸"))
    await message.answer(text=msg_construction, parse_mode=ParseMode.MARKDOWN_V2.HTML)
    await state.set_state(AdminSendMessage.admin_message)


@user_message_router.message(AdminSendMessage.admin_message, (IsAdmin(list(ADMIN_LIST))) and
                             (F.text != '/start') & (F.content_type.in_([
    ContentType.PHOTO, ContentType.TEXT,
    ContentType.VIDEO, ContentType.LOCATION,
    ContentType.DOCUMENT, ContentType.VOICE,
    ContentType.VIDEO_NOTE])))
async def catch_admin_messages_function(message: Message, state: FSMContext):
    users = await User.get_all()
    video = message.video.file_id if message.video else None
    caption = message.caption if message.caption else ""
    picture = message.photo[-1].file_id if message.photo else None  # Use the last photo for better quality
    voice = message.voice.file_id if message.voice else None
    file = message.document.file_id if message.document else None
    node_video = message.video_note.file_id if message.video_note else None
    location = message.location if message.location else None

    for user in users:
        if int(user.telegram_id) not in list(ADMIN_LIST):
            if video:
                await message.bot.send_video(chat_id=user.telegram_id, video=video, caption=caption)
            if picture:
                await message.bot.send_photo(chat_id=user.telegram_id, photo=picture, caption=caption)
            if voice:
                await message.bot.send_voice(chat_id=user.telegram_id, voice=voice, caption=caption)
            if file:
                await message.bot.send_document(chat_id=user.telegram_id, document=file, caption=caption)
            if node_video:
                await message.bot.send_video_note(chat_id=user.telegram_id, video_note=node_video)
            if location:
                await message.bot.send_location(chat_id=user.telegram_id, latitude=location.latitude,
                                                longitude=location.longitude)
            if message.text:
                await message.bot.send_message(chat_id=user.telegram_id, text=message.text)
    await state.clear()
    await message.answer(text=_("Muvofaqiyatliy yuborildi davom etish ➡ <b>/start</b>"),
                         parse_mode=ParseMode.MARKDOWN_V2.HTML)


@user_message_router.message(F.text == __("🌐Ijtimoiy  tarmoqlarimiz"))
async def social_networks(message: Message, bot: Bot):
    await bot.delete_messages(chat_id=message.chat.id, message_ids=[message.message_id - 1])
    text = _("""
Telegram: {}
    """).format(conf.bot.TELEGRAM_USERNAME)
    await message.answer(text=text, reply_to_message_id=message.message_id,
                         reply_markup=main_menu_keyboard_buttons(message))


@user_message_router.message(F.text == __("🛠Sozlamalar"))
async def settings_function(message: Message, bot: Bot):
    await bot.delete_messages(chat_id=message.chat.id, message_ids=[message.message_id - 1])
    await message.answer(_("Sozlamalar bo'limiga xush kelibsiz👇"), reply_markup=settings_submenu())


@user_message_router.message(F.text == __("🔍Kursni bilish"))
async def get_rate(message: Message, bot: Bot, state: FSMContext):
    addition_amount = await AdditionAmountForCourse.get(id_=1)
    data = await state.get_data()
    text = _(
        """
<b>📉 So'ngi kurs:</b>

💰1$ 👇<blockquote>{yuan}¥</blockquote>
~-~-~-~-~-~-~-~-~-~-~-~-~-~-~
💰1$ 👇<blockquote>{soum} UZS</blockquote>
        """
    ).format(yuan=custom_humanize(str(database['usd_yuan'] - float(float(addition_amount.yuan_ga)))),
             soum=custom_humanize(str(database['usd_uzs'] + float(addition_amount.som_ga))))

    await bot.delete_messages(chat_id=message.chat.id, message_ids=[message.message_id - 1])
    await message.answer(text, ParseMode.MARKDOWN_V2.HTML,
                         reply_markup=main_menu_keyboard_buttons(message, lang=data['locale']))


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
    await message.answer(_("Davom ettirishingiz mumkin👇"),
                         reply_markup=main_menu_keyboard_buttons(message, lang=data['locale']))


@user_message_router.message(F.text == __("🇨🇳CNY"))
async def type_rate_function(message: Message, state: FSMContext, bot: Bot):
    await bot.delete_messages(chat_id=message.chat.id, message_ids=[message.message_id - 1])
    await state.set_state(FormGetAmountInYuan.cny_amount)
    await message.answer(text=_("Summani yuanda kiriting"))


@user_message_router.message(FormGetAmountInYuan.cny_amount,
                             F.text.func(lambda text: text.replace('.', '', 1).isdigit()))
async def catch_amount_func(message: Message, state: FSMContext):
    addition_amount = await AdditionAmountForCourse.get(id_=1)
    text = _(
        """
<b>Tranzaksiya miqdori:</b>

💰1$ 👇<blockquote>{yuan}¥</blockquote>
~-~-~-~-~-~-~-~-~-~-~-~-~-~-~
💰1$ 👇<blockquote>{soum} UZS</blockquote>

~-~-~-~-~-~-~-~-~-~-~-~-~-~-~
<b>📩Qabul qilasiz:</b> <blockquote>{taken_yuan}¥</blockquote>
~-~-~-~-~-~-~-~-~-~-~-~-~-~-~
<b>📤To'laysiz:</b>
 
<b>🇺🇿So'mda:</b><blockquote>{payment_amount} UZS</blockquote>

<b>💲Dollarda:</b><blockquote>{payment_amount_in_dollar}$</blockquote>
        """
    )
    if message.text.isdigit():
        a = int(message.text)
        payment_amount = round(
            (database['usd_uzs'] + float(addition_amount.som_ga)) / (
                    database['usd_yuan'] - float(addition_amount.yuan_ga)) * a, 3)
        await state.update_data(uzs_amount=payment_amount)
        await state.update_data(cny_amount=int(message.text))
        text = text.format(taken_yuan=custom_humanize(str(a)),
                           yuan=custom_humanize(str(database['usd_yuan'] - float(addition_amount.yuan_ga))),
                           soum=custom_humanize(str(database['usd_uzs'] + float(addition_amount.som_ga))),
                           payment_amount=custom_humanize(str(payment_amount)),
                           payment_amount_in_dollar=custom_humanize(
                               str(round(payment_amount / (database['usd_uzs'] + float(addition_amount.som_ga)),
                                         1))))
        await message.answer(text=text, parse_mode=ParseMode.MARKDOWN_V2.HTML, reply_markup=first_confirm_transaction())
    else:
        if len(message.text.split('.')) == 2:
            a = int(message.text.split('.')[0]) + int(message.text.split('.')[1]) / int(
                f"10" * len(message.text.split('.')[1]))
            payment_amount = round(
                database['usd_uzs'] + float(addition_amount.som_ga) / (
                        database['usd_yuan'] - float(addition_amount.yuan_ga)) * a, 3)
            await state.update_data(uzs_amount=payment_amount)
            await state.update_data(cny_amount=a)
            text = text.format(taken_yuan=custom_humanize(str(a)),
                               yuan=custom_humanize(str(database['usd_yuan'] - float(addition_amount.yuan_ga))),
                               soum=custom_humanize(str(database['usd_uzs'] + float(addition_amount.som_ga))),
                               payment_amount=custom_humanize(str(payment_amount)),
                               payment_amount_in_dollar=custom_humanize(
                                   str(round(payment_amount / (database['usd_uzs'] + float(addition_amount.som_ga)),
                                             2))))
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


@user_message_router.message(FormGetAmountInUZS.uzs_amount,
                             F.text.func(lambda text: text.replace('.', '', 1).isdigit()))
async def catch_amount_func(message: Message, state: FSMContext):
    addition_amount = await AdditionAmountForCourse.get(id_=1)
    text = _(
        """
<b>Tranzaksiya miqdori:</b>

💰1$ 👇<blockquote>{yuan}¥</blockquote>
~-~-~-~-~-~-~-~-~-~-~-~-~-~-~
💰1$ 👇<blockquote>{soum} UZS</blockquote>

~-~-~-~-~-~-~-~-~-~-~-~-~-~-~
<b>📩Qabul qilasiz:</b> <blockquote>{taken_yuan}¥</blockquote>
~-~-~-~-~-~-~-~-~-~-~-~-~-~-~
<b>📤To'laysiz:</b> 

<b>🇺🇿So'mda:</b><blockquote>{payment_amount} UZS</blockquote>

<b>💲Dollarda:</b><blockquote>{payment_amount_in_dollar}$</blockquote>
        """
    )
    if message.text.isdigit():
        a = int(message.text)
        taken_yuan = round(
            (database['usd_yuan'] - float(addition_amount.yuan_ga)) * a / (
                    database['usd_uzs'] + float(addition_amount.som_ga)), 3)
        await state.update_data(uzs_amount=a)
        await state.update_data(cny_amount=taken_yuan)
        text = text.format(taken_yuan=custom_humanize(str(taken_yuan)),
                           yuan=custom_humanize(str(database['usd_yuan'] - float(addition_amount.yuan_ga))),
                           soum=custom_humanize(str(database['usd_uzs'] + float(addition_amount.som_ga))),
                           payment_amount=custom_humanize(str(a)),
                           payment_amount_in_dollar=custom_humanize(
                               str(round(a / (database['usd_uzs'] + float(addition_amount.som_ga)), 1))))
        await message.answer(text=text, parse_mode=ParseMode.MARKDOWN_V2.HTML, reply_markup=first_confirm_transaction())
    else:
        if len(message.text.split('.')) == 2:
            a = int(message.text.split('.')[0]) + int(message.text.split('.')[1]) / int(
                f"10" * len(message.text.split('.')[1]))
            taken_yuan = round(
                (database['usd_yuan'] - float(addition_amount.yuan_ga)) * a / (
                        database['usd_uzs'] + float(addition_amount.som_ga)),
                3)
            await state.update_data(uzs_amount=a)
            await state.update_data(cny_amount=taken_yuan)
            text = text.format(taken_yuan=custom_humanize(str(taken_yuan)),
                               yuan=custom_humanize(str(database['usd_yuan'] - float(addition_amount.yuan_ga))),
                               soum=custom_humanize(str(database['usd_uzs'] + float(addition_amount.som_ga))),
                               payment_amount=custom_humanize(str(a)),
                               payment_amount_in_dollar=custom_humanize(
                                   str(round(a / (database['usd_uzs'] + float(addition_amount.som_ga)), 1)))
                               )
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
    addition_amount = await AdditionAmountForCourse.get(id_=1)
    data = await state.get_data()
    text = _("""
To'lov mablag'i: <blockquote>{payment_amount} UZS</blockquote>
~-~-~-~-~-~-~-~-~-~-~-~-~-~-~
Yoki:<blockquote>{payment_amount_in_dollar}$</blockquote>

Kartalardan birini tanlang👇
    """).format(payment_amount=custom_humanize(str(data.get('uzs_amount'))),
                payment_amount_in_dollar=custom_humanize(
                    str(round(data.get('uzs_amount') / (database['usd_uzs'] + float(addition_amount.som_ga)), 1))))
    await message.answer(text=text, parse_mode=ParseMode.MARKDOWN_V2.HTML, reply_markup=credit_cards())


@user_message_router.message((F.text == __("💳Humo")) | (F.text == __("🗃Uzcard")) | (F.text == __("💳Visa")))
async def catch_humo_card(message: Message, state: FSMContext):
    addition_amount = await AdditionAmountForCourse.get(id_=1)
    ADMIN_HUMO_CARD = await AdminCreditCard.get_card_by_name(card_type=AdminCreditCard.CardType.HUMO)
    ADMIN_UZCARD = await AdminCreditCard.get_card_by_name(card_type=AdminCreditCard.CardType.UZCARD)
    ADMIN_VISA = await AdminCreditCard.get_card_by_name(card_type=AdminCreditCard.CardType.VISA)
    current_card_image = None
    data = await state.get_data()
    await state.set_state(FormPhotoState.screenshot)
    caption_text = _("""
<b>💰Mablag'</b>: {payment_amount}
<b>To'lov uchun karta👇</b>
<code>{card_number}</code>
<blockquote>{card_owner}</blockquote>

⚠❗️Diqqat to'lov qilganingizdan keyin chekni screenshotini yuboring🖼
    """)
    if message.text == __("🗃Uzcard") and ADMIN_UZCARD:
        caption_text = caption_text.format(payment_amount=custom_humanize(str(data.get('uzs_amount'))),
                                           card_number=ADMIN_UZCARD.card_number,
                                           card_owner=ADMIN_UZCARD.owner_first_last_name)
        current_card_image = PHOTO_PATH_UZCARD
    elif message.text == __("💳Humo") and ADMIN_HUMO_CARD:
        caption_text = caption_text.format(payment_amount=custom_humanize(str(data.get('uzs_amount'))),
                                           card_number=ADMIN_HUMO_CARD.card_number,
                                           card_owner=ADMIN_HUMO_CARD.owner_first_last_name
                                           )
        current_card_image = PHOTO_PATH_HUMO
    elif message.text == __("💳Visa") and ADMIN_VISA:
        caption_text = caption_text.format(payment_amount=custom_humanize(
            str(round(data.get('uzs_amount') / (database['usd_uzs'] + float(addition_amount.som_ga)), 1))) + "$",
                                           card_number=ADMIN_VISA.card_number,
                                           card_owner=ADMIN_VISA.owner_first_last_name
                                           )
        current_card_image = PHOTO_PATH_VISA
    await message.answer_photo(photo=FSInputFile(current_card_image), caption=caption_text,
                               parse_mode=ParseMode.MARKDOWN_V2.HTML, reply_markup=only_back())


@user_message_router.message(FormPhotoState.screenshot, F.content_type == ContentType.PHOTO)
async def take_screenshot(message: Message, state: FSMContext, bot: Bot):
    await state.update_data(screenshot=(await save_photo_to_media(message, bot, state)))
    await state.set_state(FormPhotoState.alipay_photo)
    await message.answer(text=_("AliPay summani olish uchun QR kodni rasmini yuboring"))


@user_message_router.message(FormPhotoState.alipay_photo, F.content_type == ContentType.PHOTO)
async def take_alipyqr(message: Message, bot: Bot, state: FSMContext):
    additional_amount = await AdditionAmountForCourse.get(id_=1)
    await state.update_data(alipay_photo=(await save_photo_to_media(message, bot, state)))
    data = await state.get_data()
    user = await User.get_by_telegram_id(message.from_user.id)
    transaction_obj = await Transaction.create(
        user_id=user.id,
        check_image=data.get('screenshot'),
        card_image=data.get('alipay_photo'),
        cny_course=custom_humanize(str(database['usd_yuan'] - float(additional_amount.yuan_ga))),
        uzs_course=custom_humanize(str(database['usd_uzs'] + float(additional_amount.som_ga))),
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
                         reply_markup=main_menu_keyboard_buttons(message, lang=data['locale']))


@user_message_router.message(F.text == __("🇺🇿 ♻️ 🇷🇺 Tilni almashtirish"))
async def change_lang(message: Message, bot: Bot):
    await bot.delete_messages(chat_id=message.chat.id, message_ids=[message.message_id - 1])
    await message.answer(_("Tillardan birini tanlang👇"), reply_markup=change_lang_buttons())
