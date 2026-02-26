from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel


class OrderCreate(BaseModel):
    symbol: str
    side: str
    quantity: Decimal
    price: Decimal


class ConditionCreate(BaseModel):
    condition_type: str
    parameters: dict
    action: dict
