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
```
GROQ_API_KEY=your_api_key_here
```
Option A: Containerized Deployment (Docker) - Recommended for Testing
The fastest way to spin up the isolated environment without modifying the host OS.

Build the Docker image
```
docker build -t engineering-rag-copilot:latest .
```
Run the container (exposing port 8000 and injecting the .env file)
```
docker run -d \
  --name rag-copilot-instance \
  -p 8000:8000 \
  --env-file .env \
  -v $(pwd)/docs_storage:/app/docs_storage \
  -v $(pwd)/chroma_db:/app/chroma_db \
  engineering-rag-copilot:latest
```
Option B: Enterprise Orchestration (Kubernetes)
For high-availability production environments. Manifests are located in the k8s/ directory.

Ensure your Kubernetes cluster (e.g., Minikube, EKS, GKE) is running.

Create the required secret for the API key
```
kubectl create secret generic rag-copilot-secrets --from-literal=GROQ_API_KEY=your_api_key_here
```
Apply the infrastructure manifests
```
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
```
Option C: Cloud Provisioning (Terraform)
To provision the underlying AWS EKS cluster infrastructure before deploying K8s manifests.
```
cd terraform
terraform init
terraform plan
terraform apply
```
Option D: Bare-Metal Local Development
For active codebase development and debugging.
```
# 1. Run the initialization script to setup venv and dependencies
./install.sh

# 2. Activate environment
source venv/bin/activate

# 3. Start the Uvicorn server
python api.py
```
Security & Quality Assurance
This repository enforces strict code quality via GitHub Actions. Every push to the ```main``` branch triggers:

```flake8``` for PEP-8 compliance and syntax validation.

```mypy``` for strict static type checking across FastAPI routes and LangChain modules.
