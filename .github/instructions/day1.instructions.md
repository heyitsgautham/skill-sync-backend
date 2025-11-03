

Goal: Implement resume and internship storage with RAG-based matching logic.

Tasks:

Create DB models:

User (Student, Company, Admin)

Internship

Resume

Application

Build API routes:

/resume/upload

/internship/post

/internship/list

Integrate a Parser service (using PyMuPDF, pdfminer, or docx reader)

Setup Vector DB (e.g., FAISS, Chroma, or Pinecone)

Implement rag_engine.py to:

Generate embeddings (e.g., HuggingFace)

Store embeddings in Vector DB

Retrieve matches via cosine similarity

Test matching flow manually with dummy data.

Deliverable:
✔️ Working RAG engine integrated with resume and internship embeddings.
✔️ All core models functional and persisted.