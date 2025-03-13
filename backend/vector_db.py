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

def initialize_chroma():
    chroma_client = chromadb.PersistentClient(path="./chroma_db")
    collection = chroma_client.get_or_create_collection(name="html")

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
        print()

    return chunks

def update_database(db: chromadb.Collection, chunks):
    doc_ids = [f"doc_{i}" for i in range(len(chunks))]
    db.add(ids=doc_ids, documents=chunks)

def main():
    # collection = initialize_chroma()
    doc = parse_doc(SOURCE)
    chunk(doc)
    # update_database(collection, chunks)

if __name__ == "__main__":
    main()
