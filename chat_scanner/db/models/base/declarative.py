from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase

from .mixin import BaseQuery

class Base(AsyncAttrs, DeclarativeBase, BaseQuery):
    # type_annotation_map = {
    #     str_30: String(30),
    #     str_50: String(50),
    #     num_12_4: Numeric(12, 4),
    #     num_6_2: Numeric(6, 2),
    # }
    # registry = registry(
    #     type_annotation_map={
    #         # str_30: String(30),
    #         # str_50: String(50),
    #         # num_12_4: Numeric(12, 4),
    #         # num_6_2: Numeric(6, 2),
    #         int: BigInteger,
    #     }
    # )
    pass
