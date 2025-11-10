from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models import Contract, Customer
from app.schemas import ContractCreate, ContractRead, ContractUpdate, ContractUploadResponse
from app.services.nlp_service import NLPService
from app.utils.file_parser import parse_document
from datetime import datetime

router = APIRouter(prefix="/api/contracts", tags=["contracts"])

@router.post("/upload", response_model=ContractUploadResponse)
async def upload_contract(
    file: UploadFile = File(...),
    customer_id: int = None,
    db: Session = Depends(get_db)
):
    """Upload and parse a contract file"""
    # Read file content
    content = await file.read()
    
    # Parse document to extract text
    text = parse_document(content, file.filename)
    
    if not text:
        raise HTTPException(status_code=400, detail="Could not extract text from file")
    
    # Use NLP to extract fields
    nlp_service = NLPService()
    extracted_fields = nlp_service.extract_contract_fields(text)
    
    # Create contract record
    contract = Contract(
        customer_id=customer_id,
        contract_number=f"CNT-{datetime.timezone.utc().strftime('%Y%m%d%H%M%S')}",
        title=file.filename,
        raw_text=text,
        file_path=file.filename,
        parsed_data=extracted_fields,
        obligations=extracted_fields.get("obligations", []),
        payment_terms=extracted_fields.get("payment_terms"),
        total_value=extracted_fields.get("total_value"),
        status="active"
    )
    
    # Parse renewal date if found
    if extracted_fields.get("renewal_date"):
        try:
            contract.renewal_date = datetime.fromisoformat(extracted_fields["renewal_date"])
        except:
            pass
    
    db.add(contract)
    db.commit()
    db.refresh(contract)
    
    return ContractUploadResponse(
        id=contract.id,
        message="Contract uploaded and parsed successfully",
        parsed_fields=extracted_fields
    )

@router.get("/", response_model=List[ContractRead])
def list_contracts(
    skip: int = 0,
    limit: int = 100,
    status: str = None,
    db: Session = Depends(get_db)
):
    """List all contracts with optional filtering"""
    query = db.query(Contract)
    
    if status:
        query = query.filter(Contract.status == status)
    
    contracts = query.offset(skip).limit(limit).all()
    return contracts

@router.get("/{contract_id}", response_model=ContractRead)
def get_contract(contract_id: int, db: Session = Depends(get_db)):
    """Get a single contract by ID"""
    contract = db.query(Contract).filter(Contract.id == contract_id).first()
    
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")
    
    return contract

@router.put("/{contract_id}", response_model=ContractRead)
def update_contract(
    contract_id: int,
    contract_update: ContractUpdate,
    db: Session = Depends(get_db)
):
    """Update contract details"""
    contract = db.query(Contract).filter(Contract.id == contract_id).first()
    
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")
    
    update_data = contract_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(contract, field, value)
    
    contract.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(contract)
    
    return contract

@router.delete("/{contract_id}")
def delete_contract(contract_id: int, db: Session = Depends(get_db)):
    """Delete a contract"""
    contract = db.query(Contract).filter(Contract.id == contract_id).first()
    
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")
    
    db.delete(contract)
    db.commit()
    
    return {"message": "Contract deleted successfully"}

@router.post("/{contract_id}/reparse")
def reparse_contract(contract_id: int, db: Session = Depends(get_db)):
    """Re-parse an existing contract"""
    contract = db.query(Contract).filter(Contract.id == contract_id).first()
    
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")
    
    if not contract.raw_text:
        raise HTTPException(status_code=400, detail="No text available for parsing")
    
    # Re-run NLP extraction
    nlp_service = NLPService()
    extracted_fields = nlp_service.extract_contract_fields(contract.raw_text)
    
    # Update contract with new parsed data
    contract.parsed_data = extracted_fields
    contract.obligations = extracted_fields.get("obligations", [])
    contract.payment_terms = extracted_fields.get("payment_terms")
    contract.total_value = extracted_fields.get("total_value")
    
    if extracted_fields.get("renewal_date"):
        try:
            contract.renewal_date = datetime.fromisoformat(extracted_fields["renewal_date"])
        except:
            pass
    
    contract.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(contract)
    
    return {
        "message": "Contract re-parsed successfully",
        "parsed_fields": extracted_fields
    }