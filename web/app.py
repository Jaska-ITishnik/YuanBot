import os

import uvicorn
from libcloud.storage.drivers.local import LocalStorageDriver
from sqlalchemy_file.storage import StorageManager
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.sessions import SessionMiddleware
from starlette_admin import I18nConfig
from starlette_admin.contrib.sqla import Admin, ModelView

from config import conf
from db import User, Transaction, database
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
    label = "Klientlar"
    # list_template = ''

    fields_default_sort = 'username', 'first_name', 'phone'
    searchable_fields = 'username', 'first_name', 'phone'
    exclude_fields_from_edit = 'created_at', 'updated_at'



class TransactionModelView(ModelView):
    label = "Tranzaksiyalar"
    sortable_fields = "cny_amount", "uzs_amount"
    exclude_fields_from_create = 'created_at', 'updated_at'
    exclude_fields_from_edit = 'created_at', 'updated_at'


admin.add_view(UserModelView(User))
admin.add_view(TransactionModelView(Transaction))

# Mount admin to your app
admin.mount_to(app)

# Configure Storage
os.makedirs("./media/attachment", 0o777, exist_ok=True)
container = LocalStorageDriver("./media").get_container("attachment")
StorageManager.add_storage("default", container)

if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=8080)
