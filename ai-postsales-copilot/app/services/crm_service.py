import requests
import pandas as pd
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from app.config import settings
import json

class CRMService:
    def __init__(self):
        self.salesforce_client = SalesforceClient()
        self.hubspot_client = HubSpotClient()
    
    def sync_all(self) -> Dict[str, Any]:
        """Sync data from all CRM sources"""
        results = {
            "salesforce": None,
            "hubspot": None,
            "errors": []
        }
        
        # Sync Salesforce
        try:
            results["salesforce"] = self.salesforce_client.sync()
        except Exception as e:
            results["errors"].append(f"Salesforce sync error: {str(e)}")
        
        # Sync HubSpot
        try:
            results["hubspot"] = self.hubspot_client.sync()
        except Exception as e:
            results["errors"].append(f"HubSpot sync error: {str(e)}")
        
        return results
    
    def unify_customer_data(self, salesforce_data: Dict, hubspot_data: Dict) -> Dict:
        """Unify customer data from different CRM sources"""
        unified = {
            "account_name": salesforce_data.get("Name") or hubspot_data.get("name"),
            "industry": salesforce_data.get("Industry") or hubspot_data.get("industry"),
            "annual_revenue": salesforce_data.get("AnnualRevenue") or hubspot_data.get("annualrevenue"),
            "employee_count": salesforce_data.get("NumberOfEmployees") or hubspot_data.get("numberofemployees"),
            "primary_contact": salesforce_data.get("PrimaryContact") or hubspot_data.get("primary_contact"),
            "primary_email": salesforce_data.get("Email") or hubspot_data.get("email"),
            "last_activity_date": self._parse_date(
                salesforce_data.get("LastActivityDate") or hubspot_data.get("notes_last_updated")
            )
        }
        
        return unified
    
    def _parse_date(self, date_str: Any) -> Optional[datetime]:
        """Parse date from various formats"""
        if not date_str:
            return None
        
        if isinstance(date_str, datetime):
            return date_str
        
        try:
            # Try ISO format first
            return datetime.fromisoformat(str(date_str).replace('Z', '+00:00'))
        except:
            try:
                # Try common formats
                return datetime.strptime(str(date_str), '%Y-%m-%d')
            except:
                return None


class SalesforceClient:
    def __init__(self):
        self.client_id = settings.salesforce_client_id
        self.client_secret = settings.salesforce_client_secret
        self.username = settings.salesforce_username
        self.password = settings.salesforce_password
        self.security_token = settings.salesforce_security_token
        self.access_token = None
        self.instance_url = None
    
    def authenticate(self):
        """Authenticate with Salesforce"""
        if not all([self.client_id, self.client_secret, self.username, self.password]):
            raise ValueError("Salesforce credentials not configured")
        
        auth_url = "https://login.salesforce.com/services/oauth2/token"
        
        data = {
            'grant_type': 'password',
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'username': self.username,
            'password': f"{self.password}{self.security_token or ''}"
        }
        
        response = requests.post(auth_url, data=data)
        if response.status_code == 200:
            auth_data = response.json()
            self.access_token = auth_data['access_token']
            self.instance_url = auth_data['instance_url']
        else:
            raise Exception(f"Salesforce authentication failed: {response.text}")
    
    def sync(self) -> Dict[str, Any]:
        """Sync Salesforce data"""
        if not self.access_token:
            self.authenticate()
        
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
        
        results = {
            "accounts": [],
            "opportunities": [],
            "contacts": []
        }
        
        # Fetch Accounts
        query = "SELECT Id, Name, Industry, AnnualRevenue, NumberOfEmployees FROM Account LIMIT 100"
        response = self._query(query, headers)
        if response:
            results["accounts"] = response.get("records", [])
        
        # Fetch Opportunities
        query = "SELECT Id, Name, Amount, StageName, CloseDate FROM Opportunity WHERE CloseDate > LAST_N_DAYS:90"
        response = self._query(query, headers)
        if response:
            results["opportunities"] = response.get("records", [])
        
        # Fetch Contacts
        query = "SELECT Id, FirstName, LastName, Email, Phone FROM Contact LIMIT 100"
        response = self._query(query, headers)
        if response:
            results["contacts"] = response.get("records", [])
        
        return results
    
    def _query(self, soql: str, headers: Dict) -> Optional[Dict]:
        """Execute SOQL query"""
        try:
            url = f"{self.instance_url}/services/data/v59.0/query"
            params = {'q': soql}
            response = requests.get(url, headers=headers, params=params)
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Query failed: {response.text}")
                return None
        except Exception as e:
            print(f"Query error: {e}")
            return None


class HubSpotClient:
    def __init__(self):
        self.api_key = settings.hubspot_api_key
        self.base_url = "https://api.hubapi.com"
    
    def sync(self) -> Dict[str, Any]:
        """Sync HubSpot data"""
        if not self.api_key:
            raise ValueError("HubSpot API key not configured")
        
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        
        results = {
            "companies": [],
            "deals": [],
            "contacts": []
        }
        
        # Fetch Companies
        companies = self._fetch_companies(headers)
        if companies:
            results["companies"] = companies
        
        # Fetch Deals
        deals = self._fetch_deals(headers)
        if deals:
            results["deals"] = deals
        
        # Fetch Contacts
        contacts = self._fetch_contacts(headers)
        if contacts:
            results["contacts"] = contacts
        
        return results
    
    def _fetch_companies(self, headers: Dict) -> List[Dict]:
        """Fetch companies from HubSpot"""
        try:
            url = f"{self.base_url}/crm/v3/objects/companies"
            params = {
                'limit': 100,
                'properties': 'name,industry,annualrevenue,numberofemployees'
            }
            
            response = requests.get(url, headers=headers, params=params)
            if response.status_code == 200:
                return response.json().get('results', [])
            else:
                print(f"Failed to fetch companies: {response.text}")
                return []
        except Exception as e:
            print(f"Error fetching companies: {e}")
            return []
    
    def _fetch_deals(self, headers: Dict) -> List[Dict]:
        """Fetch deals from HubSpot"""
        try:
            url = f"{self.base_url}/crm/v3/objects/deals"
            params = {
                'limit': 100,
                'properties': 'dealname,amount,dealstage,closedate'
            }
            
            response = requests.get(url, headers=headers, params=params)
            if response.status_code == 200:
                return response.json().get('results', [])
            else:
                print(f"Failed to fetch deals: {response.text}")
                return []
        except Exception as e:
            print(f"Error fetching deals: {e}")
            return []
    
    def _fetch_contacts(self, headers: Dict) -> List[Dict]:
        """Fetch contacts from HubSpot"""
        try:
            url = f"{self.base_url}/crm/v3/objects/contacts"
            params = {
                'limit': 100,
                'properties': 'firstname,lastname,email,phone'
            }
            
            response = requests.get(url, headers=headers, params=params)
            if response.status_code == 200:
                return response.json().get('results', [])
            else:
                print(f"Failed to fetch contacts: {response.text}")
                return []
        except Exception as e:
            print(f"Error fetching contacts: {e}")
            return []