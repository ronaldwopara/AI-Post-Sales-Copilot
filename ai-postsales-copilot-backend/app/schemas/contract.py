from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

class ContractBase(BaseModel):
    customer_id: int
    contract_number: str
    title: str
    start_date: Optional[datetime] = None
    renewal_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    total_value: Optional[float] = None
    payment_terms: Optional[str] = None
    payment_frequency: Optional[str] = None

class ContractCreate(ContractBase):
    raw_text: Optional[str] = None
    file_path: Optional[str] = None

class ContractUpdate(BaseModel):
    title: Optional[str] = None
    renewal_date: Optional[datetime] = None
    payment_terms: Optional[str] = None
    total_value: Optional[float] = None
    status: Optional[str] = None

class ContractRead(ContractBase):
    id: int
    obligations: Optional[List[str]] = None
    status: str
    parsed_data: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class ContractUploadResponse(BaseModel):
    id: int
    message: str
    parsed_fields: Dict[str, Any]