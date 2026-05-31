"""
RAG (Retrieval-Augmented Generation) module.
Loads markdown documents from the knowledge_base/ folder, chunks them,
embeds with OpenAI embeddings, and stores in a ChromaDB vector store.
"""

import os
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma

from config.settings import (
    KNOWLEDGE_BASE_DIR,
    CHROMA_PERSIST_DIR,
    EMBEDDING_MODEL,
    RAG_CHUNK_SIZE,
    RAG_CHUNK_OVERLAP,
    RAG_TOP_K,
)


def build_vectorstore() -> Chroma:
    """Load knowledge-base documents, chunk, embed, and persist to ChromaDB.

    If the persisted store already exists it is loaded directly (fast path).
    """
    embeddings = OpenAIEmbeddings(model=EMBEDDING_MODEL)

    # Fast path — reuse existing store
    if os.path.exists(CHROMA_PERSIST_DIR) and os.listdir(CHROMA_PERSIST_DIR):
        print("  ↳ Loading existing vector store from disk …")
        return Chroma(
            persist_directory=CHROMA_PERSIST_DIR,
            embedding_function=embeddings,
        )

    print("  ↳ Building vector store from knowledge base …")
    # Load all .md files from the knowledge_base directory
    loader = DirectoryLoader(
        KNOWLEDGE_BASE_DIR,
        glob="**/*.md",
        loader_cls=TextLoader,
        loader_kwargs={"encoding": "utf-8"},
    )
    documents = loader.load()

    if not documents:
        raise FileNotFoundError(
            f"No .md files found in {KNOWLEDGE_BASE_DIR}. "
            "Add knowledge-base documents before building the vector store."
        )

    # Chunk the documents for better retrieval granularity
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=RAG_CHUNK_SIZE,
        chunk_overlap=RAG_CHUNK_OVERLAP,
        separators=["\n## ", "\n### ", "\n\n", "\n", " "],
    )
    chunks = splitter.split_documents(documents)
    print(f"  ↳ {len(documents)} documents → {len(chunks)} chunks")

    # Create and persist the vector store
    os.makedirs(CHROMA_PERSIST_DIR, exist_ok=True)
    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=CHROMA_PERSIST_DIR,
    )
    print("  ↳ Vector store persisted to disk.")
    return vectorstore


def get_retriever(vectorstore: Chroma):
    """Return a LangChain retriever from the vectorstore."""
    return vectorstore.as_retriever(
        search_type="similarity",
        search_kwargs={"k": RAG_TOP_K},
    )
