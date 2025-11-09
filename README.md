# Assistant-using-agentic-ai-for-O-RAN

The Assistant-using-agentic-ai-for-O-RAN is a Python-based web application designed to analyze and optimize content related to O-RAN (Open Radio Access Network) using Retrieval-Augmented Generation (RAG). It leverages the `llama_index` library and integrates with local (`Ollama` with `mistral:instruct`) and cloud-based (`Groq` with `llama-3.3-70b-versatile`) language models to process content from a specified webpage (`https://docs.o-ran-sc.org/projects/o-ran-sc-nonrtric/en/latest/overview.html#nonrtric-components`) and data files including `graduation_book`, `O-RAN.WG3.E2SM-KPM-R003-v03.00`, and `O-RAN.WG3.E2SM-RC-v01.02` located in the `data/` folder. The tool generates a concise summary (100-150 words) displayed in the GUI's **Recommendations** section and a detailed PDF report (`report.pdf`) with comprehensive analysis and recommendations, adhering to content quality principles like E-E-A-T (Experience, Expertise, Authoritativeness, Trustworthiness).

## Features
- Webpage Analysis: Scrapes and summarizes content from the O-RAN SC NONRTRIC components page.
- Data File Integration: Processes and analyzes PDF documents (`graduation_book`, `O-RAN.WG3.E2SM-KPM-R003-v03.00`, `O-RAN.WG3.E2SM-RC-v01.02`) for structured recommendations.
- Actionable Recommendations: Provides a detailed report with at least three specific suggestions and a concise summary for the GUI.
- PDF Report Generation: Converts the full report into a downloadable PDF using `pandoc` and `pdflatex`, with downloads triggered only when the user clicks the "Download Full PDF Report" button.
- User-Friendly Web Interface: Allows users to input prompts, view summaries, and download the full report via a modern GUI.
- Flexible LLM Processing: Supports both local (`Ollama`) and cloud-based (`Groq`) language models, with fallback to `Ollama` if `Groq` is unavailable.
- Vector Store Options: Supports `Chroma` for persistent storage and `LlamaIndex` for in-memory indexing.

## Project Structure
```
Assistant-using-agentic-ai-for-O-RAN/
│
├── data/
│   ├── graduation_book      # General guidelines or project-related document
│   ├── O-RAN.WG3.E2SM-KPM-R003-v03.00  # E2SM-KPM specification PDF
│   └── O-RAN.WG3.E2SM-RC-v01.02        # E2SM-RC specification PDF
├── embeddings/            # Stores vector embeddings for webpage and PDFs
├── tools/
│   ├── guidelines.py      # Processes data files for content analysis
│   ├── web_reader.py      # Scrapes and processes webpage content
│   └── report_generator.py # Generates PDF reports from Markdown
├── config.py              # Configures LLM and embedding models
├── main.py                # CLI script for generating reports
├── main_api.py            # FastAPI backend for the web interface
├── index.html             # Web interface for user interaction
├── requirements.txt       # Required Python libraries
├── .gitignore             # Ignores unnecessary files
└── README.md              # Project documentation
```

## Prerequisites
- **Python 3.8+**: Ensure Python is installed.
- **Ollama**: Local server for running the `mistral:instruct` model (optional if using `Groq`).
- **Pandoc**: For converting Markdown to PDF.
- **MiKTeX**: Provides `pdflatex` for PDF generation.
- **Git**: For version control and GitHub interaction.
- **Web Browser**: Any modern browser (e.g., Chrome, Firefox) to access the GUI.
- **Groq API Key**: Required for cloud-based LLM processing (set in `.env` file).

## Setup Instructions
1. **Clone the Repository**:
   ```bash
   git clone https://github.com/mohesham59/Assistant-using-agentic-ai-for-O-RAN.git
   cd Assistant-using-agentic-ai-for-O-RAN
   ```

2. **Install Dependencies**:
   Create a virtual environment and install required libraries:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Set Up Groq API (Optional)**:
   - Obtain a `GroqCloud_API_TOKEN` from [x.ai/api](https://x.ai/api).
   - Create a `.env` file in the project root and add your Groq API key:
     ```bash
     echo "GroqCloud_API_TOKEN=your-api-key-here" > .env
     ```
   - Verify the key is loaded correctly when running the application.

4. **Install Ollama (Optional)**:
   - Download and install Ollama from [ollama.com](https://ollama.com).
   - Pull the `mistral:instruct` model:
     ```bash
     ollama pull mistral
     ```
   - Start the Ollama server:
     ```bash
     ollama serve
     ```

5. **Install Pandoc**:
   - Download and install Pandoc from [pandoc.org](https://pandoc.org/installing.html).
   - Verify installation:
     ```bash
     pandoc --version
     ```

6. **Install MiKTeX**:
   - Download and install MiKTeX from [miktex.org](https://miktex.org/download).
   - Verify `pdflatex`:
     ```bash
     pdflatex --version
     ```

7. **Prepare Data Files**:
   - Place `graduation_book`, `O-RAN.WG3.E2SM-KPM-R003-v03.00`, and `O-RAN.WG3.E2SM-RC-v01.02` in the `data/` folder. These files contain guidelines or O-RAN specifications for analysis.

8. **Build Web and PDF Index**:
   - Generate the web index for the NONRTRIC components page and process PDF data:
     ```bash
     python -m tools.web_reader
     ```

## Usage
### Option 1: Command-Line Interface (CLI)
1. **Run the CLI Script**:
   ```bash
   python main.py
   ```
2. **Enter Input**:
   - Input a prompt like:
     ```
     Optimize content using E2SM-KPM and E2SM-RC specifications
     ```
   - Type `quit` to exit.
3. **View Output**:
   - The script prints the report and generates `report.pdf` in the project root.

### Option 2: Web Interface
<img width="1734" height="528" alt="Screenshot 2025-07-05 011416" src="https://github.com/user-attachments/assets/21021dfa-b3c5-466a-984c-007707f9614c" />

1. **Run the Backend**:
   Start the FastAPI server:
   ```bash
   python main_api.py
   ```
2. **Run the Frontend**:
   Start a local web server to serve the GUI:
   ```bash
   python -m http.server 8080
   ```
   Open `http://localhost:8080/index.html` in your browser.
3. **Enter Input**:
   - In the "Enter your prompt" field, type:
     ```
     Optimize content using E2SM-KPM and E2SM-RC specifications
     ```
   - Select a vector store (`Chroma` or `LlamaIndex`) and click "Generate Report".
4. **View Output**:
   - The **Output** section displays a concise summary (100-150 words).
   - The "Download Full PDF Report" button appears after the summary, allowing you to download the full report only when clicked.
   - After downloading, a message appears: "Download complete and ready! You can enter a new prompt.", the input field resets, and the output and download button are hidden until the next report is generated.

## Dependencies
Listed in `requirements.txt`:
```
llama_index==0.12.45
llama_index_vector_stores_chroma
llama_index_readers_web
chromadb
fastapi
uvicorn
python-dotenv
pypandoc
openai
validators
nltk
```

## Troubleshooting
- **Ollama Model Not Found**: Ensure the `mistral:instruct` model is installed with `ollama pull mistral`. For memory issues, try `llama3.1:8b` and update `config.py`.
- **PDF Generation Fails**: Verify `pandoc` and `pdflatex` are installed. Check MiKTeX package installation prompts and increase delay in `main_api.py` if needed.
- **Summary Not Displaying in GUI**: Check browser console for JavaScript errors, verify API response, and ensure the backend and web/PDF index are built.
- **PDF Downloads Automatically**: Use the updated `index.html` and check for unintended `fetch` events.
- **"Failed to connect to the server"**: Ensure the backend runs on `http://localhost:8000`, check firewall settings, and adjust fetch delay in `index.html`.
- **Web/PDF Index Issues**: Rebuild the index with `python -m tools.web_reader`.
- **Groq API Issues**: Verify the `GroqCloud_API_TOKEN` in `.env` and check logs.

## Contributing
Submit pull requests or issues on GitHub for bug fixes or enhancements.

## License
This project is licensed under the MIT License.
