from fastapi import FastAPI, HTTPException, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Dict, Optional
from rag_core import ask_engineering_question, process_document, sync_directory, DOCS_DIR
import os
import shutil

app = FastAPI(title="Engineering RAG API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

os.makedirs(DOCS_DIR, exist_ok=True)
app.mount("/docs", StaticFiles(directory=DOCS_DIR), name="docs")

class QueryRequest(BaseModel):
    query: str
    chat_history: Optional[List[Dict[str, str]]] = []

class ProcessRequest(BaseModel):
    file_path: str

# НОВИЙ ЕНДПОІНТ: Віддає веб-інтерфейс
@app.get("/")
async def serve_frontend():
    if not os.path.exists("index.html"):
        raise HTTPException(status_code=404, detail="index.html not found on server.")
    return FileResponse("index.html")

@app.post("/ask")
async def ask_question(request: QueryRequest):
    try:
        result = ask_engineering_question(request.query, request.chat_history)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/upload")
async def upload_and_process_pdf(file: UploadFile = File(...)):
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")
    
    file_path = os.path.join(DOCS_DIR, file.filename)
    
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        chunks_count = process_document(file_path)
        return {"message": f"Successfully uploaded and indexed '{file.filename}' ({chunks_count} chunks)."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/sync")
async def sync_storage_directory():
    try:
        files_count, chunks_count = sync_directory()
        return {"message": f"Storage synchronized. Indexed {files_count} files ({chunks_count} chunks total)."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    # 0.0.0.0 означає, що сервер слухає запити з УСІХ мережевих інтерфейсів (LAN)
    uvicorn.run(app, host="0.0.0.0", port=8000)