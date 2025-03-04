from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional

class RecordBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255, description="Title of the record")
    content: str = Field(..., min_length=1, description="Content of the record")

class RecordCreate(RecordBase):
    pass

class Record(RecordBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)