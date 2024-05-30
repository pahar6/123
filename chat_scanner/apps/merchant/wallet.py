import datetime
from typing import Literal
from enum import StrEnum

from pydantic import BaseModel

from loguru import logger

# from chat_scanner.db.models import invoice
from .base import BaseMerchant, MerchantEnum
from ...db.models.invoice import Invoice


class WalletResponseStatuses(StrEnum):
    SUCCESS = 'SUCCESS'
    ALREADY = 'ALREADY'
    CONFLICT = 'CONFLICT'
    DENIED = 'ACCESS_DENIED'
    INVALID = 'INVALID_REQUEST'
    INTERNAL = 'INTERNAL_ERROR'


class WalletAssets(StrEnum):
    USDT: str = 'USDT'
    BTC: str = 'BTC'
    TON: str = 'TON'


class WalletOrderStatuses(StrEnum):
    ACTIVE = 'ACTIVE'
    PAID = 'PAID'
    EXPIRED = 'EXPIRED'
    CANCELED = 'CANCELED'


class WalletSchemas:
    assets: WalletAssets = WalletAssets
    response_statuses: WalletResponseStatuses = WalletResponseStatuses
    order_statuses: WalletOrderStatuses = WalletOrderStatuses


class WalletCreateOrderRequest:
    def __init__(self, currency, amount, description, user_id):
        self.currency = currency
        self.amount = amount
        self.description = description
        self.user_id = user_id
        self.__check_options__()

    def __check_options__(self):
        if len(self.description) > 100:
            self.description = self.description[:100]

    def __create_order_data__(self) -> dict:
        external_id = f"{self.user_id}-{datetime.datetime.now().replace(microsecond=0)}"  # Уникальный id заказа
        return {
            "amount": {
                "currencyCode": self.currency,
                "amount": str(float(self.amount))
            },
            "autoConversionCurrency": 'USDT',  # Начислять в USDT
            "description": self.description[:100],  # не больше 100 символов в description
            "returnUrl": "https://t.me/redirect_to_bot",
            "failReturnUrl": "https://t.me/redirect_to_bot",
            "externalId": external_id,
            "timeoutSeconds": 10800,  # Заказ можно оплатить в течение 3 часов
            "customerTelegramUserId": self.user_id
        }


class Wallet(BaseMerchant):
    create_url: str = "https://pay.wallet.tg/wpay/store-api/v1/order"  # uri для обработки апи
    merchant: Literal[MerchantEnum.WALLET]

    @property
    def headers(self) -> dict:
        return {
            "Wpay-Store-Api-Key": self.api_key.get_secret_value(),
            "Content-Type": 'application/json',
            'Accept': 'application/json'
        }

    async def create_invoice(
            self,
            user_id: int,
            amount: int | float | str,  # In RUB
            currency: str = 'USDT',  # Default - USDT
            description: str | None = None,
            rate: str | None = None,
            **kwargs
    ) -> Invoice | None:

        try:
            response = await self.make_request(
                method='POST',
                url=self.create_url,
                json=WalletCreateOrderRequest(
                    currency=currency,
                    amount=amount,
                    description=description,
                    user_id=user_id
                ).__create_order_data__()
            )

            if response['status'] == WalletSchemas.response_statuses.SUCCESS:
                order_id = response['data']['id']
                pay_link = response['data']['payLink']

                return Invoice(
                    user_id=user_id,
                    amount=amount,
                    currency=currency,
                    invoice_id=str(order_id),
                    pay_url=pay_link,
                    description=description,
                    merchant=self.merchant,
                    rate=rate
                )
            else:
                message = response['message']
                logger.warning(f'Not create invoice for user ({user_id}) with wallet-error-message: {message}')
        except Exception as create_invoice_error:
            logger.warning(f"[INVOICE] Not create invoice with error: {create_invoice_error}")
        return None

    async def is_paid(self, invoice_id: str) -> bool:
        try:
            response = await self.make_request(
                method='GET',
                url=self.create_url + f'/preview?id={invoice_id}'
            )
            # logger.warning(f"[INVOICE] Check paid invoice request (response): {response}")
            if response['status'] == WalletSchemas.response_statuses.SUCCESS:
                if response['data']['status'] == WalletSchemas.order_statuses.PAID:
                    return True
            return False
        except Exception as error:
            logger.warning(f"[INVOICE] Check paid invoice error: {error} ")
        return False


if __name__ == '__main__':
    print(1)
    wallet_data = {"shop-id": None, 'api-key': 'Pf8mLDdmWHflcwL6kbd060yqQdiFAMXX4ezO'}
    wallet = Wallet(**wallet_data)
    print(wallet)
    print(wallet.merchant)
