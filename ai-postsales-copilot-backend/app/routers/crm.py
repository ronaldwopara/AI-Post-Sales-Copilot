from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.schemas.crm import CRMRecordRead, CRMSyncRequest
from app.services.crm_service import CRMService
from app.models import CRMRecord, Customer
from datetime import datetime

router = APIRouter(prefix="/api/crm", tags=["crm"])

@router.post("/sync")
async def sync_crm(
    request: CRMSyncRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Trigger CRM synchronization"""
    # Add to background tasks for async processing
    background_tasks.add_task(
        perform_crm_sync,
        request.source,
        request.full_sync,
        db
    )
    
    return {
        "message": f"CRM sync initiated for {request.source}",
        "status": "processing"
    }

def perform_crm_sync(source: str, full_sync: bool, db: Session):
    """Perform the actual CRM sync (background task)"""
    service = CRMService()
    
    try:
        if source == "all":
            results = service.sync_all()
            process_sync_results(results, db)
        elif source == "salesforce":
            results = service.salesforce_client.sync()
            process_salesforce_results(results, db)
        elif source == "hubspot":
            results = service.hubspot_client.sync()
            process_hubspot_results(results, db)
    except Exception as e:
        print(f"CRM sync error: {e}")

def process_sync_results(results: dict, db: Session):
    """Process and store sync results"""
    if results.get("salesforce"):
        process_salesforce_results(results["salesforce"], db)
    
    if results.get("hubspot"):
        process_hubspot_results(results["hubspot"], db)

def process_salesforce_results(data: dict, db: Session):
    """Process Salesforce sync results"""
    for account in data.get("accounts", []):
        # Check if customer exists
        customer = db.query(Customer).filter(
            Customer.name == account.get("Name")
        ).first()
        
        if not customer:
            customer = Customer(
                name=account.get("Name"),
                email=f"{account.get('Id')}@salesforce.com"  # Placeholder
            )
            db.add(customer)
            db.flush()
        
        # Create or update CRM record
        crm_record = db.query(CRMRecord).filter(
            CRMRecord.source == "salesforce",
            CRMRecord.source_id == account.get("Id")
        ).first()
        
        if not crm_record:
            crm_record = CRMRecord(
                customer_id=customer.id,
                source="salesforce",
                source_id=account.get("Id")
            )
            db.add(crm_record)
        
        # Update fields
        crm_record.account_name = account.get("Name")
        crm_record.industry = account.get("Industry")
        crm_record.annual_revenue = account.get("AnnualRevenue")
        crm_record.employee_count = account.get("NumberOfEmployees")
        crm_record.raw_data = account
        crm_record.synced_at = datetime.timezone.utc()
    
    db.commit()

def process_hubspot_results(data: dict, db: Session):
    """Process HubSpot sync results"""
    for company in data.get("companies", []):
        properties = company.get("properties", {})
        
        # Check if customer exists
        customer = db.query(Customer).filter(
            Customer.name == properties.get("name")
        ).first()
        
        if not customer:
            customer = Customer(
                name=properties.get("name"),
                email=f"{company.get('id')}@hubspot.com"  # Placeholder
            )
            db.add(customer)
            db.flush()
        
        # Create or update CRM record
        crm_record = db.query(CRMRecord).filter(
            CRMRecord.source == "hubspot",
            CRMRecord.source_id == str(company.get("id"))
        ).first()
        
        if not crm_record:
            crm_record = CRMRecord(
                customer_id=customer.id,
                source="hubspot",
                source_id=str(company.get("id"))
            )
            db.add(crm_record)
        
        # Update fields
        crm_record.account_name = properties.get("name")
        crm_record.industry = properties.get("industry")
        crm_record.annual_revenue = properties.get("annualrevenue")
        crm_record.employee_count = properties.get("numberofemployees")
        crm_record.raw_data = company
        crm_record.synced_at = datetime.utcnow()
    
    db.commit()

@router.get("/records", response_model=List[CRMRecordRead])
def list_crm_records(
    source: str = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """List CRM records with optional filtering"""
    query = db.query(CRMRecord)
    
    if source:
        query = query.filter(CRMRecord.source == source)
    
    records = query.offset(skip).limit(limit).all()
    return records

@router.get("/sync-status")
def get_sync_status(db: Session = Depends(get_db)):
    """Get CRM sync status and last sync times"""
    from sqlalchemy import func
    
    status = {}
    
    # Get last sync times for each source
    sources = ["salesforce", "hubspot"]
    for source in sources:
        last_sync = db.query(func.max(CRMRecord.synced_at)).filter(
            CRMRecord.source == source
        ).scalar()
        
        record_count = db.query(CRMRecord).filter(
            CRMRecord.source == source
        ).count()
        
        status[source] = {
            "last_sync": last_sync.isoformat() if last_sync else None,
            "record_count": record_count
        }
    
    return status