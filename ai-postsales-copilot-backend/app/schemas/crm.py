from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime

class CRMRecordRead(BaseModel):
    id: int
    customer_id: int
    source: str
    source_id: str
    account_name: Optional[str] = None
    industry: Optional[str] = None
    annual_revenue: Optional[float] = None
    total_opportunity_value: Optional[float] = None
    last_activity_date: Optional[datetime] = None
    synced_at: datetime
    
    class Config:
        from_attributes = True

class CRMSyncRequest(BaseModel):
    source: str  # salesforce or hubspot
    full_sync: bool = False

class DashboardSummary(BaseModel):
    total_contracts: int
    contracts_expiring_30_days: int
    contracts_expiring_60_days: int
    contracts_expiring_90_days: int
    total_contract_value: float
    payment_reminders: List[Dict[str, Any]]
    recent_activities: List[Dict[str, Any]]