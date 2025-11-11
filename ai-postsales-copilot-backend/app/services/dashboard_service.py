from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from datetime import datetime, timedelta
from typing import Dict, List, Any
from app.models import Contract, Customer, CRMRecord
from app.schemas.crm import DashboardSummary

class DashboardService:
    def __init__(self, db: Session):
        self.db = db
    
    def get_summary(self) -> DashboardSummary:
        """Get dashboard summary data"""
        now = datetime.utcnow()
        
        # Total contracts
        total_contracts = self.db.query(Contract).filter(
            Contract.status == "active"
        ).count()
        
        # Contracts expiring soon
        contracts_30 = self._get_expiring_contracts(30)
        contracts_60 = self._get_expiring_contracts(60)
        contracts_90 = self._get_expiring_contracts(90)
        
        # Total contract value
        total_value = self.db.query(Contract).filter(
            Contract.status == "active"
        ).with_entities(
            func.sum(Contract.total_value)
        ).scalar() or 0.0
        
        # Payment reminders
        payment_reminders = self._get_payment_reminders()
        
        # Recent activities
        recent_activities = self._get_recent_activities()
        
        return DashboardSummary(
            total_contracts=total_contracts,
            contracts_expiring_30_days=len(contracts_30),
            contracts_expiring_60_days=len(contracts_60),
            contracts_expiring_90_days=len(contracts_90),
            total_contract_value=total_value,
            payment_reminders=payment_reminders,
            recent_activities=recent_activities
        )
    
    def _get_expiring_contracts(self, days: int) -> List[Contract]:
        """Get contracts expiring within specified days"""
        now = datetime.utcnow()
        future_date = now + timedelta(days=days)
        
        return self.db.query(Contract).filter(
            and_(
                Contract.renewal_date >= now,
                Contract.renewal_date <= future_date,
                Contract.status == "active"
            )
        ).all()
    
    def _get_payment_reminders(self) -> List[Dict[str, Any]]:
        """Get upcoming payment reminders"""
        reminders = []
        
        # Get contracts with payment terms
        contracts = self.db.query(Contract).filter(
            and_(
                Contract.status == "active",
                Contract.payment_terms.isnot(None)
            )
        ).all()
        
        for contract in contracts:
            # Parse payment terms and calculate next payment
            if contract.payment_frequency == "monthly":
                next_payment = datetime.utcnow() + timedelta(days=30)
            elif contract.payment_frequency == "quarterly":
                next_payment = datetime.utcnow() + timedelta(days=90)
            elif contract.payment_frequency == "annually":
                next_payment = datetime.utcnow() + timedelta(days=365)
            else:
                continue
            
            reminders.append({
                "contract_id": contract.id,
                "contract_number": contract.contract_number,
                "customer_id": contract.customer_id,
                "next_payment_date": next_payment.isoformat(),
                "amount": contract.total_value,
                "payment_terms": contract.payment_terms
            })
        
        # Sort by next payment date
        reminders.sort(key=lambda x: x["next_payment_date"])
        return reminders[:10]  # Return top 10
    
    def _get_recent_activities(self) -> List[Dict[str, Any]]:
        """Get recent CRM activities"""
        activities = []
        
        # Get recent CRM syncs
        recent_crm = self.db.query(CRMRecord).order_by(
            CRMRecord.synced_at.desc()
        ).limit(5).all()
        
        for record in recent_crm:
            activities.append({
                "type": "crm_sync",
                "source": record.source,
                "account_name": record.account_name,
                "timestamp": record.synced_at.isoformat(),
                "details": f"Synced from {record.source}"
            })
        
        # Get recently added contracts
        recent_contracts = self.db.query(Contract).order_by(
            Contract.created_at.desc()
        ).limit(5).all()
        
        for contract in recent_contracts:
            activities.append({
                "type": "contract_added",
                "contract_number": contract.contract_number,
                "timestamp": contract.created_at.isoformat(),
                "details": f"New contract: {contract.title}"
            })
        
        # Sort by timestamp
        activities.sort(key=lambda x: x["timestamp"], reverse=True)
        return activities[:10]
    
    def get_renewal_forecast(self, months: int = 6) -> Dict[str, Any]:
        """Get renewal forecast for next N months"""
        now = datetime.utcnow()
        future_date = now + timedelta(days=months * 30)
        
        contracts = self.db.query(Contract).filter(
            and_(
                Contract.renewal_date >= now,
                Contract.renewal_date <= future_date,
                Contract.status == "active"
            )
        ).all()
        
        # Group by month
        forecast = {}
        for contract in contracts:
            month_key = contract.renewal_date.strftime("%Y-%m")
            if month_key not in forecast:
                forecast[month_key] = {
                    "count": 0,
                    "total_value": 0.0,
                    "contracts": []
                }
            
            forecast[month_key]["count"] += 1
            forecast[month_key]["total_value"] += contract.total_value or 0
            forecast[month_key]["contracts"].append({
                "id": contract.id,
                "number": contract.contract_number,
                "value": contract.total_value
            })
        
        return forecast