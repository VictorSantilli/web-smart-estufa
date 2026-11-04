from datetime import date

from pydantic import BaseModel


class GreenhouseOut(BaseModel):
    id: int
    name: str | None


class GreenhouseUserOut(BaseModel):
    id: int
    email: str
    name: str | None
    is_admin: bool
    is_active: bool
    linked_at: date
