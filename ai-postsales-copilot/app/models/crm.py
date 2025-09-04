from sqlalchemy import Column, Integer, String, DateTime, Float, JSON, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

class CRMRecord(Base):
    __tablename__ = "crm_records"
    
    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"))
    
    # CRM source
    source = Column(String)  # salesforce, hubspot
    source_id = Column(String, index=True)  # ID in source system
    
    # Unified fields
    account_name = Column(String)
    account_type = Column(String)
    industry = Column(String)
    annual_revenue = Column(Float)
    employee_count = Column(Integer)
    
    # Contact info
    primary_contact = Column(String)
    primary_email = Column(String)
    primary_phone = Column(String)
    
    # Sales data
    total_opportunities = Column(Integer)
    open_opportunities = Column(Integer)
    won_opportunities = Column(Integer)
    total_opportunity_value = Column(Float)
    
    # Activity
    last_activity_date = Column(DateTime)
    last_contact_date = Column(DateTime)
    
    # Raw data from CRM
    raw_data = Column(JSON)
    
    # Metadata
    synced_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    customer = relationship("Customer", back_populates="crm_records")