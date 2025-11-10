"""
Resume Anonymization Service - Remove PII from resumes for unbiased screening

This service provides on-demand anonymization of resumes:
- Downloads original PDF from S3 (never modifies the original)
- Removes personal information (name, email, phone, LinkedIn, GitHub)
- Returns anonymized PDF without storing it
- Controlled by admin toggle per company
"""

import os
import re
import logging
import tempfile
from typing import Optional, List, Tuple, BinaryIO
from io import BytesIO
import fitz  # PyMuPDF for better text extraction and redaction

logger = logging.getLogger(__name__)


class ResumeAnonymizationService:
    """Service for anonymizing resumes by removing personal information (on-demand)"""
    
    def __init__(self):
        self.anonymization_enabled = True
        self.temp_dir = tempfile.gettempdir()
    
    def anonymize_resume_from_file(
        self,
        input_pdf_path: str,
        full_name: str,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        linkedin_url: Optional[str] = None,
        github_url: Optional[str] = None
    ) -> bytes:
        """
        Anonymize a PDF resume and return as bytes (in-memory, no file storage)
        
        Args:
            input_pdf_path: Path to original PDF (can be temp file from S3)
            full_name: Full name of candidate (as registered)
            email: Email to redact (optional)
            phone: Phone to redact (optional)
            linkedin_url: LinkedIn URL to redact (optional)
            github_url: GitHub URL to redact (optional)
            
        Returns:
            Anonymized PDF as bytes
        """
        try:
            logger.info(f"🔒 Starting on-demand resume anonymization for: {full_name}")
            
            # Open PDF with PyMuPDF
            doc = fitz.open(input_pdf_path)
            
            # Build list of exact text patterns to redact (no replacement text)
            redaction_patterns = self._build_redaction_patterns(
                full_name=full_name,
                email=email,
                phone=phone,
                linkedin_url=linkedin_url,
                github_url=github_url
            )
            
            total_redactions = 0
            
            # Process each page
            for page_num in range(len(doc)):
                page = doc[page_num]
                
                # Step 1: Redact exact pattern matches
                for pattern in redaction_patterns:
                    # Search for exact text instances (case-sensitive for better accuracy)
                    text_instances = page.search_for(pattern)
                    
                    if text_instances:
                        logger.info(f"📍 Found {len(text_instances)} instances of '{pattern}' on page {page_num + 1}")
                        
                        for inst in text_instances:
                            # Add black redaction box (no text replacement)
                            page.add_redact_annot(inst, fill=(0, 0, 0))  # Black box
                            total_redactions += 1
                
                # Redact common identity-revealing keywords
                identity_keywords = ["Portfolio", "PORTFOLIO"]
                for keyword in identity_keywords:
                    keyword_instances = page.search_for(keyword)
                    for inst in keyword_instances:
                        page.add_redact_annot(inst, fill=(0, 0, 0))
                        total_redactions += 1
                        logger.info(f"📝 Redacted keyword: {keyword}")
                
                # Step 2: Redact URLs and email patterns using regex
                page_text = page.get_text("text")
                
                # Find and redact email addresses (any @domain.com pattern)
                email_pattern = r'\b[\w\.-]+@[\w\.-]+\.\w{2,}\b'
                for match in re.finditer(email_pattern, page_text):
                    email_found = match.group()
                    instances = page.search_for(email_found)
                    for inst in instances:
                        page.add_redact_annot(inst, fill=(0, 0, 0))
                        total_redactions += 1
                        logger.info(f"📧 Redacted email: {email_found[:3]}***")
                
                # Find and redact LinkedIn URLs
                linkedin_pattern = r'(?:https?://)?(?:www\.)?linkedin\.com/in/[\w-]+'
                for match in re.finditer(linkedin_pattern, page_text, re.IGNORECASE):
                    url_found = match.group()
                    instances = page.search_for(url_found)
                    for inst in instances:
                        page.add_redact_annot(inst, fill=(0, 0, 0))
                        total_redactions += 1
                        logger.info(f"🔗 Redacted LinkedIn URL")
                
                # Find and redact GitHub URLs (ALL GitHub links - profile AND projects)
                github_pattern = r'(?:https?://)?(?:www\.)?github\.com/[\w-]+(?:/[\w-]+)*'
                for match in re.finditer(github_pattern, page_text, re.IGNORECASE):
                    url_found = match.group()
                    instances = page.search_for(url_found.rstrip('/'))
                    for inst in instances:
                        page.add_redact_annot(inst, fill=(0, 0, 0))
                        total_redactions += 1
                        logger.info(f"🔗 Redacted GitHub URL: {url_found[:30]}...")
                
                # Find and redact phone numbers (various formats)
                phone_patterns = [
                    r'\+?\d{1,3}[-.\s]?\(?\d{1,4}\)?[-.\s]?\d{1,4}[-.\s]?\d{1,9}',  # International
                    r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',  # US format
                    r'\d{3}[-.\s]?\d{3}[-.\s]?\d{4}',  # 123-456-7890
                ]
                
                for pattern in phone_patterns:
                    for match in re.finditer(pattern, page_text):
                        phone_found = match.group()
                        digit_count = sum(c.isdigit() for c in phone_found)
                        if digit_count >= 10:
                            instances = page.search_for(phone_found)
                            for inst in instances:
                                page.add_redact_annot(inst, fill=(0, 0, 0))
                                total_redactions += 1
                                logger.info(f"📞 Redacted phone number")
                
                # Step 3: Remove ALL clickable links (make entire resume unclickable)
                links = page.get_links()
                for link in links:
                    # Delete all hyperlinks to make them unclickable
                    # This removes the clickable functionality but keeps the text visible
                    page.delete_link(link)
                    logger.info(f"🔓 Removed clickable link functionality")
                
                # Apply all redactions on this page
                page.apply_redactions()
            
            # Save to bytes in memory (no file storage)
            pdf_bytes = doc.tobytes(garbage=4, deflate=True, clean=True)
            doc.close()
            
            logger.info(f"✅ Resume anonymized successfully! Total redactions: {total_redactions}")
            
            return pdf_bytes
            
        except Exception as e:
            logger.error(f"  Anonymization failed: {str(e)}")
            raise Exception(f"Failed to anonymize resume: {str(e)}")
    
    def _build_redaction_patterns(
        self,
        full_name: str,
        email: Optional[str],
        phone: Optional[str],
        linkedin_url: Optional[str],
        github_url: Optional[str]
    ) -> List[str]:
        """
        Build list of EXACT text strings to redact
        
        Returns:
            List of exact text strings to find and redact with black boxes
        """
        patterns = []
        
        # Full name - only exact matches to avoid false positives
        if full_name:
            patterns.append(full_name)
            
            # Try common name variations
            name_parts = full_name.split()
            if len(name_parts) >= 2:
                # Reversed format: "Last, First"
                reversed_name = f"{name_parts[-1]}, {' '.join(name_parts[:-1])}"
                patterns.append(reversed_name)
        
        # Email - exact match only
        if email:
            patterns.append(email)
            # Try lowercase version
            if email != email.lower():
                patterns.append(email.lower())
        
        # Phone - exact match only
        if phone:
            patterns.append(phone)
        
        # LinkedIn URL - exact match
        if linkedin_url:
            patterns.append(linkedin_url)
            # Try without protocol
            url_without_protocol = linkedin_url.replace("https://", "").replace("http://", "")
            if url_without_protocol != linkedin_url:
                patterns.append(url_without_protocol)
        
        # GitHub URL - exact match
        if github_url:
            patterns.append(github_url)
            # Try without protocol
            url_without_protocol = github_url.replace("https://", "").replace("http://", "")
            if url_without_protocol != github_url:
                patterns.append(url_without_protocol)
        
        return patterns
    
    def verify_anonymization(
        self,
        pdf_path: str,
        full_name: str,
        email: Optional[str] = None
    ) -> dict:
        """
        Verify that PII has been removed from PDF
        
        Args:
            pdf_path: Path to anonymized PDF
            full_name: Name that should be removed
            email: Email that should be removed
            
        Returns:
            Dictionary with verification results
        """
        try:
            doc = fitz.open(pdf_path)
            
            found_pii = {
                "name_found": False,
                "email_found": False,
                "pages_with_pii": [],
                "is_anonymized": True
            }
            
            for page_num in range(len(doc)):
                page = doc[page_num]
                text = page.get_text().lower()
                
                # Check for name
                if full_name.lower() in text:
                    found_pii["name_found"] = True
                    found_pii["is_anonymized"] = False
                    found_pii["pages_with_pii"].append(page_num + 1)
                
                # Check for email
                if email and email.lower() in text:
                    found_pii["email_found"] = True
                    found_pii["is_anonymized"] = False
                    if page_num + 1 not in found_pii["pages_with_pii"]:
                        found_pii["pages_with_pii"].append(page_num + 1)
            
            doc.close()
            
            if found_pii["is_anonymized"]:
                logger.info("✅ Verification passed - No PII found in anonymized PDF")
            else:
                logger.warning(f"⚠️ Verification failed - PII found on pages: {found_pii['pages_with_pii']}")
            
            return found_pii
            
        except Exception as e:
            logger.error(f"  Verification failed: {str(e)}")
            return {
                "error": str(e),
                "is_anonymized": False
            }


# Singleton instance
anonymization_service = ResumeAnonymizationService()
