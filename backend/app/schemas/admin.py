from pydantic import BaseModel, EmailStr, Field


class InviteRequestSchema(BaseModel):
    email: EmailStr
    role: str = Field(default="client", pattern="^(admin|client)$")


class InviteResponseSchema(BaseModel):
    id: str
    email_address: str
    status: str
    role: str
