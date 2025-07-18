import os
from dotenv import load_dotenv
from llama_index.core import Settings
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.llms.groq import Groq
from openai import OpenAI
import logging

# Setup logging configuration
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

# Retrieve Groq API key
groq_api_key = os.getenv("GroqCloud_API_TOKEN")
if not groq_api_key:
    logger.error("[!] Groq API Key not found in .env file")
    raise ValueError("Please set GroqCloud_API_TOKEN in .env file")

# Initialize Groq OpenAI-compatible client
client = OpenAI(
    api_key=groq_api_key,
    base_url="https://api.groq.com/openai/v1"
)

# Test Groq API connection
try:
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": "Test connection"}],
        max_tokens=10
    )
    logger.info("[✔] Groq API is running successfully.")
except Exception as e:
    logger.error(f"[!] Error connecting to Groq API: {str(e)}")
    exit(1)

# Initialize embedding model using HuggingFace
try:
    Settings.embed_model = HuggingFaceEmbedding(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )
    logger.info("[✔] HuggingFace embedding model initialized successfully.")
except Exception as e:
    logger.error(f"[!] Error initializing embedding model: {str(e)}")
    raise

# Initialize Groq LLM
try:
    Settings.llm = Groq(
        api_key=groq_api_key,
        model="llama-3.3-70b-versatile",
        api_base="https://api.groq.com/openai/v1"
    )
    logger.info("[✔] Groq LLM initialized successfully.")
except Exception as e:
    logger.error(f"[!] Error initializing Groq LLM: {str(e)}. Falling back to Ollama.")
    from llama_index.llms.ollama import Ollama
    
    # Fallback to local LLM via Ollama if Groq fails
    Settings.llm = Ollama(model="mistral:instruct", request_timeout=360.0, base_url="http://127.0.0.1:11434")

# Define path for Chroma vector store
CHROMA_DB_PATH = "./chroma_db"

# Export the client for use in other modules
Settings.llm_client = client
