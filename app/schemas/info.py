from typing import List
from pydantic import BaseModel


class InventoryItem(BaseModel):
    type: str
    quantity: int

class ReceivedTransactionInfo(BaseModel):
    fromUser: str
    amount: int

class SentTransactionInfo(BaseModel):
    toUser: str
    amount: int

class TransactionHistory(BaseModel):
    received: List[ReceivedTransactionInfo]
    sent: List[SentTransactionInfo]

class InfoResponse(BaseModel):
    coins: int
    inventory: List[InventoryItem]
    coinHistory: TransactionHistory
