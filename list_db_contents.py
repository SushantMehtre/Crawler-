import os
import chromadb

def inspect_database():
    db_path = os.path.join(os.getcwd(), "chroma_db")
    print(f"Opening ChromaDB at: {db_path}...")
    
    if not os.path.exists(db_path):
        print("Database directory does not exist yet. You need to index some data first!")
        return

    try:
        chroma_client = chromadb.PersistentClient(path=db_path)
        collection_name = "reddit_scraped_data"
        
        # Check available collections
        collections = chroma_client.list_collections()
        col_names = [c.name for c in collections]
        print(f"Available collections: {col_names}")
        
        if collection_name not in col_names:
            print(f"Collection '{collection_name}' has not been created yet.")
            return
            
        collection = chroma_client.get_collection(name=collection_name)
        count = collection.count()
        print(f"Total stored text chunks: {count}")
        
        if count == 0:
            print("The collection is currently empty.")
            return
            
        # Retrieve all documents and metadatas
        data = collection.get()
        metadatas = data.get('metadatas', [])
        
        # Aggregate unique sources
        unique_sources = {}
        for meta in metadatas:
            title = meta.get('title', 'Untitled')
            url = meta.get('source_url', 'Pasted/Uploaded')
            unique_sources[title] = unique_sources.get(title, 0) + 1
            
        print("\n--- Stored Documents ---")
        for idx, (title, chunk_count) in enumerate(unique_sources.items(), 1):
            print(f"{idx}. Title: {title}")
            print(f"   Chunks: {chunk_count}")
            print("-" * 30)
            
    except Exception as e:
        print(f"Error inspecting database: {e}")

if __name__ == "__main__":
    inspect_database()
