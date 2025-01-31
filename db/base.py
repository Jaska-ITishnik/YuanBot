from datetime import datetime

import pytz
from sqlalchemy import delete as sqlalchemy_delete, DateTime, update as sqlalchemy_update, BigInteger, \
    TypeDecorator, func
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, AsyncAttrs
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.future import select
from sqlalchemy.orm import sessionmaker, DeclarativeBase, Mapped, mapped_column

from config import conf


class Base(AsyncAttrs, DeclarativeBase):
    @declared_attr
    def __tablename__(self) -> str:
        return self.__name__.lower() + 's'


class AsyncDatabaseSession:
    def __init__(self):
        self._session = None
        self._engine = None

    def __getattr__(self, name):
        return getattr(self._session, name)

    def init(self):
        self._engine = create_async_engine(
            conf.db.db_url
        )
        self._session = sessionmaker(self._engine, expire_on_commit=False, class_=AsyncSession)()

    async def create_all(self):
        async with self._engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def drop_all(self):
        async with self._engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)


db = AsyncDatabaseSession()
db.init()


# ----------------------------- ABSTRACTS ----------------------------------
class AbstractClass:
    @staticmethod
    async def commit():
        try:
            await db.commit()
        except Exception as e:
            print(e)
            await db.rollback()

    @classmethod
    async def create(cls, **kwargs):  # Create
        object_ = cls(**kwargs)
        db.add(object_)
        await cls.commit()
        return object_

    @classmethod
    async def update(cls, id_, **kwargs):
        query = (
            sqlalchemy_update(cls)
            .where(cls.id == id_)
            .values(**kwargs)
            .execution_options(synchronize_session="fetch")
        )
        await db.execute(query)
        await cls.commit()

    @classmethod
    async def get(cls, id_):
        query = select(cls).where(cls.id == id_)
        return (await db.execute(query)).scalar()

    @classmethod
    async def get_by_telegram_id(cls, telegram_id):
        query = select(cls).where(cls.telegram_id == telegram_id)
        return (await db.execute(query)).scalar()

    @classmethod
    async def get_transactions_by_user(cls, user_id):
        query = select(cls).where(cls.user_id == user_id)
        return (await db.execute(query)).scalars()

    @classmethod
    async def get_transaction_by_user(cls, user_id):
        query = select(cls).where(cls.user_id == user_id)
        return (await db.execute(query)).scalar()

    @classmethod
    async def delete(cls, id_):
        query = sqlalchemy_delete(cls).where(cls.id == id_)
        await db.execute(query)
        await cls.commit()

    @classmethod
    async def get_all(cls):
        return (await db.execute(select(cls))).scalars()


class TimeStamp(TypeDecorator):
    impl = DateTime(timezone=True)
    cache_ok = True
    TASHKENT_TIMEZONE = pytz.timezone("Asia/Tashkent")

    def process_bind_param(self, value: datetime, dialect):
        if value is None:
            return None
        if value.tzinfo is None:
            value = self.TASHKENT_TIMEZONE.localize(value)
        return value.astimezone(self.TASHKENT_TIMEZONE)

    def process_result_value(self, value, dialect):
        if value is not None:
            return value.astimezone(self.TASHKENT_TIMEZONE)
        return value


class CreatedModel(Base, AbstractClass):
    __abstract__ = True
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    created_at: Mapped[TimeStamp] = mapped_column(TimeStamp, server_default=func.now())
    updated_at: Mapped[TimeStamp] = mapped_column(TimeStamp, server_default=func.now(), server_onupdate=func.now())
