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
    received: list[ReceivedTransactionInfo]
    sent: list[SentTransactionInfo]

class InfoResponse(BaseModel):
    coins: int
    inventory: list[InventoryItem]
    coinHistory: TransactionHistory
