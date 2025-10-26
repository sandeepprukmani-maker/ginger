import os
import requests
from PyPDF2 import PdfReader
from docx import Document
import tempfile

class DocumentProcessor:
    def __init__(self):
        pass
    
    def process_attachment(self, attachment_url, filename, auth):
        """Process document attachments and extract text"""
        try:
            file_extension = os.path.splitext(filename)[1].lower()
            
            response = requests.get(attachment_url, auth=auth)
            response.raise_for_status()
            
            with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as tmp_file:
                tmp_file.write(response.content)
                tmp_path = tmp_file.name
            
            try:
                if file_extension == '.pdf':
                    text = self._extract_pdf_text(tmp_path)
                elif file_extension in ['.docx', '.doc']:
                    text = self._extract_docx_text(tmp_path)
                elif file_extension == '.txt':
                    text = self._extract_txt_text(tmp_path)
                else:
                    text = f"[Unsupported file type: {file_extension}]"
                
                return text
            finally:
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)
                    
        except Exception as e:
            return f"[Error processing {filename}: {str(e)}]"
    
    def _extract_pdf_text(self, file_path):
        """Extract text from PDF files"""
        try:
            reader = PdfReader(file_path)
            text_parts = []
            
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    text_parts.append(text)
            
            return '\n\n'.join(text_parts)
        except Exception as e:
            return f"[Error extracting PDF: {str(e)}]"
    
    def _extract_docx_text(self, file_path):
        """Extract text from DOCX files"""
        try:
            doc = Document(file_path)
            text_parts = []
            
            for paragraph in doc.paragraphs:
                if paragraph.text.strip():
                    text_parts.append(paragraph.text)
            
            for table in doc.tables:
                for row in table.rows:
                    for cell in row.cells:
                        if cell.text.strip():
                            text_parts.append(cell.text)
            
            return '\n\n'.join(text_parts)
        except Exception as e:
            return f"[Error extracting DOCX: {str(e)}]"
    
    def _extract_txt_text(self, file_path):
        """Extract text from TXT files"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read()
        except Exception as e:
            return f"[Error extracting TXT: {str(e)}]"
