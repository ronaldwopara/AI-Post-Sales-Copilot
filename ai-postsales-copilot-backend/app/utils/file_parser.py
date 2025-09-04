import PyPDF2
from docx import Document
import pandas as pd
from typing import Optional
import io

def parse_document(file_content: bytes, filename: str) -> str:
    """Parse various document formats and extract text"""
    text = ""
    
    if filename.lower().endswith('.pdf'):
        text = parse_pdf(file_content)
    elif filename.lower().endswith(('.docx', '.doc')):
        text = parse_docx(file_content)
    elif filename.lower().endswith(('.xlsx', '.xls')):
        text = parse_excel(file_content)
    elif filename.lower().endswith('.txt'):
        text = file_content.decode('utf-8', errors='ignore')
    
    return text

def parse_pdf(file_content: bytes) -> str:
    """Extract text from PDF"""
    try:
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_content))
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
        return text
    except Exception as e:
        print(f"Error parsing PDF: {e}")
        return ""

def parse_docx(file_content: bytes) -> str:
    """Extract text from DOCX"""
    try:
        doc = Document(io.BytesIO(file_content))
        text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
        return text
    except Exception as e:
        print(f"Error parsing DOCX: {e}")
        return ""

def parse_excel(file_content: bytes) -> str:
    """Extract text from Excel"""
    try:
        df = pd.read_excel(io.BytesIO(file_content))
        return df.to_string()
    except Exception as e:
        print(f"Error parsing Excel: {e}")
        return ""