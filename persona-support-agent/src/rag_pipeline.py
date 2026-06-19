import os
import sys
from pathlib import Path
from typing import List, Dict, Any
from pypdf import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter
import chromadb
from google import genai

# Ensure project path is accessible
sys.path.append(str(Path(__file__).resolve().parent.parent))

from src import config

class LocalRAGPipeline:
    def __init__(self, db_dir: str = None):
        """Initializes the RAG Pipeline with ChromaDB and Embedding models."""
        self.db_dir = db_dir or str(config.DB_DIR)
        self.chroma_client = chromadb.PersistentClient(path=self.db_dir)
        
        # Setup API Client for Gemini
        self.api_key = config.GEMINI_API_KEY
        self.gemini_client = None
        self.local_model = None
        self.use_local = False
        
        if self.api_key:
            try:
                self.gemini_client = genai.Client(api_key=self.api_key)
                print(f"Using Gemini API {config.DEFAULT_EMBEDDING_MODEL} for embeddings.")
            except Exception as e:
                print(f"Error initializing Gemini client: {e}. Falling back to local SentenceTransformers.")
                self.use_local = True
        else:
            print("No GEMINI_API_KEY found in environment or .env. Using local SentenceTransformers.")
            self.use_local = True
            
        if self.use_local:
            try:
                from sentence_transformers import SentenceTransformer
                print(f"Loading local SentenceTransformer model '{config.LOCAL_EMBEDDING_MODEL}'...")
                self.local_model = SentenceTransformer(config.LOCAL_EMBEDDING_MODEL)
                print("Local embedding model loaded successfully.")
            except Exception as e:
                print(f"Error loading local SentenceTransformer model: {e}")
                raise e

        # Determine target dimension of our embedding model
        try:
            target_dim = len(self.get_embedding("test_dimension"))
        except Exception as e:
            print(f"Error generating test embedding: {e}")
            target_dim = 384  # default/fallback

        # Check if collection exists and has matching dimension
        collection_exists = False
        try:
            self.chroma_client.get_collection(name="support_kb")
            collection_exists = True
        except Exception:
            pass

        if collection_exists:
            try:
                temp_col = self.chroma_client.get_collection(name="support_kb")
                if temp_col.count() > 0:
                    sample = temp_col.peek(limit=1)
                    if sample and sample.get('embeddings') is not None and len(sample['embeddings']) > 0:
                        stored_dim = len(sample['embeddings'][0])
                        if stored_dim != target_dim:
                            print(f"Dimension mismatch: DB stores {stored_dim} dims, but model generates {target_dim} dims. Re-initializing collection...")
                            self.chroma_client.delete_collection(name="support_kb")
            except Exception as e:
                print(f"Error checking DB dimensions: {e}. Attempting collection recreation...")
                try:
                    self.chroma_client.delete_collection(name="support_kb")
                except Exception:
                    pass

        # Now safely create or get the collection
        self.collection = self.chroma_client.get_or_create_collection(
            name="support_kb",
            metadata={"hnsw:space": "cosine"}
        )

        # Ingest documents if database is empty
        if self.collection.count() == 0:
            print("Database is empty. Running ingestion...")
            self.ingest_directory()

    def get_embedding(self, text: str) -> List[float]:
        """Generates embedding vector for a given text."""
        if not self.use_local and self.gemini_client:
            try:
                # Call Gemini Embedding API
                response = self.gemini_client.models.embed_content(
                    model=config.DEFAULT_EMBEDDING_MODEL,
                    contents=text
                )
                return response.embeddings[0].values
            except Exception as e:
                print(f"Gemini embedding API call failed: {e}. Attempting fallback...")
                # Lazy load local model on API failure
                if not self.local_model:
                    from sentence_transformers import SentenceTransformer
                    self.local_model = SentenceTransformer(config.LOCAL_EMBEDDING_MODEL)
                self.use_local = True
        
        # Local embedding fallback
        return self.local_model.encode(text).tolist()

    def load_pdf_document(self, file_path: Path) -> List[Dict[str, Any]]:
        """Parses a PDF file page-by-page and returns structured page data."""
        pages_content = []
        try:
            reader = PdfReader(file_path)
            for idx, page in enumerate(reader.pages):
                text = page.extract_text()
                if text and text.strip():
                    pages_content.append({
                        "content": text.strip(),
                        "metadata": {
                            "source": file_path.name,
                            "page": idx + 1,
                            "type": "pdf"
                        }
                    })
        except Exception as e:
            print(f"Error reading PDF {file_path.name}: {e}")
        return pages_content

    def load_text_document(self, file_path: Path) -> List[Dict[str, Any]]:
        """Reads a text or markdown file."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            if content and content.strip():
                return [{
                    "content": content.strip(),
                    "metadata": {
                        "source": file_path.name,
                        "type": file_path.suffix[1:] or "txt"
                    }
                }]
        except Exception as e:
            print(f"Error reading text file {file_path.name}: {e}")
        return []

    def ingest_document(self, file_name: str, content: str, doc_metadata: Dict[str, Any] = None):
        """Splits document content into chunks and adds them to ChromaDB."""
        metadata = doc_metadata or {"source": file_name, "type": "txt"}
        
        # Initialize LangChain character splitter
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=config.CHUNK_SIZE,
            chunk_overlap=config.CHUNK_OVERLAP
        )
        chunks = splitter.split_text(content)

        for idx, chunk in enumerate(chunks):
            embedding = self.get_embedding(chunk)
            chunk_id = f"{file_name}_chunk_{idx}"
            
            # Enrich metadata
            chunk_metadata = metadata.copy()
            chunk_metadata["chunk_index"] = idx
            
            # Clean metadata (ChromaDB does not support nested values or lists, only str, int, float, bool)
            self.collection.add(
                ids=[chunk_id],
                embeddings=[embedding],
                metadatas=[chunk_metadata],
                documents=[chunk]
            )

    def ingest_directory(self, data_dir: Path = None):
        """Loads and indexes all documents from the data directory."""
        dir_path = data_dir or config.DATA_DIR
        print(f"Starting ingestion of files from: {dir_path}")
        
        files = list(dir_path.glob("*"))
        if not files:
            print("No files found to ingest.")
            return

        for filepath in files:
            if filepath.is_dir():
                continue
                
            suffix = filepath.suffix.lower()
            if suffix == ".pdf":
                print(f"Parsing PDF file: {filepath.name}")
                pages = self.load_pdf_document(filepath)
                for page in pages:
                    # Ingest page text individually to keep page association
                    page_content = page["content"]
                    page_meta = page["metadata"]
                    self.ingest_document(
                        file_name=f"{filepath.name}_page_{page_meta['page']}",
                        content=page_content,
                        doc_metadata=page_meta
                    )
            elif suffix in [".txt", ".md"]:
                print(f"Parsing text/markdown file: {filepath.name}")
                docs = self.load_text_document(filepath)
                for doc in docs:
                    self.ingest_document(
                        file_name=filepath.name,
                        content=doc["content"],
                        doc_metadata=doc["metadata"]
                    )
            else:
                print(f"Skipping unsupported file type: {filepath.name}")
        
        print("Ingestion completed successfully.")

    def retrieve_context(self, query: str, top_k: int = None) -> List[Dict[str, Any]]:
        """Searches the vector database for relevant chunks and calculates similarity."""
        k = top_k or config.TOP_K
        query_vector = self.get_embedding(query)

        try:
            results = self.collection.query(
                query_embeddings=[query_vector],
                n_results=k
            )
        except Exception as e:
            print(f"ChromaDB search query failed: {e}")
            return []

        retrieved_items = []
        if results and 'documents' in results and results['documents'] and len(results['documents'][0]) > 0:
            documents = results['documents'][0]
            metadatas = results['metadatas'][0]
            distances = results['distances'][0] if results['distances'] else [1.0] * len(documents)

            for i in range(len(documents)):
                # Chroma configured with cosine space returns cosine distance
                # Cosine Similarity = 1.0 - Cosine Distance
                distance = distances[i]
                similarity_score = max(0.0, 1.0 - distance)
                
                retrieved_items.append({
                    "text": documents[i],
                    "source": metadatas[i].get("source", "Unknown"),
                    "page": metadatas[i].get("page", None),
                    "type": metadatas[i].get("type", "txt"),
                    "chunk_index": metadatas[i].get("chunk_index", 0),
                    "score": round(similarity_score, 4)
                })
        
        # Sort by similarity score descending
        retrieved_items.sort(key=lambda x: x["score"], reverse=True)
        return retrieved_items

# Allow script execution to populate the database
if __name__ == "__main__":
    print("Initializing RAG pipeline for database ingestion...")
    pipeline = LocalRAGPipeline()
    
    # Reset collection for a fresh start
    try:
        pipeline.chroma_client.delete_collection("support_kb")
        pipeline.collection = pipeline.chroma_client.get_or_create_collection(
            name="support_kb",
            metadata={"hnsw:space": "cosine"}
        )
        print("Existing database collection cleared.")
    except Exception:
        pass
        
    pipeline.ingest_directory()
    print("Database population completed!")
