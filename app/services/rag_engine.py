"""
RAG (Retrieval-Augmented Generation) Engine
Handles embeddings, vector storage, and similarity matching
"""

import os
import logging
from typing import List, Dict, Optional, Tuple
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
import numpy as np
from dotenv import load_dotenv

from app.utils.gemini_key_manager import get_gemini_key_manager

load_dotenv()

logger = logging.getLogger(__name__)


class RAGEngine:
    """RAG engine for semantic matching between resumes and internships"""
    
    def __init__(self):
        """Initialize RAG engine with HuggingFace embeddings and ChromaDB"""
        # Initialize HuggingFace embedding model
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        logger.info("✅ Initialized HuggingFace embedding model: all-MiniLM-L6-v2")
        
        # Initialize ChromaDB client
        db_path = os.getenv("CHROMA_DB_PATH", "./data/chroma_db")
        os.makedirs(db_path, exist_ok=True)
        
        self.chroma_client = chromadb.PersistentClient(
            path=db_path,
            settings=Settings(anonymized_telemetry=False)
        )
        
        # Create or get collections
        self.resume_collection = self.chroma_client.get_or_create_collection(
            name="resumes",
            metadata={"description": "Student resume embeddings"}
        )
        
        self.internship_collection = self.chroma_client.get_or_create_collection(
            name="internships",
            metadata={"description": "Internship posting embeddings"}
        )
        
        # Initialize Gemini key manager
        self.key_manager = get_gemini_key_manager()
        logger.info("✅ RAGEngine initialized with GeminiKeyManager")
    
    def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding vector for text using HuggingFace
        
        Args:
            text: Input text to embed
            
        Returns:
            Embedding vector as list of floats
        """
        embedding = self.embedding_model.encode(text, convert_to_numpy=True)
        return embedding.tolist()
    
    def store_resume_embedding(
        self, 
        resume_id: str, 
        content: str, 
        skills: List[str],
        metadata: Optional[Dict] = None
    ) -> str:
        """
        Store resume embedding in vector database
        
        Args:
            resume_id: Unique identifier for resume
            content: Resume text content
            skills: List of extracted skills
            metadata: Additional metadata
            
        Returns:
            Embedding ID
        """
        # Combine content and skills for better matching
        combined_text = f"{content}\n\nSkills: {', '.join(skills)}"
        
        # Generate embedding
        embedding = self.generate_embedding(combined_text)
        
        # Prepare metadata (ChromaDB requires scalar values, convert list to string)
        meta = metadata or {}
        meta.update({
            "resume_id": resume_id,
            "skills": ", ".join(skills),  # Convert list to comma-separated string
            "num_skills": len(skills)
        })
        
        # Store in ChromaDB
        self.resume_collection.add(
            embeddings=[embedding],
            documents=[combined_text],
            metadatas=[meta],
            ids=[f"resume_{resume_id}"]
        )
        
        return f"resume_{resume_id}"
    
    def store_internship_embedding(
        self, 
        internship_id: str, 
        title: str,
        description: str, 
        required_skills: List[str],
        metadata: Optional[Dict] = None
    ) -> str:
        """
        Store internship embedding in vector database
        
        Args:
            internship_id: Unique identifier for internship
            title: Internship title
            description: Internship description
            required_skills: List of required skills
            metadata: Additional metadata
            
        Returns:
            Embedding ID
        """
        # Combine title, description and skills
        combined_text = f"Title: {title}\n\nDescription: {description}\n\nRequired Skills: {', '.join(required_skills)}"
        
        # Generate embedding
        embedding = self.generate_embedding(combined_text)
        
        # Prepare metadata (ChromaDB requires scalar values, convert list to string)
        meta = metadata or {}
        meta.update({
            "internship_id": internship_id,
            "title": title,
            "required_skills": ", ".join(required_skills),  # Convert list to comma-separated string
            "num_skills": len(required_skills)
        })
        
        # Store in ChromaDB
        self.internship_collection.add(
            embeddings=[embedding],
            documents=[combined_text],
            metadatas=[meta],
            ids=[f"internship_{internship_id}"]
        )
        
        return f"internship_{internship_id}"
    
    def find_matching_internships(
        self, 
        resume_id: str, 
        top_k: int = 10
    ) -> List[Dict]:
        """
        Find matching internships for a resume using cosine similarity
        
        Args:
            resume_id: Resume identifier
            top_k: Number of top matches to return
            
        Returns:
            List of matching internships with scores
        """
        import logging
        logger = logging.getLogger(__name__)
        
        try:
            logger.info(f"[RAG] Finding matching internships for resume_id: {resume_id}")
            
            # Check what's in the resume collection
            all_resumes = self.resume_collection.get()
            logger.info(f"[RAG] Total resumes in collection: {len(all_resumes['ids']) if all_resumes['ids'] else 0}")
            logger.info(f"[RAG] Resume IDs in collection: {all_resumes['ids']}")
            
            # Get resume embedding
            lookup_id = f"resume_{resume_id}"
            logger.info(f"[RAG] Looking for resume with ID: {lookup_id}")
            
            resume_result = self.resume_collection.get(
                ids=[lookup_id],
                include=["embeddings", "metadatas"]
            )
            
            logger.info(f"[RAG] Resume lookup result IDs: {resume_result.get('ids', [])}")
            logger.info(f"[RAG] Has embeddings: {resume_result.get('embeddings') is not None}")
            
            # Check if embeddings exist
            if 'embeddings' not in resume_result or resume_result['embeddings'] is None or len(resume_result['embeddings']) == 0:
                logger.warning(f"[RAG] No embeddings found for resume {resume_id}")
                return []
            
            resume_embedding = resume_result['embeddings'][0]
            logger.info(f"[RAG] Found resume embedding with dimension: {len(resume_embedding)}")
            
            # Check what's in the internship collection
            all_internships = self.internship_collection.get()
            logger.info(f"[RAG] Total internships in collection: {len(all_internships['ids']) if all_internships['ids'] else 0}")
            logger.info(f"[RAG] Internship IDs in collection: {all_internships['ids']}")
            
            # Query internship collection
            logger.info(f"[RAG] Querying for top {top_k} matches")
            results = self.internship_collection.query(
                query_embeddings=[resume_embedding],
                n_results=top_k,
                include=["metadatas", "distances"]
            )
            
            logger.info(f"[RAG] Query returned {len(results['metadatas'][0]) if results['metadatas'] else 0} results")
            
            # Format results with match scores using min-max normalization
            matches = []
            if results['metadatas'] and len(results['metadatas']) > 0 and len(results['metadatas'][0]) > 0:
                distances = results['distances'][0]
                
                # Get distance range for normalization
                if len(distances) > 1:
                    min_dist = min(distances)
                    max_dist = max(distances)
                    dist_range = max_dist - min_dist
                else:
                    min_dist = distances[0] if distances else 0
                    dist_range = 0
                
                for metadata, distance in zip(results['metadatas'][0], distances):
                    # Min-max normalization with inversion (lower distance = higher score)
                    if dist_range > 0:
                        normalized = 1 - ((distance - min_dist) / dist_range)
                        # Scale to 35-95 range for good visual differentiation
                        similarity = int(35 + (normalized * 60))
                    else:
                        # All distances the same, give high score
                        similarity = 85
                    
                    similarity = max(0, min(100, similarity))
                    
                    # Convert skills string back to list
                    skills_str = metadata.get('required_skills', '')
                    skills_list = [s.strip() for s in skills_str.split(',')] if skills_str else []
                    
                    matches.append({
                        "internship_id": metadata.get('internship_id'),
                        "title": metadata.get('title'),
                        "required_skills": skills_list,
                        "match_score": similarity
                    })
            
            return matches
            
        except Exception as e:
            import traceback
            print(f"Error in find_matching_internships: {str(e)}")
            print(f"Traceback: {traceback.format_exc()}")
            return []
    
    def find_matching_candidates(
        self, 
        internship_id: str, 
        top_k: int = 20
    ) -> List[Dict]:
        """
        Find matching candidates for an internship using cosine similarity
        
        Args:
            internship_id: Internship identifier
            top_k: Number of top matches to return
            
        Returns:
            List of matching resumes with scores
        """
        try:
            # Get internship embedding
            internship_result = self.internship_collection.get(
                ids=[f"internship_{internship_id}"],
                include=["embeddings", "metadatas"]
            )
            
            # Check if embeddings exist
            if 'embeddings' not in internship_result or internship_result['embeddings'] is None or len(internship_result['embeddings']) == 0:
                return []
            
            internship_embedding = internship_result['embeddings'][0]
            
            # Query resume collection
            results = self.resume_collection.query(
                query_embeddings=[internship_embedding],
                n_results=top_k,
                include=["metadatas", "distances"]
            )
            
            # Format results with match scores using min-max normalization
            matches = []
            if results['metadatas'] and len(results['metadatas']) > 0 and len(results['metadatas'][0]) > 0:
                distances = results['distances'][0]
                
                # Get distance range for normalization
                if len(distances) > 1:
                    min_dist = min(distances)
                    max_dist = max(distances)
                    dist_range = max_dist - min_dist
                else:
                    min_dist = distances[0] if distances else 0
                    dist_range = 0
                
                for metadata, distance in zip(results['metadatas'][0], distances):
                    # Min-max normalization with inversion (lower distance = higher score)
                    if dist_range > 0:
                        normalized = 1 - ((distance - min_dist) / dist_range)
                        # Scale to 35-95 range for good visual differentiation
                        similarity = int(35 + (normalized * 60))
                    else:
                        # All distances the same, give high score
                        similarity = 85
                    
                    similarity = max(0, min(100, similarity))
                    
                    # Convert skills string back to list
                    skills_str = metadata.get('skills', '')
                    skills_list = [s.strip() for s in skills_str.split(',')] if skills_str else []
                    
                    matches.append({
                        "resume_id": metadata.get('resume_id'),
                        "skills": skills_list,
                        "match_score": similarity
                    })
            
            return matches
            
        except Exception as e:
            print(f"Error finding matches: {str(e)}")
            return []
    
    def get_resume_embedding(self, resume_id: str) -> Optional[List[float]]:
        """
        Retrieve resume embedding from vector database
        
        Args:
            resume_id: Unique identifier for resume
            
        Returns:
            Embedding vector or None if not found
        """
        try:
            result = self.resume_collection.get(
                ids=[f"resume_{resume_id}"],
                include=["embeddings"]
            )
            
            # Check if result has embeddings
            if result and 'embeddings' in result and result['embeddings'] is not None:
                if len(result['embeddings']) > 0:
                    return result['embeddings'][0]
            return None
            
        except Exception as e:
            print(f"Error retrieving resume embedding: {str(e)}")
            return None
    
    def get_internship_embedding(self, internship_id: str) -> Optional[List[float]]:
        """
        Retrieve internship embedding from vector database
        
        Args:
            internship_id: Unique identifier for internship
            
        Returns:
            Embedding vector or None if not found
        """
        try:
            result = self.internship_collection.get(
                ids=[f"internship_{internship_id}"],
                include=["embeddings"]
            )
            
            # Check if result has embeddings
            if result and 'embeddings' in result and result['embeddings'] is not None:
                if len(result['embeddings']) > 0:
                    return result['embeddings'][0]
            return None
            
        except Exception as e:
            print(f"Error retrieving internship embedding: {str(e)}")
            return None
    
    def delete_resume_embedding(self, resume_id: str) -> bool:
        """Delete resume embedding from vector database"""
        try:
            self.resume_collection.delete(ids=[f"resume_{resume_id}"])
            return True
        except Exception as e:
            print(f"Error deleting resume embedding: {str(e)}")
            return False
    
    def delete_internship_embedding(self, internship_id: str) -> bool:
        """Delete internship embedding from vector database"""
        try:
            self.internship_collection.delete(ids=[f"internship_{internship_id}"])
            return True
        except Exception as e:
            print(f"Error deleting internship embedding: {str(e)}")
            return False
    
    def clear_all_resume_embeddings(self) -> int:
        """
        Clear ALL resume embeddings from ChromaDB at once
        
        This is much more reliable than deleting one-by-one.
        Returns the number of embeddings cleared.
        """
        try:
            # Get all current IDs
            result = self.resume_collection.get()
            all_ids = result['ids']
            count = len(all_ids)
            
            logger.info(f"Found {count} resume embeddings to clear from ChromaDB")
            
            # Delete all at once if any exist
            if count > 0:
                self.resume_collection.delete(ids=all_ids)
                logger.info(f"✅ Successfully cleared {count} resume embeddings from ChromaDB")
            else:
                logger.info("No resume embeddings to clear")
            
            return count
        except Exception as e:
            logger.error(f"  Error clearing all resume embeddings: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return 0


# Global RAG engine instance
rag_engine = RAGEngine()
