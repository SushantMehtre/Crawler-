import os
import chromadb
from typing import List, Dict, Any, Optional

def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
    """
    Splits text into chunks of roughly chunk_size characters with a given overlap.
    """
    if len(text) <= chunk_size:
        return [text]
        
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk)
        start += chunk_size - overlap
        
    return chunks

class RedditVectorStore:
    """
    Manages the ChromaDB client and collection using ChromaDB's default local embedding function.
    No Gemini embedding API calls are needed for vectorizing data, avoiding API 404/quota errors.
    """
    def __init__(self, persist_directory: str, api_key: str = None, collection_name: str = "reddit_scraped_data"):
        self.persist_directory = persist_directory
        self.collection_name = collection_name
        
        # Initialize Persistent Chroma DB
        self.chroma_client = chromadb.PersistentClient(path=self.persist_directory)
        
        # Use ChromaDB's default local embedding function (ONNX-based all-MiniLM-L6-v2)
        # This runs completely locally and does not require an API key or trigger 404 errors.
        self.collection = self.chroma_client.get_or_create_collection(
            name=self.collection_name
        )
        
    def add_reddit_data(self, title: str, texts: List[str], source_url: str):
        """
        Chunks the scraped text contents and inserts them into ChromaDB.
        """
        documents = []
        metadatas = []
        ids = []
        
        doc_counter = 0
        for text_index, text in enumerate(texts):
            chunks = chunk_text(text, chunk_size=800, overlap=150)
            for chunk_index, chunk in enumerate(chunks):
                doc_id = f"doc_{text_index}_{chunk_index}_{doc_counter}"
                documents.append(chunk)
                metadatas.append({
                    "title": title,
                    "source_url": source_url,
                    "text_index": text_index,
                    "chunk_index": chunk_index
                })
                ids.append(doc_id)
                doc_counter += 1
                
        if documents:
            self.collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            
    def clear_collection(self):
        """
        Deletes the collection and recreates it.
        """
        try:
            self.chroma_client.delete_collection(name=self.collection_name)
        except Exception:
            pass
        self.collection = self.chroma_client.get_or_create_collection(
            name=self.collection_name
        )
        
    def query(self, query_text: str, n_results: int = 5) -> List[Dict[str, Any]]:
        """
        Queries the ChromaDB collection.
        """
        results = self.collection.query(
            query_texts=[query_text],
            n_results=n_results
        )
        
        # Format results
        formatted_results = []
        if results and results.get('documents'):
            docs = results['documents'][0]
            metas = results['metadatas'][0]
            distances = results['distances'][0] if 'distances' in results else [0]*len(docs)
            
            for doc, meta, dist in zip(docs, metas, distances):
                formatted_results.append({
                    "content": doc,
                    "metadata": meta,
                    "distance": dist
                })
                
        return formatted_results

    def get_stored_documents(self) -> Dict[str, str]:
        """
        Retrieves unique titles and source URLs of all stored documents.
        """
        try:
            data = self.collection.get()
            unique_sources = {}
            if data and data.get('metadatas'):
                for meta in data['metadatas']:
                    title = meta.get('title', 'Untitled')
                    url = meta.get('source_url', 'Pasted/Uploaded')
                    unique_sources[title] = url
            return unique_sources
        except Exception:
            return {}
