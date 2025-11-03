"""
RAG (Retrieval-Augmented Generation) Engine
Handles embeddings, vector storage, and similarity matching
"""

import os
from typing import List, Dict, Optional, Tuple
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
import numpy as np
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()


class RAGEngine:
    """RAG engine for semantic matching between resumes and internships"""
    
    def __init__(self):
        """Initialize RAG engine with HuggingFace embeddings and ChromaDB"""
        # Initialize HuggingFace embedding model
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        
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
        
        # Initialize Google Generative AI
        google_api_key = os.getenv("GOOGLE_API_KEY")
        if google_api_key:
            genai.configure(api_key=google_api_key)
            self.llm_model = genai.GenerativeModel('gemini-pro')
        else:
            self.llm_model = None
    
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
        try:
            # Get resume embedding
            resume_result = self.resume_collection.get(
                ids=[f"resume_{resume_id}"],
                include=["embeddings", "metadatas"]
            )
            
            # Check if embeddings exist
            if 'embeddings' not in resume_result or resume_result['embeddings'] is None or len(resume_result['embeddings']) == 0:
                return []
            
            resume_embedding = resume_result['embeddings'][0]
            
            # Query internship collection
            results = self.internship_collection.query(
                query_embeddings=[resume_embedding],
                n_results=top_k,
                include=["metadatas", "distances"]
            )
            
            # Format results with match scores
            matches = []
            if results['metadatas'] and len(results['metadatas']) > 0 and len(results['metadatas'][0]) > 0:
                for metadata, distance in zip(results['metadatas'][0], results['distances'][0]):
                    # Convert distance to similarity score (0-100)
                    similarity = max(0, min(100, int((1 - distance) * 100)))
                    
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
            
            # Format results with match scores
            matches = []
            if results['metadatas'] and len(results['metadatas']) > 0 and len(results['metadatas'][0]) > 0:
                for metadata, distance in zip(results['metadatas'][0], results['distances'][0]):
                    # Convert distance to similarity score (0-100)
                    similarity = max(0, min(100, int((1 - distance) * 100)))
                    
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


# Global RAG engine instance
rag_engine = RAGEngine()
