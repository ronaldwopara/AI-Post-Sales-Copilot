from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Float, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

class Contract(Base):
    __tablename__ = "contracts"
    
    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"))
    contract_number = Column(String, unique=True, index=True)
    title = Column(String)
    
    # Key contract fields
    start_date = Column(DateTime)
    renewal_date = Column(DateTime, index=True)
    end_date = Column(DateTime)
    
    # Financial
    total_value = Column(Float)
    payment_terms = Column(String)
    payment_frequency = Column(String)  # monthly, quarterly, annually
    
    # Contract details
    obligations = Column(JSON)  # List of obligations
    raw_text = Column(Text)
    file_path = Column(String)
    
    # Metadata
    status = Column(String, default="active")  # active, expired, renewed
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Parsed data
    parsed_data = Column(JSON)  # Store NLP extraction results
    
    # Relationships
    customer = relationship("Customer", back_populates="contracts")