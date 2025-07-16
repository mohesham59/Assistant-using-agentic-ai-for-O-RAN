import os
import logging
import re
import time
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from orjson import JSONDecodeError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from llama_index.core import VectorStoreIndex, Settings, SimpleDirectoryReader
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.core.retrievers import VectorIndexRetriever
from llama_index.core.prompts import PromptTemplate
from llama_index.readers.web import SimpleWebPageReader
from tools.guidelines import load_index as load_guidelines_index
from tools.web_reader import load_index as load_web_index
from tools.report_generator import generate_report
import config
import llama_index.core

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Log current llama-index version
logger.info(f"Llama-index version: {llama_index.core.__version__}")

# Load indexes either from persistent Chroma DB or in-memory using LlamaIndex
def load_indexes(vector_store_type):
    try:
        if vector_store_type == "chroma":
            # Load vector indexes from Chroma
            guidelines_index = load_guidelines_index("data", "guidelines")
            web_index = load_web_index("https://docs.o-ran-sc.org/projects/o-ran-sc-nonrtric/en/latest/overview.html#nonrtric-components", "web")
        else:
            # Load guidelines index without Chroma (using LlamaIndex in-memory)
            documents = SimpleDirectoryReader(input_dir="data", required_exts=['.pdf']).load_data()
            guidelines_index = VectorStoreIndex.from_documents(documents)
            logger.info("Created in-memory guidelines index for LlamaIndex")
            
            # Load web index without Chroma
            web_documents = SimpleWebPageReader(html_to_text=True).load_data(["https://docs.o-ran-sc.org/projects/o-ran-sc-nonrtric/en/latest/overview.html#nonrtric-components"])
            web_index = VectorStoreIndex.from_documents(web_documents)
            logger.info("Created in-memory web index for LlamaIndex")
        
        return guidelines_index, web_index
    except Exception as e:
        logger.error(f"[!] Error loading indexes: {str(e)}", exc_info=True)
        raise

# Initialize retrievers and query engines
def create_query_engines(guidelines_index, web_index):
    guidelines_retriever = VectorIndexRetriever(index=guidelines_index, similarity_top_k=5)
    web_retriever = VectorIndexRetriever(index=web_index, similarity_top_k=5)
    
    guidelines_query_engine = RetrieverQueryEngine(retriever=guidelines_retriever)
    web_query_engine = RetrieverQueryEngine(retriever=web_retriever)
    
    return guidelines_query_engine, web_query_engine

# Default URL used for web document index
DEFAULT_URL = "https://docs.o-ran-sc.org/projects/o-ran-sc-nonrtric/en/latest/overview.html#nonrtric-components"

# Prompt used to generate factual Markdown responses from retrieved data
report_prompt = PromptTemplate(
    """
    You are an expert assistant with access to guidelines documents (PDFs in the data directory) and web data. Based on the user input, retrieve and provide a clear, concise, and accurate description or explanation of the requested topic from the available data. The output should be in Markdown format and include:

    - Provide a direct and detailed answer to the user's query, focusing on the requested topic (e.g., definitions, descriptions, components, or functionalities).
    - If the requested topic involves code (e.g., installation scripts or configurations), include the relevant code snippets verbatim in the response, formatted as Markdown code blocks.
    - Include relevant details, examples, or references from the guidelines documents or web data to support the explanation.
    - Use clear and simple language suitable for both technical and non-technical audiences.
    - If applicable, include a brief explanation of any technical terms or acronyms mentioned.
    - Do not include a "Response" heading in the output; the response will be formatted later.

    ### Source Information
    - List the sources used (e.g., specific PDF files from the data directory or web URLs) to provide transparency.

    Ensure the response is well-structured, professional, and suitable for conversion to a PDF. Avoid generating a content optimization report or recommendations unless explicitly requested. Focus on answering the query directly.

    User Input: {user_input}
    """
)

# Initialize FastAPI app
app = FastAPI()

# Serve static files (for downloading report.pdf)
app.mount("/static", StaticFiles(directory="."), name="static")

# Enable CORS for frontend compatibility
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve the frontend HTML page
@app.get("/")
async def serve_index():
    return FileResponse("index.html")

# Define the input schema
class PromptRequest(BaseModel):
    prompt: str
    vectorStoreType: str # User can choose between 'chroma' or 'llamaindex'

# Format the Markdown response with sources
def format_response(response, sources):
    """
    Format the response in Markdown with source information.
    """
    markdown_content = f"### Response\n{response}\n\n### Source Information\n"
    if sources:
        for source in sources:
            markdown_content += f"- {source}\n"
    else:
        markdown_content += "- No specific sources identified.\n"
    return markdown_content

# Main endpoint for generating the report
@app.post("/generate")
async def generate_report_endpoint(request: PromptRequest):
    user_input = request.prompt
    vector_store_type = request.vectorStoreType
    if not user_input:
        raise HTTPException(status_code=400, detail="Prompt cannot be empty")
    if vector_store_type not in ["chroma", "llamaindex"]:
        raise HTTPException(status_code=400, detail="Invalid vector store type. Use 'chroma' or 'llamaindex'.")

    try:
        # Load indexes based on vector store type
        guidelines_index, web_index = load_indexes(vector_store_type)
        guidelines_query_engine, web_query_engine = create_query_engines(guidelines_index, web_index)

        # Query both engines to retrieve relevant information
        sources = []
        response_parts = []

        # Query guidelines index
        user_input_formatted = report_prompt.format(user_input=user_input)
        guidelines_response = guidelines_query_engine.query(user_input_formatted).response
        if guidelines_response:
            response_parts.append(guidelines_response)
            pdf_files = [f for f in os.listdir("data") if f.endswith('.pdf')]
            sources.extend([f"PDF: {f}" for f in pdf_files])

        # Query web index if relevant
        if "web page" in user_input.lower() or "nonrtric" in user_input.lower():
            logger.info(f"Using default URL: {DEFAULT_URL}")
            web_response = web_query_engine.query(user_input_formatted).response
            if web_response:
                response_parts.append(web_response)
                sources.append(f"Web: {DEFAULT_URL}")

        # Combine responses
        combined_response = "\n\n".join(response_parts) if response_parts else "No relevant information found in the provided data."
        markdown_content = format_response(combined_response, sources)
        logger.info(f"Query engine response: {combined_response[:100]}...")

        # Generate PDF
        full_markdown_content = (
            f"# Response to '{user_input}'\n\n"
            f"{markdown_content}"
        )
        report_result = generate_report(full_markdown_content, output_file="report.pdf")
        logger.info(f"Report generation result: {report_result}")

        # Add a delay to ensure the PDF is fully written
        time.sleep(1)  # Wait for 1 second to ensure file system sync

        # Check if PDF exists and is accessible
        pdf_path = os.path.abspath("report.pdf")
        if not os.path.exists(pdf_path):
            logger.error(f"[!] PDF file not found at {pdf_path}")
            raise HTTPException(status_code=500, detail="Failed to generate PDF report. Check pandoc and pdflatex installation.")

        # Verify the PDF file is not empty and accessible
        if os.path.getsize(pdf_path) == 0:
            logger.error(f"[!] PDF file at {pdf_path} is empty")
            raise HTTPException(status_code=500, detail="Generated PDF is empty. Check report generation process.")

        logger.info(f"Returning PDF URL: http://localhost:8000/static/report.pdf")
        return {
            "report": combined_response,
            "summary": combined_response[:150] + "..." if len(combined_response) > 150 else combined_response,
            "pdf_url": "http://localhost:8000/static/report.pdf"
        }

    except JSONDecodeError as e:
        logger.error(f"⚠️ JSON decode error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=400, detail=f"Invalid JSON data: {str(e)}")
    except Exception as e:
        logger.error(f"⚠️ Error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}. Check logs for details.")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
