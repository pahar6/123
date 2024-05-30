
from typing import Annotated

from pydantic import Field

from .base import BaseMerchant, MerchantEnum
from .cryptopay import CryptoPay
from .yookassa import YooKassa
from .wallet import Wallet


MerchantAnnotated = Annotated[
    YooKassa | CryptoPay | Wallet,
    Field(description="merchant")
]
