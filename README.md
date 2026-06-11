# Engineering Docs // RAG Copilot

Enterprise-grade, cloud-native History-Aware Retrieval-Augmented Generation (RAG) system tailored for hardware engineering, industrial technical documentation, and B2B environments.

## Architecture Stack

### Application Layer
- **Backend:** FastAPI, Python 3.12 (Strict typing enforced via `mypy`)
- **LLM / Inference:** Llama 3.3 70B (via Groq API)
- **Vector Database:** ChromaDB (Persistent local storage)
- **Embeddings:** paraphrase-multilingual-MiniLM-L12-v2 (HuggingFace)
- **Frontend:** HTML/JS/CSS (Vanilla) with System Command Parsing

### Infrastructure & DevOps
- **Containerization:** Docker
- **Orchestration:** Kubernetes (K8s Deployments, Services, PVCs)
- **Infrastructure as Code (IaC):** Terraform (AWS EKS & VPC Provisioning)
- **CI/CD:** GitHub Actions (Automated Flake8 Linting & Static Type Checking)

## Enterprise Features
- **Context-Aware Memory:** History-Aware Retriever for multi-turn conversational technical queries.
- **Multilingual Support:** Processes English, Ukrainian, and other languages accurately.
- **Automated Directory Sync:** Drop PDFs into `docs_storage/` and rebuild the vector index via UI or REST API.
- **Precise Citations:** UI provides clickable source citations with exact PDF page routing.
- **Cloud-Ready:** Decoupled architecture ready for deployment on AWS, GCP, or Azure via K8s.

---

## Deployment Protocols

### Prerequisites
For all deployment methods, a `.env` file is required in the root directory containing your LLM provider key:
```env
GROQ_API_KEY=your_api_key_here
