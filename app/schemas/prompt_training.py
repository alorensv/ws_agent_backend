from pydantic import BaseModel, Field


class PromptTrainingResponse(BaseModel):
    account_id: str
    account_name: str
    system_prompt: str
    updated_at: str | None = None


class PromptTrainingUpdate(BaseModel):
    system_prompt: str = Field(..., min_length=20)
