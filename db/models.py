from enum import Enum

from sqlalchemy import BigInteger, VARCHAR, ForeignKey
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import Mapped, relationship
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
