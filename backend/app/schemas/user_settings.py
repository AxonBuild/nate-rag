from pydantic import BaseModel, Field


class SystemPromptResponseSchema(BaseModel):
    default_prompt: str
    custom_prompt: str | None = None
    effective_prompt: str
    is_custom: bool


class SystemPromptUpdateSchema(BaseModel):
    system_prompt: str = Field(default="", description="Full prompt text; empty resets to default")
