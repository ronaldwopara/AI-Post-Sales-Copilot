from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.crm import DashboardSummary
from app.services.dashboard_service import DashboardService

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])

@router.get("/summary", response_model=DashboardSummary)
def get_dashboard_summary(db: Session = Depends(get_db)):
    """Get dashboard summary with key metrics"""
    service = DashboardService(db)
    return service.get_summary()

@router.get("/renewal-forecast")
def get_renewal_forecast(
    months: int = 6,
    db: Session = Depends(get_db)
):
    """Get contract renewal forecast"""
    service = DashboardService(db)
    return service.get_renewal_forecast(months)

@router.get("/metrics")
def get_detailed_metrics(db: Session = Depends(get_db)):
    """Get detailed business metrics"""
    service = DashboardService(db)
    
    metrics = {
        "contracts": {
            "total_active": 0,
            "total_expired": 0,
            "avg_value": 0,
            "total_value": 0
        },
        "customers": {
            "total": 0,
            "with_active_contracts": 0,
            "top_by_value": []
        },
        "payments": {
            "upcoming_30_days": 0,
            "overdue": 0,
            "total_expected": 0
        }
    }
    
    # Calculate metrics
    from app.models import Contract, Customer
    from sqlalchemy import func
    
    # Contract metrics
    metrics["contracts"]["total_active"] = db.query(Contract).filter(
        Contract.status == "active"
    ).count()
    
    metrics["contracts"]["total_expired"] = db.query(Contract).filter(
        Contract.status == "expired"
    ).count()
    
    avg_value = db.query(func.avg(Contract.total_value)).filter(
        Contract.status == "active"
    ).scalar()
    metrics["contracts"]["avg_value"] = float(avg_value) if avg_value else 0
    
    total_value = db.query(func.sum(Contract.total_value)).filter(
        Contract.status == "active"
    ).scalar()
    metrics["contracts"]["total_value"] = float(total_value) if total_value else 0
    
    # Customer metrics
    metrics["customers"]["total"] = db.query(Customer).count()
    
    metrics["customers"]["with_active_contracts"] = db.query(Customer).join(
        Contract
    ).filter(Contract.status == "active").distinct().count()
    
    # Top customers by contract value
    top_customers = db.query(
        Customer.name,
        func.sum(Contract.total_value).label("total_value")
    ).join(Contract).filter(
        Contract.status == "active"
    ).group_by(Customer.id, Customer.name).order_by(
        func.sum(Contract.total_value).desc()
    ).limit(5).all()
    
    metrics["customers"]["top_by_value"] = [
        {"name": name, "value": float(value) if value else 0}
        for name, value in top_customers
    ]
    
    return metrics