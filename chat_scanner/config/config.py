import zoneinfo
from pathlib import Path
from typing import Optional, Any, Callable, NamedTuple

from loguru import logger

import yaml
from pydantic import BaseModel, BaseSettings, Field, SecretStr, validator
from pydantic.env_settings import InitSettingsSource, EnvSettingsSource, SecretsSettingsSource

from .db import SqliteDB, PostgresDB
from .webhook import Webhook

from ..apps.merchant import MerchantAnnotated, MerchantEnum

BASE_DIR = Path(__file__).parent.parent.parent
LOG_DIR = BASE_DIR / "logs"
MEDIA_DIR = BASE_DIR / 'media'

for DIR in [LOG_DIR, MEDIA_DIR]:
    DIR.mkdir(exist_ok=True)

LOCALES_DIR = BASE_DIR / "chat_scanner/locales"
TIME_ZONE = zoneinfo.ZoneInfo("Europe/Moscow")


def load_yaml(file: str | Path) -> dict[str, Any] | list[Any]:
    with open(BASE_DIR / file, "r", encoding="utf-8") as f:
        r = yaml.safe_load(f)
    return r


class IncludeSupportMessage(NamedTuple):
    message_id: int
    chat_id: int


class SupportMessage(NamedTuple):
    from_message: IncludeSupportMessage
    to_message: IncludeSupportMessage


class Bot(BaseModel):
    token: SecretStr
    admins: list[int] = Field(default_factory=list)
    super_admins: list[int] = Field(default_factory=list)
    REFERRAL_PERCENT: float = 20.0
    SUBSCRIPTION_1_MONTH: float = 500.0
    SUBSCRIPTION_6_MONTH: float = 3000.0
    SUBSCRIPTION_12_MONTH: float = 5000.0
    SUBSCRIPTION_PRO_1_MONTH: float = 1000.0
    SUBSCRIPTION_PRO_6_MONTH: float = 6000.0
    SUBSCRIPTION_PRO_12_MONTH: float = 10000.0
    SUPPORT_CHAT_ID: int | None = None
    SUPPORT_MESSAGES: dict[IncludeSupportMessage, IncludeSupportMessage] = Field(default_factory=dict)

    WITHDRAW_BALANCE: float = 4000
    INSTRUCTION: str = "Пусто"

    START_MESSAGE: str = "Пусто"

    BONUS: float = 200.0
    BONUS_TEXT: str = "Мы дарим на твой реферальный счет 250 ₽"
    AUTO_DELETE_MESSAGE: str = "Автоудаление дублей"
    RESPONSE: str = "Настройка ответов"
    logger.warning(f'[CONFIG-LOGS] Config Bot object variables created')

    @validator("admins", "super_admins")
    def validate_admins(cls, v):
        return v or []


class Settings(BaseSettings):
    bot: Bot
    db: PostgresDB | SqliteDB
    webhook: Optional[Webhook]
    merchants: list[MerchantAnnotated] = Field(default_factory=list)
    logger.success(f'[CONFIG-LOGS] Config Settings merchants variable created with data: {merchants}')

    class Config:
        env_file = r"..\..\.env"
        env_file_encoding = "utf-8"
        config_file = "config.yml"
        allow_mutation = False
        env_nested_delimiter = '__'

        @classmethod
        def customise_sources(
                cls,
                init_settings: InitSettingsSource,
                env_settings: EnvSettingsSource,
                file_secret_settings: SecretsSettingsSource
        ) -> tuple[InitSettingsSource, EnvSettingsSource, Callable, SecretsSettingsSource]:
            r = (
                init_settings,
                env_settings,
                lambda s: load_yaml(BASE_DIR / s.__config__.config_file),
                file_secret_settings
            )
            logger.success(f'[CONFIG-LOGS] Config Settings-Config.customize_source method return data: {r}')  # OK
            return r

    def dump(self):
        with open(BASE_DIR / self.__config__.config_file, "w", encoding="utf-8") as f:
            data = self.dict()

            def recursive_remove_secret(obj):
                if isinstance(obj, dict):
                    for k, v in obj.items():
                        if k == "SUPPORT_MESSAGES":
                            obj[k] = {}

                        if k == "merchants":
                            merchants = []

                            for merchant in v:
                                merchants.append(
                                    {"merchant": str(merchant["merchant"]),
                                     "shop_id": merchant["shop_id"],
                                     "api_key": merchant["api_key"].get_secret_value(),
                                     }
                                )
                            obj[k] = merchants
                        elif isinstance(v, SecretStr):
                            obj[k] = v.get_secret_value()
                        else:
                            recursive_remove_secret(v)
                elif isinstance(obj, list):
                    for v in obj:
                        recursive_remove_secret(v)

            recursive_remove_secret(data)
            yaml.dump(data, f, allow_unicode=True, sort_keys=False)

    def get_merchant(self, merchant: MerchantEnum) -> MerchantAnnotated | None:
        for m in self.merchants:
            if m.merchant == merchant:
                return m
        return None

