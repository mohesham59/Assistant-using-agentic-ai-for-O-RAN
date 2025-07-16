import os
import logging
from llama_index.core import VectorStoreIndex, Document
from llama_index.readers.web import SimpleWebPageReader
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.core.tools import QueryEngineTool, ToolMetadata
from urllib.parse import urlparse
import validators
from llama_index.core import Settings
import chromadb
import config

# Configure logging for consistent debug output
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def load_index(url: str = None, index_name: str = "web", use_chroma=True):
    # Set a default URL if none is provided
    if not url:
        url = "https://docs.o-ran-sc.org/projects/o-ran-sc-nonrtric/en/latest/overview.html#nonrtric-components"
    
    # Validate the provided URL
    if not validators.url(url):
        logger.error(f"[!] Invalid URL: {url}")
        raise ValueError(f"Invalid URL: {url}")

    # Ensure the embedding model is initialized
    if not Settings.embed_model:
        logger.error("[!] Embedding model not initialized")
        raise ValueError("Embedding model not initialized")

    try:
        # Load and parse the webpage into documents
        documents = SimpleWebPageReader(html_to_text=True).load_data([url])
        logger.info(f"Loaded {len(documents)} documents from {url}")

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
        logger.error(f"Error loading index for {url}: {str(e)}")
        raise

def asQueryEngineTool(index):
    if index is None:
        logger.error("[!] Web index could not be loaded")
        raise ValueError("Web index could not be loaded")
    
    query_engine = index.as_query_engine(response_mode="compact")
    return QueryEngineTool(
        query_engine=query_engine,
        metadata=ToolMetadata(
            name="web_reader_engine",
            description="This tool retrieves content from a specified web page to provide insights or recommendations."
        )
    )

try:
    index = load_index(use_chroma=True)  # Default to Chroma
    web_reader_engine = asQueryEngineTool(index)
except Exception as e:
    logger.error(f"[!] Failed to initialize web_reader_engine: {str(e)}")
    raise
