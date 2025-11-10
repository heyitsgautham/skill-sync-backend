"""
S3 Service - Cloud storage for resume files
"""

import os
import boto3
from botocore.exceptions import ClientError
from typing import Optional
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class S3Service:
    """Service for managing resume uploads to AWS S3"""
    
    def __init__(self):
        self.aws_access_key_id = os.getenv("AWS_ACCESS_KEY_ID")
        self.aws_secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY")
        self.aws_region = os.getenv("AWS_REGION", "us-east-1")
        self.bucket_name = os.getenv("AWS_S3_BUCKET_NAME")
        
        if not all([self.aws_access_key_id, self.aws_secret_access_key, self.bucket_name]):
            logger.warning("⚠️ AWS S3 credentials not configured. Resume storage will use local filesystem.")
            self.s3_client = None
            self.enabled = False
        else:
            try:
                from botocore.client import Config
                # Force signature version 4 and set region explicitly
                self.s3_client = boto3.client(
                    's3',
                    aws_access_key_id=self.aws_access_key_id,
                    aws_secret_access_key=self.aws_secret_access_key,
                    region_name=self.aws_region,
                    config=Config(
                        signature_version='s3v4',
                        region_name=self.aws_region
                    )
                )
                self.enabled = True
                logger.info("✅ S3 Service initialized successfully")
            except Exception as e:
                logger.error(f"  Failed to initialize S3 client: {str(e)}")
                self.s3_client = None
                self.enabled = False
    
    def is_enabled(self) -> bool:
        """Check if S3 storage is enabled"""
        return self.enabled
    
    def upload_resume(
        self,
        file_path: str,
        student_id: int,
        file_name: str,
        is_tailored: bool = False,
        internship_id: Optional[int] = None
    ) -> Optional[str]:
        """
        Upload resume to S3
        
        Args:
            file_path: Local file path
            student_id: ID of the student
            file_name: Original filename
            is_tailored: Whether this is a tailored resume
            internship_id: ID of internship if tailored
            
        Returns:
            S3 key if successful, None otherwise
        """
        if not self.enabled:
            logger.warning("S3 not enabled, skipping upload")
            return None
        
        try:
            # Generate S3 key with organized folder structure
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            if is_tailored and internship_id:
                s3_key = f"resumes/{student_id}/tailored/{internship_id}/{timestamp}_{file_name}"
            else:
                s3_key = f"resumes/{student_id}/base/{timestamp}_{file_name}"
            
            # Upload file
            logger.info(f"📤 Uploading to S3: {s3_key}")
            with open(file_path, 'rb') as file_data:
                self.s3_client.upload_fileobj(
                    file_data,
                    self.bucket_name,
                    s3_key,
                    ExtraArgs={
                        'ContentType': self._get_content_type(file_name),
                        'Metadata': {
                            'student_id': str(student_id),
                            'original_filename': file_name,
                            'is_tailored': str(is_tailored),
                            'internship_id': str(internship_id) if internship_id else ''
                        }
                    }
                )
            
            logger.info(f"✅ Successfully uploaded to S3: {s3_key}")
            return s3_key
            
        except ClientError as e:
            logger.error(f"  S3 upload failed: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"  Unexpected error during S3 upload: {str(e)}")
            return None
    
    def generate_presigned_url(
        self,
        s3_key: str,
        expiration: int = 3600
    ) -> Optional[str]:
        """
        Generate a public URL for resume access (bucket is public)
        
        Args:
            s3_key: S3 object key
            expiration: Not used (kept for backward compatibility)
            
        Returns:
            Public S3 URL if successful, None otherwise
        """
        if not self.enabled:
            logger.warning("S3 not enabled, cannot generate URL")
            return None
        
        try:
            # Generate direct public URL (bucket is public, no signature needed)
            url = f"https://{self.bucket_name}.s3.{self.aws_region}.amazonaws.com/{s3_key}"
            logger.info(f"✅ Generated public URL for: {s3_key}")
            return url
            
        except Exception as e:
            logger.error(f"  Unexpected error generating URL: {str(e)}")
            return None
    
    def delete_resume(self, s3_key: str) -> bool:
        """
        Delete resume from S3
        
        Args:
            s3_key: S3 object key
            
        Returns:
            True if successful, False otherwise
        """
        if not self.enabled:
            logger.warning("S3 not enabled, cannot delete")
            return False
        
        try:
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=s3_key
            )
            logger.info(f"✅ Deleted from S3: {s3_key}")
            return True
            
        except ClientError as e:
            logger.error(f"  Failed to delete from S3: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"  Unexpected error deleting from S3: {str(e)}")
            return False
    
    def download_resume(self, s3_key: str, local_path: str) -> bool:
        """
        Download resume from S3 to local path
        
        Args:
            s3_key: S3 object key
            local_path: Local file path to save
            
        Returns:
            True if successful, False otherwise
        """
        if not self.enabled:
            logger.warning("S3 not enabled, cannot download")
            return False
        
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            
            # Download file
            self.s3_client.download_file(
                self.bucket_name,
                s3_key,
                local_path
            )
            logger.info(f"✅ Downloaded from S3: {s3_key} to {local_path}")
            return True
            
        except ClientError as e:
            logger.error(f"  Failed to download from S3: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"  Unexpected error downloading from S3: {str(e)}")
            return False
    
    def _get_content_type(self, filename: str) -> str:
        """Get content type based on file extension"""
        ext = os.path.splitext(filename)[1].lower()
        content_types = {
            '.pdf': 'application/pdf',
            '.doc': 'application/msword',
            '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            '.txt': 'text/plain'
        }
        return content_types.get(ext, 'application/octet-stream')


# Global S3 service instance
s3_service = S3Service()
