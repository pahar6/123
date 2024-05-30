from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

from cachetools import TTLCache, cachedmethod
from loguru import logger
from pycoingecko import CoinGeckoAPI


@dataclass
class Rate:
    """
    Курс рубля к криптовалютам
    """
    btc: float = 2080330
    usdt: float = 77.03
    ton: float = 148.53
    cache: ClassVar[TTLCache] = TTLCache(maxsize=1, ttl=5)

    @classmethod
    @cachedmethod(lambda cls: cls.cache)
    def get_rate(cls):
        logger.info('Getting rate')
        cg = CoinGeckoAPI()
        try:
            result = cg.get_price(ids='tether,the-open-network,bitcoin', vs_currencies='rub')
            return Rate(
                btc=result['bitcoin']['rub'],
                usdt=result['tether']['rub'],
                ton=result['the-open-network']['rub'],
            )
        except Exception as e:
            logger.error(e)
            return Rate()

    def get_amount(self, rub: float):
        return Rate(
            btc=rub / self.btc,
            usdt=rub / self.usdt,
            ton=rub / self.ton,
        )


import asyncio


async def main():
    rate = Rate.get_rate()
    print(rate)
    rate = rate.get_amount(100)
    print(rate)

    # 4.806929669812001e-05
    print(rate.bitcoin)

    # normal
    print(f"{rate.bitcoin:.8f}")

    print(rate.bitcoin.as_integer_ratio())


if __name__ == '__main__':
    asyncio.run(main())
