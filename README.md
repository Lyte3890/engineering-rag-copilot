
# Engineering Docs // RAG Copilot

Enterprise-grade History-Aware Retrieval-Augmented Generation (RAG) system tailored for hardware engineering, industrial technical documentation, and B2B environments.

## Architecture
- **Backend:** FastAPI, Python
- **LLM / Inference:** Llama 3.3 70B (via Groq API)
- **Vector Database:** ChromaDB
- **Embeddings:** paraphrase-multilingual-MiniLM-L12-v2 (HuggingFace)
- **Frontend:** HTML/JS/CSS (Vanilla) with System Command Parsing

## Features
- **Context-Aware Memory:** History-Aware Retriever for conversational technical queries.
- **Multilingual Support:** Processes English, Ukrainian, and other languages accurately.
- **Automated Directory Sync:** Drop PDFs into `docs_storage/` and rebuild the vector index via UI or API.
- **Precise Citations:** UI provides clickable source citations with exact PDF page routing.

## Deployment Protocol

### Quick Start (Automated Setup)
For Linux/macOS environments, use the included setup script to automatically configure the virtual environment, install dependencies, and initialize the system.

1. **Clone the repository:**
   ```
   git clone [https://github.com/Lyte3890/engineering-rag-copilot.git](https://github.com/Lyte3890/engineering-rag-copilot.git)
   cd engineering-rag-copilot
   ```
2. ### Run the installer
```
./install.sh
```
Start the Server:
```
source venv/bin/activate
python api.py
```
Navigate to ```http://localhost:8000``` (or your server's IP address).
Production Deployment (Linux Systemd)

For enterprise environments, it is recommended to run the backend as a Systemd daemon managed by Gunicorn.

    Install Gunicorn: pip install gunicorn

    Configure a Systemd service file (```/etc/systemd/system/rag-copilot.service```) with 4+ workers and extended timeouts.

  Enable and start the service:
  ```
sudo systemctl enable rag-copilot
sudo systemctl start rag-copilot
```
