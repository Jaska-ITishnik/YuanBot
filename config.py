import os
from dataclasses import dataclass, asdict

from dotenv import load_dotenv

load_dotenv()


@dataclass
class BaseConfig:
    def asdict(self):
        return asdict(self)


@dataclass
class DatabaseConfig(BaseConfig):
    """Database connection variables"""

    NAME: str = os.getenv('DB_NAME')
    USER: str = os.getenv('DB_USER')
    PASS: str = os.getenv('DB_PASS')
    HOST: str = os.getenv('DB_HOST')
    PORT: str = os.getenv('DB_PORT')

    @property
    def db_url(self):
        return f"postgresql+asyncpg://{self.USER}:{self.PASS}@{self.HOST}:{self.PORT}/{self.NAME}"


@dataclass
class BotConfig(BaseConfig):
    """Bot configuration"""
    BOT_TOKEN: str = os.getenv('BOT_TOKEN')
    ADMIN_LIST: str = os.getenv('ADMIN_LIST')
    CHAT_IDES_LIST: str = os.getenv('CHAT_IDES_LIST')
    TELEGRAM_USERNAME: str = os.getenv('TELEGRAM_USERNAME')
    MIN_AMOUNT_YUAN: int = int(os.getenv('MIN_AMOUNT_YUAN'))
    MIN_AMOUNT_UZS: int = int(os.getenv('MIN_AMOUNT_UZS'))
    ADMIN_HUMO_CARD_NUMBER: str = os.getenv('ADMIN_HUMO_CARD_NUMBER')
    ADMIN_UZCARD_CARD_NUMBER: str = os.getenv('ADMIN_UZCARD_CARD_NUMBER')
    CARGO_DB_PASSWORD: int = os.getenv("CARGO_DB_PASSWORD")
    CARGO_DB_HOST: str = os.getenv("CARGO_DB_HOST")
    CARGO_DB_PORT: int = os.getenv("CARGO_DB_PORT")
    CARGO_DB_NAME: str = os.getenv("CARGO_DB_NAME")
    # WEB_SERVER_HOST: str = os.getenv('WEB_SERVER_HOST')
    # WEB_SERVER_PORT: int = int(os.getenv('WEB_SERVER_PORT', 8080))
    # WEBHOOK_PATH = "/webhook"
    # WEBHOOK_SECRET = os.getenv('WEBHOOK_SECRET')
    # BASE_WEBHOOK_URL = os.getenv('BASE_WEBHOOK_URL')


@dataclass
class Configuration:
    """All in one configuration's class"""
    db = DatabaseConfig()
    bot = BotConfig()


conf = Configuration()
