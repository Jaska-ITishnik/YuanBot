import os
from typing import Dict, Any, Union

import anyio
import uvicorn
from libcloud.storage.drivers.local import LocalStorageDriver
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from sqlalchemy_file.storage import StorageManager
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.sessions import SessionMiddleware
from starlette.requests import Request
from starlette_admin import I18nConfig
from starlette_admin.contrib.sqla import Admin
from starlette_admin.contrib.sqla import ModelView

from bot.handlers import database as datab
from config import conf
from db import User, Transaction, database, AdminCreditCard, AdminChannel
from db.models import AdditionAmountForCourse
from web.provider import UsernameAndPasswordProvider

middleware = [
    Middleware(SessionMiddleware, secret_key=conf.web.SECRET_KEY)
]

app = Starlette(middleware=middleware)

i18n_config = I18nConfig(
    default_locale="uz"
)
logo_url = 'https://i.ibb.co/NgjxKy0c/china-uzbek.jpg'
admin = Admin(
    engine=database._engine,
    title="Yuan Bot Web Admin",
    templates_dir='templates/admin/index.html',
    base_url='/',
    logo_url=logo_url,
    login_logo_url='https://i.ibb.co/RkbDfwS7/login-logo-2.jpg',
    auth_provider=UsernameAndPasswordProvider(),
    i18n_config=i18n_config
)


class UserModelView(ModelView):
    label = "🤵 Klientlar"
    # list_template = ''

    fields_default_sort = 'username', 'first_name', 'phone'
    searchable_fields = 'username', 'first_name', 'phone'
    exclude_fields_from_edit = 'created_at', 'updated_at'


class TransactionModelView(ModelView):
    label = "💰 Tranzaksiyalar"
    sortable_fields = "cny_amount", "uzs_amount"
    exclude_fields_from_create = 'created_at', 'updated_at'
    exclude_fields_from_edit = 'created_at', 'updated_at'


class AdminCreditCardModelView(ModelView):
    label = "💳 Admin Kartalari"
    exclude_fields_from_create = 'created_at', 'updated_at'
    exclude_fields_from_edit = 'created_at', 'updated_at'


class AdminChannelModelView(ModelView):
    label = "💬 Admin Kanallari"
    exclude_fields_from_create = 'created_at', 'updated_at'
    exclude_fields_from_edit = 'created_at', 'updated_at'


class AdditionAmountForCourseModelView(ModelView):
    label = "💸 Kursga qo'shimcha"
    exclude_fields_from_create = 'created_at', 'updated_at'
    exclude_fields_from_edit = 'created_at', 'updated_at'

    async def create(self, request: Request, data: Dict[str, Any]) -> Any:
        """Override the create method to calculate yuan and som before saving."""
        try:
            data = await self._arrange_data(request, data)  # Prepare data
            await self.validate(request, data)  # Validate input

            # ✅ Calculate yuan and som before inserting into the database
            data["yuan"] = str(self.calculate_yuan(data))
            data["som"] = str(self.calculate_som(data))

            session: Union[Session, AsyncSession] = request.state.session
            obj = await self._populate_obj(request, self.model(), data)
            session.add(obj)
            await self.before_create(request, data, obj)

            if isinstance(session, AsyncSession):
                await session.commit()
                await session.refresh(obj)
            else:
                await anyio.to_thread.run_sync(session.commit)
                await anyio.to_thread.run_sync(session.refresh, obj)

            await self.after_create(request, obj)
            return obj
        except Exception as e:
            return self.handle_exception(e)

    async def after_edit(self, request: Request, obj: Any) -> None:
        """
        This hook is called after an item is successfully edited.
        It recalculates `yuan` and `som` after updating the object.
        """
        session: Union[Session, AsyncSession] = request.state.session

        # ✅ Recalculate values
        obj.yuan = str(self.calculate_yuan(obj.__dict__))
        obj.som = str(self.calculate_som(obj.__dict__))

        # ✅ Save changes to database
        if isinstance(session, AsyncSession):
            await session.commit()
            await session.refresh(obj)
        else:
            await anyio.to_thread.run_sync(session.commit)
            await anyio.to_thread.run_sync(session.refresh, obj)


    def calculate_yuan(self, data):
        """Logic to calculate `yuan`. Modify this based on your business logic."""
        return round(datab['usd_yuan'] - float(data.get("yuan_ga", 0)), 2)

    def calculate_som(self, data):
        """Logic to calculate `som`. Modify this based on your business logic."""
        return round(datab['usd_uzs'] + float(data.get("som_ga", 0)), 2)


admin.add_view(UserModelView(User))
admin.add_view(TransactionModelView(Transaction))
admin.add_view(AdminCreditCardModelView(AdminCreditCard))
admin.add_view(AdminChannelModelView(AdminChannel))
admin.add_view(AdditionAmountForCourseModelView(AdditionAmountForCourse))

# Mount admin to your app
admin.mount_to(app)

# Configure Storage
os.makedirs("./media/attachment", 0o777, exist_ok=True)
container = LocalStorageDriver("./media").get_container("attachment")
StorageManager.add_storage("default", container)

if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=8088)
