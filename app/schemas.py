from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional

class RecordBase(BaseModel):
    title: str
    content: str

class RecordCreate(RecordBase):
    pass

class Record(RecordBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True) 