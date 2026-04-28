from pydantic import BaseModel, Field, field_validator


class CatalogItemBase(BaseModel):
    account_id: str = Field(..., min_length=1)
    category: str = Field(..., min_length=2, max_length=50)
    name: str = Field(..., min_length=3, max_length=100)
    description: str = Field(default="", max_length=5000)
    base_price: float = Field(..., ge=0)
    specifications: dict = Field(default_factory=dict)
    is_active: bool = True

    @field_validator("category", "name", "description", mode="before")
    @classmethod
    def normalize_text(cls, value):
        if value is None:
            return ""
        if isinstance(value, str):
            return value.strip()
        return value


class CatalogItemCreate(CatalogItemBase):
    pass


class CatalogItemUpdate(BaseModel):
    category: str = Field(..., min_length=2, max_length=50)
    name: str = Field(..., min_length=3, max_length=100)
    description: str = Field(default="", max_length=5000)
    base_price: float = Field(..., ge=0)
    specifications: dict = Field(default_factory=dict)
    is_active: bool = True

    @field_validator("category", "name", "description", mode="before")
    @classmethod
    def normalize_text(cls, value):
        if value is None:
            return ""
        if isinstance(value, str):
            return value.strip()
        return value


class CatalogItemResponse(BaseModel):
    id: str
    account_id: str
    category: str
    name: str
    description: str
    base_price: float
    specifications: dict
    is_active: bool
    created_at: str | None = None
