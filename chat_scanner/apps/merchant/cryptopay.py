from typing import Literal

from CryptoPayAPI import CryptoPay as CryptoPayAPI, schemas
from pydantic import validator

from .base import BaseMerchant, MerchantEnum, PAYMENT_LIFETIME
from ...db.models.invoice import Invoice


class CryptoPay(BaseMerchant):
    cp: CryptoPayAPI | None
    merchant: Literal[MerchantEnum.CRYPTO_PAY]

    @validator('cp', always=True)
    def validate_cp(cls, v, values):
        return v or CryptoPayAPI(values.get("api_key").get_secret_value())

    async def create_invoice(
            self,
            user_id: int,
            amount: int | float | str,
            currency: schemas.Assets = schemas.Assets.USDT,
            description: str | None = None,
            rate: str | None = None,
            **kwargs
    ) -> Invoice:
        invoice = await self.cp.create_invoice(
            asset=currency,
            amount=amount,
            description=description,
            # paid_btn_name=PaidButtonNames.VIEW_ITEM,
            # paid_btn_url='https://example.com'
            expires_in=PAYMENT_LIFETIME
        )
        return Invoice(
            user_id=user_id,
            amount=amount,
            currency=currency,
            invoice_id=str(invoice.invoice_id),
            pay_url=invoice.pay_url,
            description=description,
            merchant=self.merchant,
            rate=rate
        )

    async def is_paid(self, invoice_id: str) -> bool:
        invoices = await self.cp.get_invoices(
            invoice_ids=invoice_id,
            status=schemas.InvoiceStatus.PAID
        )
        return invoices[0].status == schemas.InvoiceStatus.PAID
