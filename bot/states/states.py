from aiogram.fsm.state import StatesGroup, State


class UserInfoForm(StatesGroup):
    phone_number = State()
    first_name = State()


class FormGetAmountInYuan(StatesGroup):
    cny_amount = State()
    uzs_amount = State()


class FormGetAmountInUZS(StatesGroup):
    cny_amount = State()
    uzs_amount = State()


class FormPhotoState(StatesGroup):
    # current_transaction_id = State()
    screenshot = State()
    alipay_photo = State()


class FormGetCurrentClient(StatesGroup):
    current_client_telegram_id = State()
