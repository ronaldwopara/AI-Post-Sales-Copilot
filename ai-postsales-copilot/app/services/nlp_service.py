import re
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
import spacy
from transformers import pipeline

class NLPService:
    def __init__(self):
        # Load spaCy model (install with: python -m spacy download en_core_web_sm)
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except:
            print("SpaCy model not found. Install with: python -m spacy download en_core_web_sm")
            self.nlp = None
        
        # Initialize transformer pipeline for advanced NER (optional)
        try:
            self.ner_pipeline = pipeline("ner", model="dslim/bert-base-NER")
        except:
            print("Transformer model not available")
            self.ner_pipeline = None
    
    def extract_contract_fields(self, text: str) -> Dict[str, Any]:
        """Extract key fields from contract text"""
        result = {
            "renewal_date": self.extract_renewal_date(text),
            "payment_terms": self.extract_payment_terms(text),
            "obligations": self.extract_obligations(text),
            "total_value": self.extract_contract_value(text),
            "parties": self.extract_parties(text),
            "key_dates": self.extract_all_dates(text)
        }
        
        return result
    
    def extract_renewal_date(self, text: str) -> Optional[str]:
        """Extract renewal date from contract text"""
        patterns = [
            r'renew(?:al|s)?\s+(?:date|on|by)[\s:]+(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            r'expires?\s+(?:on|by)[\s:]+(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            r'term\s+ends?\s+(?:on|by)[\s:]+(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\s+renewal',
            r'automatically\s+renew(?:s|ed)?\s+on\s+(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})'
        ]
        
        text_lower = text.lower()
        for pattern in patterns:
            match = re.search(pattern, text_lower)
            if match:
                date_str = match.group(1)
                return self.normalize_date(date_str)
        
        return None
    
    def extract_payment_terms(self, text: str) -> Optional[str]:
        """Extract payment terms from contract"""
        patterns = [
            r'payment\s+terms?[\s:]+([^\n.]+)',
            r'net\s+(\d+)\s+days?',
            r'payment\s+due\s+([^\n.]+)',
            r'(monthly|quarterly|annually|yearly)\s+payment',
            r'payment\s+(monthly|quarterly|annually|yearly)',
            r'(\d+)\s+days?\s+after\s+invoice'
        ]
        
        text_lower = text.lower()
        for pattern in patterns:
            match = re.search(pattern, text_lower)
            if match:
                return match.group(1).strip()
        
        return None
    
    def extract_obligations(self, text: str) -> List[str]:
        """Extract customer obligations from contract"""
        obligations = []
        
        # Keywords that typically precede obligations
        obligation_keywords = [
            "shall", "must", "will", "agrees to", "commits to",
            "is responsible for", "undertakes to", "obligated to"
        ]
        
        sentences = text.split('.')
        for sentence in sentences:
            sentence_lower = sentence.lower()
            for keyword in obligation_keywords:
                if keyword in sentence_lower:
                    # Clean and add the obligation
                    obligation = sentence.strip()
                    if len(obligation) > 10 and len(obligation) < 500:
                        obligations.append(obligation)
                    break
        
        # Deduplicate while preserving order
        seen = set()
        unique_obligations = []
        for item in obligations:
            if item not in seen:
                seen.add(item)
                unique_obligations.append(item)
        
        return unique_obligations[:10]  # Limit to top 10 obligations
    
    def extract_contract_value(self, text: str) -> Optional[float]:
        """Extract contract value/amount"""
        patterns = [
            r'\$\s*([0-9,]+(?:\.[0-9]{2})?)',
            r'USD\s*([0-9,]+(?:\.[0-9]{2})?)',
            r'total\s+(?:value|amount|price)[\s:]+\$?\s*([0-9,]+(?:\.[0-9]{2})?)',
            r'contract\s+(?:value|amount|price)[\s:]+\$?\s*([0-9,]+(?:\.[0-9]{2})?)'
        ]
        
        text_lower = text.lower()
        for pattern in patterns:
            matches = re.findall(pattern, text_lower)
            if matches:
                # Get the largest amount (likely the total)
                amounts = []
                for match in matches:
                    try:
                        amount = float(match.replace(',', ''))
                        amounts.append(amount)
                    except:
                        continue
                if amounts:
                    return max(amounts)
        
        return None
    
    def extract_parties(self, text: str) -> List[str]:
        """Extract parties involved in the contract"""
        parties = []
        
        if self.nlp:
            doc = self.nlp(text[:5000])  # Process first 5000 chars
            for ent in doc.ents:
                if ent.label_ in ["ORG", "PERSON"]:
                    parties.append(ent.text)
        
        # Also look for common patterns
        patterns = [
            r'between\s+([A-Z][A-Za-z\s&,]+)\s+and',
            r'PARTIES:\s*([^\n]+)',
            r'"([A-Z][A-Za-z\s&,]+)"\s+\(.*Company\)'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text)
            parties.extend(matches)
        
        # Deduplicate
        return list(set(parties))[:5]
    
    def extract_all_dates(self, text: str) -> List[Dict[str, str]]:
        """Extract all dates from the contract"""
        dates = []
        
        # Common date patterns
        date_patterns = [
            r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            r'(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{2,4})',
            r'((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s+\d{2,4})'
        ]
        
        for pattern in date_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                date_str = match.group(1)
                # Get context (20 chars before and after)
                start = max(0, match.start() - 20)
                end = min(len(text), match.end() + 20)
                context = text[start:end].replace('\n', ' ')
                
                dates.append({
                    "date": self.normalize_date(date_str),
                    "context": context,
                    "original": date_str
                })
        
        return dates[:10]  # Limit to 10 dates
    
    def normalize_date(self, date_str: str) -> Optional[str]:
        """Normalize date string to ISO format"""
        try:
            # Try various date formats
            formats = [
                '%m/%d/%Y', '%m-%d-%Y', '%Y-%m-%d',
                '%m/%d/%y', '%m-%d-%y',
                '%B %d, %Y', '%b %d, %Y',
                '%d %B %Y', '%d %b %Y'
            ]
            
            for fmt in formats:
                try:
                    dt = datetime.strptime(date_str.strip(), fmt)
                    return dt.strftime('%Y-%m-%d')
                except:
                    continue
            
            return date_str  # Return original if can't parse
        except:
            return None 