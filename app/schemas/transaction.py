from pydantic import BaseModel, Field


class SendCoinRequest(BaseModel):
    toUser: str
    amount: int = Field(gt=0)
