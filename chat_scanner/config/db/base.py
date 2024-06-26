import abc

from pydantic import BaseModel, SecretStr


class Database(BaseModel, abc.ABC):
    user: str
    password: SecretStr
    database: str
    host: str = "localhost"
    port: int =
    timezone: str = "Europe/Moscow"
    dialect: str = "asyncpg"
