import os
import logging
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.core.tools import QueryEngineTool, ToolMetadata
from llama_index.core import Settings
import chromadb
import config

# Set up logging configuration
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def load_index(data_dir, index_name, use_chroma=True):
    # Check if the data directory exists
    if not os.path.isdir(data_dir):
        logger.error(f"[!] Data directory not found: {data_dir}")
        raise FileNotFoundError(f"Data directory not found: {data_dir}")

    # Check if the directory contains PDF files
    pdf_files = [f for f in os.listdir(data_dir) if f.endswith('.pdf')]
    if not pdf_files:
        logger.error(f"[!] No PDF files found in directory: {data_dir}")
        raise FileNotFoundError(f"No PDF files found in directory: {data_dir}")

    # Ensure the embedding model is initialized
    if not Settings.embed_model:
        logger.error("[!] Embedding model not initialized")
        raise ValueError("Embedding model not initialized")

    # Ensure the LLM model is initialized
    if not Settings.llm:
        logger.error("[!] LLM not initialized")
        raise ValueError("LLM not initialized")

    try:
        # Load all PDF documents from the specified directory
        documents = SimpleDirectoryReader(input_dir=data_dir, required_exts=['.pdf']).load_data()
        logger.info(f"Loaded {len(documents)} documents from {data_dir} (files: {', '.join(pdf_files)})")

        if use_chroma:
            # Initialize Chroma client
            chroma_client = chromadb.PersistentClient(path=config.CHROMA_DB_PATH)
            chroma_collection = chroma_client.get_or_create_collection(name=index_name)

            # Create Chroma vector store
            vector_store = ChromaVectorStore(chroma_collection=chroma_collection)

            # Create and persist the index
            index = VectorStoreIndex.from_documents(
                documents,
                vector_store=vector_store
            )
            logger.info(f"Created and persisted index for {index_name} in Chroma")
        else:
            # Create in-memory index for LlamaIndex
            index = VectorStoreIndex.from_documents(documents)
            logger.info(f"Created in-memory index for {index_name} in LlamaIndex")

        return index
    except Exception as e:
        logger.error(f"Error loading index for {data_dir}: {str(e)}")
        raise

def asQueryEngineTool(index):
    if index is None:
        logger.error("[!] Index is None")
        raise ValueError("Index cannot be None")
    
    # Ensure the LLM model is initialized
    if not Settings.llm:
        logger.error("[!] LLM not initialized")
        raise ValueError("LLM not initialized")
    
    query_engine = index.as_query_engine(similarity_top_k=5, response_mode="compact")
    return QueryEngineTool(
        query_engine=query_engine,
        metadata=ToolMetadata(
            name="guidelines_engine",
            description="This tool retrieves content from all PDF documents in the data directory to provide insights or recommendations."
        )
    )

data_dir = "data"
try:
    guidelines_index = load_index(data_dir, index_name="guidelines", use_chroma=True)  # Default to Chroma
    guidelines_engine = asQueryEngineTool(guidelines_index)
except Exception as e:
    logger.error(f"[!] Failed to initialize guidelines_engine: {str(e)}")
    raise
