from enum import Enum

from sqlalchemy import BigInteger, VARCHAR, ForeignKey, Column
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import Mapped, relationship, declared_attr
from sqlalchemy.testing.schema import mapped_column

from db.base import CreatedModel


class User(CreatedModel):
    telegram_id: Mapped[int] = mapped_column(BigInteger)
    first_name: Mapped[str] = mapped_column(VARCHAR(20), nullable=True)
    username: Mapped[str] = mapped_column(VARCHAR(255), nullable=True)
    phone: Mapped[str] = mapped_column(VARCHAR(255), nullable=True)
    transactions: Mapped[list['Transaction']] = relationship('Transaction', back_populates='user')

    def __repr__(self):
        return self.telegram_id


class Transaction(CreatedModel):
    class ConvertType(Enum):
        YUAN_TO_UZS = "Yuanni_somga"
        UZS_TO_YUAN = "Somni_yuanga"

    class Status(Enum):
        PENDING = 'Kutilmoqda'
        COMPLETED = 'Muvofaqiyatliy'
        CANCELED = 'Bekor_qilingan'

    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey(User.id, ondelete='CASCADE'))
    user: Mapped[list['User']] = relationship('User', back_populates='transactions')
    check_image: Mapped[str] = mapped_column(VARCHAR)
    card_image: Mapped[str] = mapped_column(VARCHAR)
    convert_type: Mapped[ConvertType] = mapped_column(SQLEnum(ConvertType), default=ConvertType.UZS_TO_YUAN)
    status: Mapped[Status] = mapped_column(SQLEnum(Status), default=Status.PENDING)
    cny_course: Mapped[str] = mapped_column(VARCHAR, nullable=True)
    uzs_course: Mapped[str] = mapped_column(VARCHAR, nullable=True)
    cny_amount: Mapped[str] = mapped_column(VARCHAR, nullable=True)
    uzs_amount: Mapped[str] = mapped_column(VARCHAR, nullable=True)


class VerboseMixin:
    @declared_attr
    def verbose_names(cls):
        return {}

    @declared_attr
    def _columns(cls):
        cols = {}
        for field, column in cls.__dict__.items():
            if isinstance(column, Column) and field in cls.verbose_names:
                column.info["verbose_name"] = cls.verbose_names[field]
            cols[field] = column
        return cols


class AdminCreditCard(CreatedModel, VerboseMixin):
    verbose_names = {
        "card_number": "Karta raqami",
        "owner_first_last_name": "To'liq ism familiyasi",
        "card_type": "Karta turi",
    }

    class CardType(Enum):
        HUMO = 'HUMO'
        UZCARD = 'UZCARD'
        VISA = 'VISA'

    card_number: Mapped[str] = mapped_column(VARCHAR)
    owner_first_last_name: Mapped[str] = mapped_column(VARCHAR)
    card_type: Mapped[CardType] = mapped_column(SQLEnum(CardType))


class AdminChannel(CreatedModel):
    channel_name: Mapped[str] = mapped_column(VARCHAR, nullable=True)
    channel_id: Mapped[str] = mapped_column(VARCHAR)


class AdditionAmountForCourse(CreatedModel):
    yuan_ga: Mapped[str] = mapped_column(VARCHAR)
    som_ga: Mapped[str] = mapped_column(VARCHAR)
    yuan: Mapped[str] = mapped_column(VARCHAR, nullable=True)
    som: Mapped[str] = mapped_column(VARCHAR, nullable=True)

