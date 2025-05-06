from docling.document_converter import DocumentConverter
from docling.chunking import HybridChunker

from langchain.text_splitter import RecursiveCharacterTextSplitter

import chromadb

CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200
SOURCE = "https://markets.ft.com/data/equities/tearsheet/summary?s=SWP:PAR"

def parse_doc(source: str):
    converter = DocumentConverter()
    result = converter.convert(source)

    return result.document

def initialize_chroma(name: str):
    chroma_client = chromadb.PersistentClient(path="./chroma_db")
    collection = chroma_client.get_or_create_collection(name=name)

    return collection

def chunk(doc: str):
    chunker = HybridChunker()
    chunk_iter = chunker.chunk(dl_doc=doc)

    chunks = []
    for i, chunk in enumerate(chunk_iter):
        print(f"=== {i} ===")
        print(f"chunk.text:\n{repr(f'{chunk.text[:300]}…')}")

        enriched_text = chunker.serialize(chunk=chunk)
        print(f"chunker.serialize(chunk):\n{repr(f'{enriched_text[:300]}…')}")
        chunks.append(enriched_text)

    return chunks

def update_database(db: chromadb.Collection, chunks):
    existing_data = db.get()
    existing_docs = existing_data.get('documents', [])
    existing_ids = existing_data.get('ids', [])

    print(chunks)
    print(existing_docs)
    
    # Check if the content and order of existing documents match the new chunks
    if len(existing_docs) == len(chunks):
        print("Database is up-to-date. No changes needed.")
        return
    
    # Remove existing documents if they differ from new chunks
    if existing_ids:
        db.delete(ids=existing_ids)
    
    # Add new chunks with updated IDs
    doc_ids = [f"doc_{i}" for i in range(len(chunks))]
    db.add(ids=doc_ids, documents=chunks)
    print("Database updated with new chunks.")

def main():
    collection = initialize_chroma("html")
    doc = parse_doc(SOURCE)
    chunks = chunk(doc)
    update_database(collection, chunks)

if __name__ == "__main__":
    main()
